from __future__ import annotations

import ast
import dataclasses
import inspect
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from datetime import UTC, datetime
from decimal import Decimal


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"

RECOMMENDATION_MODULE_NAMES = (
    "strategy_candidate_recommendation",
    "paper_strategy_selection_policy",
    "strategy_recommendation_explain",
    "strategy_recommendation_history",
)

SAFETY_DATACLASS_FIELDS = ("paper_only", "report_only", "readonly")

FORBIDDEN_LIVE_EXECUTION_TERMS = (
    "private_key",
    "wallet",
    "allowance",
    "signature",
    "relayer",
    "live_order",
    "order_builder",
    "clob_client",
    "create_order",
    "post_order",
)


def import_recommendation_module(module_name: str) -> ModuleType:
    return pytest.importorskip(f"polymarket_alpha_lab.{module_name}")


def parse_module(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"))


def package_root_exports() -> set[str]:
    assigned_exports = None
    for node in ast.walk(parse_module(PACKAGE_ROOT_PATH)):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                assigned_exports = ast.literal_eval(node.value)

    assert assigned_exports is not None
    return set(assigned_exports)


def package_root_imported_modules() -> set[str]:
    imported_modules: set[str] = set()
    for node in ast.walk(parse_module(PACKAGE_ROOT_PATH)):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported_modules.add(node.module or "")
    return imported_modules


def package_root_bound_names() -> set[str]:
    bound_names: set[str] = set()
    for node in ast.walk(parse_module(PACKAGE_ROOT_PATH)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound_names.add(alias.asname or alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                bound_names.add(alias.asname or alias.name)
    return bound_names


def is_public_module_member(name: str, value: Any, module_name: str) -> bool:
    if name.startswith("_") or inspect.ismodule(value):
        return False
    owner_module = getattr(value, "__module__", None)
    if owner_module is not None:
        return owner_module == module_name
    return True


def public_api_names(module: ModuleType) -> tuple[str, ...]:
    explicit_exports = getattr(module, "__all__", None)
    if explicit_exports is not None:
        return tuple(explicit_exports)

    return tuple(
        sorted(
            name
            for name, value in vars(module).items()
            if is_public_module_member(name, value, module.__name__)
        )
    )


def public_dataclass_types(module: ModuleType) -> tuple[type[Any], ...]:
    dataclass_types: list[type[Any]] = []
    for name in public_api_names(module):
        value = getattr(module, name, None)
        if inspect.isclass(value) and dataclasses.is_dataclass(value):
            dataclass_types.append(value)
    return tuple(dataclass_types)


def assert_safety_field_defaults_to_true(dataclass_type: type[Any]) -> None:
    for field in dataclasses.fields(dataclass_type):
        if field.name in SAFETY_DATACLASS_FIELDS:
            assert field.default is True, (dataclass_type.__name__, field.name)


def module_source(module: ModuleType) -> str:
    module_path = getattr(module, "__file__", None)
    assert module_path is not None, module.__name__
    return Path(module_path).read_text(encoding="utf-8")


def module_tree(module: ModuleType) -> ast.AST:
    module_path = getattr(module, "__file__", None)
    assert module_path is not None, module.__name__
    return parse_module(Path(module_path))


def assert_no_package_root_import_dependency(module: ModuleType) -> None:
    for node in ast.walk(module_tree(module)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "polymarket_alpha_lab", (
                    module.__name__,
                    alias.name,
                )
        elif isinstance(node, ast.ImportFrom):
            assert not (node.level == 0 and node.module == "polymarket_alpha_lab"), (
                module.__name__,
                ast.unparse(node),
            )


@pytest.mark.parametrize("module_name", RECOMMENDATION_MODULE_NAMES)
def test_recommendation_layer_modules_do_not_need_package_root_exports(
    module_name: str,
) -> None:
    module = import_recommendation_module(module_name)

    package_exports = package_root_exports()
    package_bound_names = package_root_bound_names()
    package_imports = package_root_imported_modules()

    assert_no_package_root_import_dependency(module)
    assert f"polymarket_alpha_lab.{module_name}" not in package_imports
    for public_name in public_api_names(module):
        assert public_name not in package_exports, public_name
        assert public_name not in package_bound_names, public_name


@pytest.mark.parametrize("module_name", RECOMMENDATION_MODULE_NAMES)
def test_recommendation_layer_public_dataclass_defaults_are_readonly_paper_reports(
    module_name: str,
) -> None:
    module = import_recommendation_module(module_name)

    for dataclass_type in public_dataclass_types(module):
        assert_safety_field_defaults_to_true(dataclass_type)


@pytest.mark.parametrize("module_name", RECOMMENDATION_MODULE_NAMES)
def test_recommendation_layer_source_omits_live_execution_and_auth_terms(
    module_name: str,
) -> None:
    module = import_recommendation_module(module_name)

    source = module_source(module).lower()
    for forbidden_term in FORBIDDEN_LIVE_EXECUTION_TERMS:
        assert forbidden_term not in source, (module.__name__, forbidden_term)


def test_recommendation_layer_real_report_feeds_selection_and_explanation() -> None:
    candidate_recommendation = import_recommendation_module(
        "strategy_candidate_recommendation",
    )
    selection_policy = import_recommendation_module("paper_strategy_selection_policy")
    explanation = import_recommendation_module("strategy_recommendation_explain")

    from polymarket_alpha_lab.candidate_assessment import (  # noqa: PLC0415
        PaperCandidateAssessmentReport,
        PaperCandidateAssessmentRow,
    )
    from polymarket_alpha_lab.strategy_readiness_state import (  # noqa: PLC0415
        PaperStrategyReadinessSignal,
        build_paper_strategy_readiness_state_report,
    )

    generated_at = datetime(2026, 6, 18, 16, 0, tzinfo=UTC)
    assessment_report = PaperCandidateAssessmentReport(
        generated_at=generated_at,
        config_version="candidate-assessment-v1",
        candidate_count=1,
        assessed_count=1,
        ready_count=1,
        watch_count=0,
        blocked_count=0,
        assessment_rows=(
            PaperCandidateAssessmentRow(
                market_slug="real-link-candidate",
                question="Will this linked paper candidate resolve yes?",
                research_bucket="research_ready",
                assessment_status="ready",
                source_status="paper_review_ready",
                selected_side="yes",
                scoring_side="yes",
                screening_score=Decimal("0.200000"),
                net_edge_per_share=Decimal("0.200000"),
                total_cost_per_share=Decimal("0.010000"),
                confidence=Decimal("0.9000"),
                spread=Decimal("0.0100"),
                resolution_risk=Decimal("0.0200"),
                readiness_score=Decimal("0.300000"),
                reason_codes=("assessment_ready",),
            ),
        ),
    )
    readiness_report = build_paper_strategy_readiness_state_report(
        (
            PaperStrategyReadinessSignal(
                source_name="calibration_gate",
                status="pass",
                reason_codes=("calibration_ready",),
                severity=1,
            ),
        ),
        config_version="readiness-v1",
        generated_at=generated_at,
    )
    recommendation_report = (
        candidate_recommendation.build_paper_strategy_candidate_recommendation_report(
            assessment_report,
            readiness_report,
            config=candidate_recommendation.PaperStrategyCandidateRecommendationConfig(
                config_version="recommendation-v1",
                min_recommendation_score=Decimal("0.010000"),
            ),
            generated_at=generated_at,
        )
    )

    selection_report = selection_policy.build_paper_strategy_selection_policy_report(
        recommendation_report,
        config=selection_policy.PaperStrategySelectionPolicyConfig(
            config_version="selection-v1",
            base_position_notional=Decimal("10.000000"),
            max_position_notional=Decimal("10.000000"),
            max_total_notional=Decimal("10.000000"),
        ),
        generated_at=generated_at,
    )
    explanation_report = (
        explanation.build_paper_strategy_recommendation_explanation_report(
            recommendation_report,
            generated_at=generated_at,
        )
    )

    assert recommendation_report.recommend_count == 1
    assert selection_report.selected_count == 1
    assert selection_report.total_selected_notional == Decimal("3.000000")
    assert explanation_report.source_config_version == "recommendation-v1"
    assert explanation_report.explanation_rows[0].recommendation_score == Decimal(
        "0.300000",
    )
