from __future__ import annotations

import ast
import dataclasses
import inspect
import re
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from datetime import UTC, datetime
from decimal import Decimal


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"

IMPLEMENTED_RECOMMENDATION_MODULE_NAMES = (
    "strategy_candidate_recommendation",
    "strategy_signal_adapter",
    "paper_capital_cost_model",
    "paper_probability_side_edge",
    "paper_recommendation_risk_budget",
    "paper_recommendation_reason_trend",
    "paper_strategy_selection_policy",
    "strategy_recommendation_explain",
    "strategy_recommendation_history",
    "strategy_recommendation_bundle",
    "strategy_recommendation_log",
    "strategy_recommendation_queue",
    "strategy_recommendation_reason_trend",
    "action_gated_strategy_recommendation_queue",
)

DB_ROW_CODEC_MODULE_NAMES = (
    "paper_probability_recommendation_queue_db_row",
    "paper_recommendation_risk_budget_db_row",
)

PLANNED_RECOMMENDATION_MODULE_NAMES = (
    "paper_capital_cost",
    "paper_correlation_grouping",
    "paper_cost_stress",
    "paper_liquidity_depth_gate",
    "paper_outcome_uncertainty",
    "paper_probability_recommendation_queue",
    "paper_recommendation_queue",
    "paper_recommendation_allocation",
    "paper_recommendation_calibration_gate",
    "paper_recommendation_consistency",
    "paper_recommendation_gate_summary",
    "paper_recommendation_health",
    "paper_recommendation_manifest",
    "paper_recommendation_readiness",
    "paper_recommendation_shadow_nav",
    "paper_recommendation_thresholds",
    "paper_research_packet",
    "paper_settlement_timing",
    "paper_side_edge_adapter",
)

RECOMMENDATION_MODULE_NAMES = IMPLEMENTED_RECOMMENDATION_MODULE_NAMES + tuple(
    module_name
    for module_name in DB_ROW_CODEC_MODULE_NAMES
    if (REPO_ROOT / "src" / "polymarket_alpha_lab" / f"{module_name}.py").exists()
)

PLANNED_RECOMMENDATION_PUBLIC_NAMES = {
    "paper_capital_cost": frozenset(
        {
            "PaperCapitalCostConfig",
            "PaperCapitalCostReport",
            "PaperCapitalCostRow",
            "build_paper_capital_cost_report",
        },
    ),
    "paper_correlation_grouping": frozenset(
        {
            "PaperCorrelationGroupingConfig",
            "PaperCorrelationGroupingReport",
            "PaperCorrelationGroupRow",
            "PaperCorrelationInputRow",
            "build_paper_correlation_grouping_report",
        },
    ),
    "paper_cost_stress": frozenset(
        {
            "PaperCostStressConfig",
            "PaperCostStressInput",
            "PaperCostStressReport",
            "PaperCostStressScenarioRow",
            "build_paper_cost_stress_report",
        },
    ),
    "paper_liquidity_depth_gate": frozenset(
        {
            "PaperLiquidityDepthGateConfig",
            "PaperLiquidityDepthGateInput",
            "PaperLiquidityDepthGateReport",
            "PaperLiquidityDepthGateRow",
            "build_paper_liquidity_depth_gate_report",
        },
    ),
    "paper_outcome_uncertainty": frozenset(
        {
            "PaperOutcomeUncertaintyConfig",
            "PaperOutcomeUncertaintyInput",
            "PaperOutcomeUncertaintyReport",
            "PaperOutcomeUncertaintyRow",
            "build_paper_outcome_uncertainty_report",
        },
    ),
    "paper_probability_recommendation_queue": frozenset(
        {
            "PaperProbabilityRecommendationQueueConfig",
            "PaperProbabilityRecommendationQueueReport",
            "PaperProbabilityRecommendationQueueRow",
            "build_paper_probability_recommendation_queue_report",
        },
    ),
    "paper_recommendation_queue": frozenset(
        {
            "PaperRecommendationQueueConfig",
            "PaperRecommendationQueueReport",
            "PaperRecommendationQueueRow",
            "build_paper_recommendation_queue_report",
        },
    ),
    "paper_recommendation_allocation": frozenset(
        {
            "PaperRecommendationAllocationConfig",
            "PaperRecommendationAllocationInput",
            "PaperRecommendationAllocationReport",
            "PaperRecommendationAllocationRow",
            "build_paper_recommendation_allocation_report",
        },
    ),
    "paper_recommendation_calibration_gate": frozenset(
        {
            "PaperRecommendationCalibrationGateConfig",
            "PaperRecommendationCalibrationGateMetric",
            "PaperRecommendationCalibrationGateReport",
            "PaperRecommendationCalibrationGateRow",
            "PaperRecommendationCalibrationGateSourceRow",
            "build_paper_recommendation_calibration_gate_report",
        },
    ),
    "paper_recommendation_consistency": frozenset(
        {
            "PaperRecommendationConsistencyConfig",
            "PaperRecommendationConsistencyFact",
            "PaperRecommendationConsistencyReport",
            "PaperRecommendationConsistencyRow",
            "build_paper_recommendation_consistency_report",
        },
    ),
    "paper_recommendation_gate_summary": frozenset(
        {
            "GateReasonCodeCount",
            "PaperRecommendationGateInputRow",
            "PaperRecommendationGateSummaryReport",
            "PaperRecommendationGateSummaryRow",
            "build_paper_recommendation_gate_summary_report",
        },
    ),
    "paper_recommendation_health": frozenset(
        {
            "PaperRecommendationHealthConfig",
            "PaperRecommendationHealthInputRow",
            "PaperRecommendationHealthReasonCodeCount",
            "PaperRecommendationHealthReport",
            "build_paper_recommendation_health_report",
        },
    ),
    "paper_recommendation_manifest": frozenset(
        {
            "PaperRecommendationManifestConfig",
            "PaperRecommendationManifestItem",
            "PaperRecommendationManifestReport",
            "build_paper_recommendation_manifest_report",
        },
    ),
    "paper_recommendation_readiness": frozenset(
        {
            "PaperRecommendationReadinessConfig",
            "PaperRecommendationReadinessGateInput",
            "PaperRecommendationReadinessReport",
            "PaperRecommendationReadinessRow",
            "build_paper_recommendation_readiness_report",
        },
    ),
    "paper_recommendation_shadow_nav": frozenset(
        {
            "PaperRecommendationShadowNavAllocationRow",
            "PaperRecommendationShadowNavConfig",
            "PaperRecommendationShadowNavReport",
            "build_paper_recommendation_shadow_nav_report",
        },
    ),
    "paper_recommendation_thresholds": frozenset(
        {
            "PaperRecommendationThresholdsConfig",
            "PaperRecommendationThresholdsInputRow",
            "PaperRecommendationThresholdsReport",
            "PaperRecommendationThresholdsRow",
            "build_paper_recommendation_thresholds_report",
        },
    ),
    "paper_research_packet": frozenset(
        {
            "PaperResearchPacketConfig",
            "PaperResearchPacketInputRow",
            "PaperResearchPacketReport",
            "PaperResearchPacketRow",
            "build_paper_research_packet",
            "build_paper_research_packet_report",
        },
    ),
    "paper_settlement_timing": frozenset(
        {
            "PaperSettlementTimingConfig",
            "PaperSettlementTimingInput",
            "PaperSettlementTimingReport",
            "PaperSettlementTimingRow",
            "build_paper_settlement_timing_report",
        },
    ),
    "paper_side_edge_adapter": frozenset(
        {
            "PaperSideEdgeAdapterConfig",
            "PaperSideEdgeAdapterInput",
            "PaperSideEdgeStrategyRow",
            "build_paper_side_edge_report",
            "build_paper_side_edge_report_from_adapter_inputs",
            "build_paper_side_edge_report_from_strategy_rows",
            "paper_side_edge_inputs_from_adapter_inputs",
            "paper_side_edge_inputs_from_strategy_rows",
        },
    ),
}

SAFETY_DATACLASS_FIELDS = ("paper_only", "report_only", "readonly")

WHOLE_MODULE_IMPORT: frozenset[str] | None = None

RECOMMENDATION_IMPORT_ALLOWLIST: dict[
    str,
    dict[str, frozenset[str] | None],
] = {
    "strategy_candidate_recommendation": {
        "__future__": frozenset({"annotations"}),
        "dataclasses": frozenset({"dataclass"}),
        "datetime": frozenset({"UTC", "datetime"}),
        "decimal": frozenset({"Decimal"}),
        "typing": frozenset({"Any"}),
        "polymarket_alpha_lab.candidate_assessment": frozenset(
            {
                "PaperCandidateAssessmentReport",
                "PaperCandidateAssessmentRow",
            },
        ),
        "polymarket_alpha_lab.strategy_readiness_state": frozenset(
            {"PaperStrategyReadinessStateReport"},
        ),
    },
    "strategy_signal_adapter": {
        "__future__": frozenset({"annotations"}),
        "decimal": frozenset({"Decimal"}),
        "polymarket_alpha_lab.calibration_gate": frozenset(
            {"PaperCalibrationGateReport"},
        ),
        "polymarket_alpha_lab.cost_health_gate": frozenset(
            {
                "PaperCostHealthGateReport",
                "PaperCostHealthGateRow",
            },
        ),
        "polymarket_alpha_lab.exposure_gate": frozenset(
            {"PaperExposureGateReport"},
        ),
        "polymarket_alpha_lab.liquidity_gate": frozenset(
            {"PaperLiquidityGateReport"},
        ),
        "polymarket_alpha_lab.market_context_freshness": frozenset(
            {"PaperMarketContextFreshnessReport"},
        ),
        "polymarket_alpha_lab.paper_nav_liquidity_risk": frozenset(
            {"PaperNavLiquidityRiskReport"},
        ),
        "polymarket_alpha_lab.paper_nav_settlement_risk_overlay": frozenset(
            {"PaperNavSettlementRiskOverlayReport"},
        ),
        "polymarket_alpha_lab.settlement_freshness_gate": frozenset(
            {"PaperSettlementFreshnessGateReport"},
        ),
        "polymarket_alpha_lab.strategy_readiness_state": frozenset(
            {"PaperStrategyReadinessSignal"},
        ),
    },
    "paper_capital_cost_model": {
        "__future__": frozenset({"annotations"}),
        "dataclasses": frozenset({"dataclass"}),
        "datetime": frozenset({"UTC", "datetime"}),
        "decimal": frozenset({"Decimal"}),
    },
    "paper_probability_side_edge": {
        "__future__": frozenset({"annotations"}),
        "collections.abc": frozenset({"Iterable"}),
        "dataclasses": frozenset({"dataclass"}),
        "datetime": frozenset({"UTC", "datetime"}),
        "decimal": frozenset({"Context", "Decimal", "localcontext"}),
    },
    "paper_recommendation_risk_budget": {
        "__future__": frozenset({"annotations"}),
        "dataclasses": frozenset({"dataclass"}),
        "datetime": frozenset({"UTC", "datetime"}),
        "decimal": frozenset({"Decimal"}),
    },
    "paper_probability_recommendation_queue_db_row": {
        "__future__": frozenset({"annotations"}),
        "dataclasses": frozenset({"asdict", "dataclass", "fields", "is_dataclass"}),
        "datetime": frozenset({"UTC", "datetime"}),
        "decimal": frozenset({"Decimal"}),
        "hashlib": WHOLE_MODULE_IMPORT,
        "json": WHOLE_MODULE_IMPORT,
        "re": WHOLE_MODULE_IMPORT,
        "typing": frozenset({"Any"}),
        "polymarket_alpha_lab.json_recovery": frozenset({"from_jsonable"}),
        "polymarket_alpha_lab.paper_probability_recommendation_queue": frozenset(
            {"PaperProbabilityRecommendationQueueReport"},
        ),
    },
    "paper_recommendation_risk_budget_db_row": {
        "__future__": frozenset({"annotations"}),
        "dataclasses": frozenset({"asdict", "dataclass", "fields", "is_dataclass"}),
        "datetime": frozenset({"UTC", "datetime"}),
        "decimal": frozenset({"Decimal"}),
        "hashlib": WHOLE_MODULE_IMPORT,
        "json": WHOLE_MODULE_IMPORT,
        "re": WHOLE_MODULE_IMPORT,
        "typing": frozenset({"Any"}),
        "polymarket_alpha_lab.json_recovery": frozenset({"from_jsonable"}),
        "polymarket_alpha_lab.paper_recommendation_risk_budget": frozenset(
            {"PaperRecommendationRiskBudgetReport"},
        ),
    },
    "paper_recommendation_reason_trend": {
        "__future__": frozenset({"annotations"}),
        "dataclasses": frozenset({"dataclass"}),
        "datetime": frozenset({"UTC", "datetime"}),
        "decimal": frozenset({"Decimal"}),
    },
    "paper_strategy_selection_policy": {
        "__future__": frozenset({"annotations"}),
        "dataclasses": frozenset({"dataclass"}),
        "datetime": frozenset({"UTC", "datetime"}),
        "decimal": frozenset({"Decimal"}),
        "importlib": frozenset({"import_module"}),
        "typing": frozenset({"Any"}),
    },
    "strategy_recommendation_explain": {
        "__future__": frozenset({"annotations"}),
        "dataclasses": frozenset({"dataclass"}),
        "datetime": frozenset({"UTC", "datetime"}),
        "decimal": frozenset({"Decimal"}),
        "typing": frozenset({"Iterable"}),
        "polymarket_alpha_lab.strategy_candidate_recommendation": frozenset(
            {"PaperStrategyCandidateRecommendationReport"},
        ),
    },
    "strategy_recommendation_history": {
        "__future__": frozenset({"annotations"}),
        "dataclasses": frozenset({"dataclass"}),
        "datetime": frozenset({"UTC", "datetime"}),
        "decimal": frozenset({"Decimal"}),
        "typing": frozenset({"Any", "Iterable"}),
        "polymarket_alpha_lab.strategy_candidate_recommendation": frozenset(
            {"PaperStrategyCandidateRecommendationReport"},
        ),
    },
    "strategy_recommendation_bundle": {
        "__future__": frozenset({"annotations"}),
        "dataclasses": frozenset({"dataclass"}),
        "datetime": frozenset({"UTC", "datetime"}),
        "decimal": frozenset({"Decimal"}),
        "typing": frozenset({"Any"}),
        "polymarket_alpha_lab.paper_strategy_selection_policy": frozenset(
            {
                "PaperStrategySelectionPolicyConfig",
                "PaperStrategySelectionPolicyReport",
                "build_paper_strategy_selection_policy_report",
            },
        ),
        "polymarket_alpha_lab.strategy_candidate_recommendation": frozenset(
            {
                "PaperStrategyCandidateRecommendationConfig",
                "PaperStrategyCandidateRecommendationReport",
                "build_paper_strategy_candidate_recommendation_report",
            },
        ),
        "polymarket_alpha_lab.strategy_recommendation_explain": frozenset(
            {
                "PaperStrategyRecommendationExplanationReport",
                "build_paper_strategy_recommendation_explanation_report",
            },
        ),
    },
    "strategy_recommendation_queue": {
        "__future__": frozenset({"annotations"}),
        "dataclasses": frozenset({"dataclass"}),
        "datetime": frozenset({"UTC", "datetime"}),
        "decimal": frozenset({"Decimal"}),
        "typing": frozenset({"Any", "Iterable"}),
        "polymarket_alpha_lab.strategy_recommendation_bundle": frozenset(
            {"PaperStrategyRecommendationBundleReport"},
        ),
    },
    "strategy_recommendation_reason_trend": {
        "__future__": frozenset({"annotations"}),
        "dataclasses": frozenset({"dataclass"}),
        "datetime": frozenset({"UTC", "datetime"}),
        "decimal": frozenset({"Decimal", "ROUND_HALF_EVEN"}),
        "typing": frozenset({"Any"}),
        "polymarket_alpha_lab.strategy_recommendation_bundle": frozenset(
            {"PaperStrategyRecommendationBundleReport"},
        ),
        "polymarket_alpha_lab.strategy_recommendation_explain": frozenset(
            {
                "NO_REASON_CODE",
                "PaperStrategyRecommendationExplanationReport",
            },
        ),
        "polymarket_alpha_lab.strategy_recommendation_history": frozenset(
            {"PaperStrategyRecommendationHistoryReport"},
        ),
    },
    "strategy_recommendation_log": {
        "__future__": frozenset({"annotations"}),
        "json": WHOLE_MODULE_IMPORT,
        "dataclasses": frozenset({"asdict", "is_dataclass"}),
        "datetime": frozenset({"UTC", "datetime"}),
        "decimal": frozenset({"Decimal", "InvalidOperation"}),
        "pathlib": frozenset({"Path"}),
        "typing": frozenset({"Any"}),
        "polymarket_alpha_lab.json_recovery": frozenset({"from_jsonable"}),
        "polymarket_alpha_lab.paper_strategy_selection_policy": frozenset(
            {"PaperStrategySelectionPolicyReport"},
        ),
        "polymarket_alpha_lab.strategy_candidate_recommendation": frozenset(
            {"PaperStrategyCandidateRecommendationReport"},
        ),
        "polymarket_alpha_lab.strategy_recommendation_bundle": frozenset(
            {"PaperStrategyRecommendationBundleReport"},
        ),
        "polymarket_alpha_lab.strategy_recommendation_explain": frozenset(
            {"PaperStrategyRecommendationExplanationReport"},
        ),
    },
    "action_gated_strategy_recommendation_queue": {
        "__future__": frozenset({"annotations"}),
        "collections.abc": frozenset({"Iterable"}),
        "dataclasses": frozenset({"dataclass"}),
        "datetime": frozenset({"UTC", "datetime"}),
        "decimal": frozenset({"Decimal"}),
        "typing": frozenset({"Any"}),
        "polymarket_alpha_lab.candidate_assessment": frozenset(
            {
                "PaperCandidateAssessmentConfig",
                "PaperCandidateAssessmentReport",
                "build_paper_candidate_assessment_report",
            },
        ),
        "polymarket_alpha_lab.paper_recommendation_cycle_action_gate": frozenset(
            {
                "PaperRecommendationCycleActionGateReasonCodeCount",
                "PaperRecommendationCycleActionGateReport",
            },
        ),
        "polymarket_alpha_lab.project_screening": frozenset(
            {"PaperProjectScreeningReport"},
        ),
        "polymarket_alpha_lab.strategy_readiness_state": frozenset(
            {
                "PaperStrategyReadinessSignal",
                "PaperStrategyReadinessStateReport",
                "build_paper_strategy_readiness_state_report",
            },
        ),
        "polymarket_alpha_lab.strategy_recommendation_bundle": frozenset(
            {
                "PaperStrategyRecommendationBundleConfig",
                "PaperStrategyRecommendationBundleReport",
                "build_paper_strategy_recommendation_bundle_report",
            },
        ),
        "polymarket_alpha_lab.strategy_recommendation_queue": frozenset(
            {
                "PaperStrategyRecommendationQueueSummaryReport",
                "build_paper_strategy_recommendation_queue_summary_report",
            },
        ),
    },
}

FORBIDDEN_IMPORT_PREFIXES = (
    "aiohttp",
    "clob_client",
    "eth_account",
    "eth_keys",
    "http",
    "httpx",
    "py_clob_client",
    "requests",
    "socket",
    "ssl",
    "subprocess",
    "urllib",
    "urllib3",
    "web3",
    "websocket",
    "websockets",
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.auth",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.execution",
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.orders",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.paper_execution",
    "polymarket_alpha_lab.positions",
    "polymarket_alpha_lab.trading",
)

FORBIDDEN_LIVE_EXECUTION_TERMS = (
    "api_key",
    "secret",
    "credential",
    "private_key",
    "wallet",
    "allowance",
    "signature",
    "relayer",
    "clob_client",
    "live_order",
    "order_builder",
    "create_order",
    "post_order",
    "cancel_order",
    "submit_order",
    "send_order",
    "sign_order",
)

FORBIDDEN_NAME_FRAGMENTS = (
    "apikey",
    "api",
    "auth",
    "client",
    "credential",
    "secret",
    "privatekey",
    "wallet",
    "allowance",
    "signature",
    "relayer",
    "clobclient",
    "liveorder",
    "orderbuilder",
    "createorder",
    "postorder",
    "cancelorder",
    "submitorder",
    "sendorder",
    "signorder",
)

FORBIDDEN_CALL_NAMES = (
    "__import__",
    "compile",
    "eval",
    "exec",
)

ALLOWED_DYNAMIC_IMPORT_TARGETS = {
    "polymarket_alpha_lab.strategy_candidate_recommendation",
}

FIRST_PARTY_IMPORT_ROOT = "polymarket_alpha_lab"
IDENTIFIER_TOKEN_RE = re.compile(
    r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|\d+",
)
FORBIDDEN_NAME_TOKEN_ALIASES = {
    "apikey": (("api", "key"),),
    "privatekey": (("private", "key"),),
    "clobclient": (("clob", "client"),),
    "liveorder": (("live", "order"),),
    "orderbuilder": (("order", "builder"),),
    "createorder": (("create", "order"),),
    "postorder": (("post", "order"),),
    "cancelorder": (("cancel", "order"),),
    "submitorder": (("submit", "order"),),
    "sendorder": (("send", "order"),),
    "signorder": (("sign", "order"),),
}


def test_recommendation_layer_documented_modules_exist() -> None:
    for module_name in RECOMMENDATION_MODULE_NAMES:
        assert module_path(module_name).exists(), module_name


def test_recommendation_layer_scope_includes_current_recommendation_modules() -> None:
    assert set(IMPLEMENTED_RECOMMENDATION_MODULE_NAMES) == {
        "strategy_candidate_recommendation",
        "strategy_signal_adapter",
        "paper_capital_cost_model",
        "paper_probability_side_edge",
        "paper_recommendation_risk_budget",
        "paper_recommendation_reason_trend",
        "paper_strategy_selection_policy",
        "strategy_recommendation_explain",
        "strategy_recommendation_history",
        "strategy_recommendation_bundle",
        "strategy_recommendation_log",
        "strategy_recommendation_queue",
        "strategy_recommendation_reason_trend",
        "action_gated_strategy_recommendation_queue",
    }


def test_recommendation_layer_scope_lists_planned_recommendation_modules() -> None:
    assert set(PLANNED_RECOMMENDATION_MODULE_NAMES) == {
        "paper_capital_cost",
        "paper_correlation_grouping",
        "paper_cost_stress",
        "paper_liquidity_depth_gate",
        "paper_outcome_uncertainty",
        "paper_probability_recommendation_queue",
        "paper_recommendation_queue",
        "paper_recommendation_allocation",
        "paper_recommendation_calibration_gate",
        "paper_recommendation_consistency",
        "paper_recommendation_gate_summary",
        "paper_recommendation_health",
        "paper_recommendation_manifest",
        "paper_recommendation_readiness",
        "paper_recommendation_shadow_nav",
        "paper_recommendation_thresholds",
        "paper_research_packet",
        "paper_settlement_timing",
        "paper_side_edge_adapter",
    }


def test_recommendation_layer_lists_db_row_codec_modules() -> None:
    assert set(DB_ROW_CODEC_MODULE_NAMES) == {
        "paper_probability_recommendation_queue_db_row",
        "paper_recommendation_risk_budget_db_row",
    }


def test_planned_recommendation_public_names_are_not_package_root_exports() -> None:
    package_exports = package_root_exports()
    package_bound_names = package_root_bound_names()
    for public_names in PLANNED_RECOMMENDATION_PUBLIC_NAMES.values():
        for public_name in public_names:
            assert public_name not in package_exports, public_name
            assert public_name not in package_bound_names, public_name


def import_recommendation_module(module_name: str) -> ModuleType:
    return pytest.importorskip(f"polymarket_alpha_lab.{module_name}")


def parse_module(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"))


def module_path(module_name: str) -> Path:
    return REPO_ROOT / "src" / "polymarket_alpha_lab" / f"{module_name}.py"


def _normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _identifier_tokens(identifier: str) -> tuple[str, ...]:
    tokens: list[str] = []
    for chunk in re.split(r"[^0-9A-Za-z]+", identifier):
        if not chunk:
            continue
        tokens.extend(match.group(0).lower() for match in IDENTIFIER_TOKEN_RE.finditer(chunk))
    return tuple(tokens)


def _module_matches_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def _absolute_import_from_module(module_name: str, node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""
    assert node.level == 1, (module_name, ast.unparse(node))
    if node.module is None:
        return "polymarket_alpha_lab"
    return f"polymarket_alpha_lab.{node.module}"


def assert_recommendation_tree_omits_forbidden_import_prefixes(
    module_name: str,
    tree: ast.AST,
) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(
                    _module_matches_prefix(alias.name, prefix)
                    for prefix in FORBIDDEN_IMPORT_PREFIXES
                ), (module_name, alias.name)
                _assert_import_alias_omits_forbidden_fragments(
                    alias.asname or alias.name,
                )
        elif isinstance(node, ast.ImportFrom):
            imported_module = _absolute_import_from_module(module_name, node)
            assert not any(
                _module_matches_prefix(imported_module, prefix)
                for prefix in FORBIDDEN_IMPORT_PREFIXES
            ), (module_name, imported_module)
            _assert_imported_names_are_allowed(
                module_name=module_name,
                imported_module=imported_module,
                imported_names=tuple(node.names),
                allowed_names=None,
                enforce_symbol_allowlist=False,
            )


def _assert_identifier_omits_forbidden_fragments(
    identifier: str,
    fragments: tuple[str, ...],
) -> None:
    normalized_identifier = _normalize_identifier(identifier)
    identifier_tokens = _identifier_tokens(identifier)
    identifier_token_set = set(identifier_tokens)
    for fragment in fragments:
        normalized_fragment = _normalize_identifier(fragment)
        alias_token_groups = FORBIDDEN_NAME_TOKEN_ALIASES.get(
            normalized_fragment,
            ((normalized_fragment,),),
        )
        assert all(
            not _identifier_tokens_contain(identifier_tokens, alias_tokens)
            for alias_tokens in alias_token_groups
        ), (identifier, fragment)
        assert normalized_fragment not in identifier_token_set, (
            identifier,
            fragment,
        )


def _identifier_tokens_contain(
    identifier_tokens: tuple[str, ...],
    forbidden_tokens: tuple[str, ...],
) -> bool:
    if len(forbidden_tokens) > len(identifier_tokens):
        return False
    return any(
        identifier_tokens[index : index + len(forbidden_tokens)] == forbidden_tokens
        for index in range(len(identifier_tokens) - len(forbidden_tokens) + 1)
    )


def _assert_import_alias_omits_forbidden_fragments(alias_name: str) -> None:
    _assert_identifier_omits_forbidden_fragments(
        alias_name.split(".", 1)[0],
        FORBIDDEN_NAME_FRAGMENTS,
    )


def _allowlisted_import_kind(
    module_name: str,
    imported_module: str,
    allowed_imports: dict[str, frozenset[str] | None],
) -> str:
    assert not any(
        _module_matches_prefix(imported_module, prefix)
        for prefix in FORBIDDEN_IMPORT_PREFIXES
    ), (module_name, imported_module)
    assert imported_module in allowed_imports, (module_name, imported_module)
    return "allowlisted"


def _assert_imported_names_are_allowed(
    *,
    module_name: str,
    imported_module: str,
    imported_names: tuple[ast.alias, ...],
    allowed_names: frozenset[str] | None,
    enforce_symbol_allowlist: bool,
) -> set[str]:
    if enforce_symbol_allowlist:
        assert allowed_names is not WHOLE_MODULE_IMPORT, (
            module_name,
            imported_module,
        )
    seen_names: set[str] = set()
    for alias in imported_names:
        if enforce_symbol_allowlist:
            assert allowed_names is not None
            assert alias.name in allowed_names, (
                module_name,
                imported_module,
                alias.name,
            )
        _assert_import_alias_omits_forbidden_fragments(alias.asname or alias.name)
        seen_names.add(alias.name)
    return seen_names


def assert_recommendation_module_imports_are_allowed(
    module_name: str,
    tree: ast.AST,
) -> None:
    allowed_imports = RECOMMENDATION_IMPORT_ALLOWLIST[module_name]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_kind = _allowlisted_import_kind(
                    module_name,
                    alias.name,
                    allowed_imports,
                )
                if import_kind == "allowlisted":
                    assert allowed_imports[alias.name] is WHOLE_MODULE_IMPORT, (
                        module_name,
                        alias.name,
                    )
                _assert_import_alias_omits_forbidden_fragments(
                    alias.asname or alias.name,
                )
        elif isinstance(node, ast.ImportFrom):
            imported_module = _absolute_import_from_module(module_name, node)
            import_kind = _allowlisted_import_kind(
                module_name,
                imported_module,
                allowed_imports,
            )
            allowed_names = (
                allowed_imports[imported_module]
                if import_kind == "allowlisted"
                else None
            )
            _assert_imported_names_are_allowed(
                module_name=module_name,
                imported_module=imported_module,
                imported_names=tuple(node.names),
                allowed_names=allowed_names,
                enforce_symbol_allowlist=import_kind == "allowlisted",
            )


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _is_allowed_regex_compile_call(node: ast.Call) -> bool:
    return (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "compile"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "re"
    )


def assert_recommendation_tree_omits_forbidden_names_and_calls(
    tree: ast.AST,
) -> None:
    dynamic_import_targets = {
        node.targets[0].id: node.value.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id.endswith("_MODULE_NAME")
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    }
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            _assert_identifier_omits_forbidden_fragments(
                node.name,
                FORBIDDEN_NAME_FRAGMENTS,
            )
        elif isinstance(node, ast.arg):
            _assert_identifier_omits_forbidden_fragments(
                node.arg,
                FORBIDDEN_NAME_FRAGMENTS,
            )
        elif isinstance(node, ast.keyword) and node.arg is not None:
            _assert_identifier_omits_forbidden_fragments(
                node.arg,
                FORBIDDEN_NAME_FRAGMENTS,
            )
        elif isinstance(node, ast.Name):
            _assert_identifier_omits_forbidden_fragments(
                node.id,
                FORBIDDEN_NAME_FRAGMENTS,
            )
        elif isinstance(node, ast.Attribute):
            _assert_identifier_omits_forbidden_fragments(
                node.attr,
                FORBIDDEN_NAME_FRAGMENTS,
            )
        elif isinstance(node, ast.Call):
            callee_name = _call_name(node)
            if callee_name is not None:
                if not _is_allowed_regex_compile_call(node):
                    assert callee_name not in FORBIDDEN_CALL_NAMES, callee_name
                _assert_identifier_omits_forbidden_fragments(
                    callee_name,
                    FORBIDDEN_NAME_FRAGMENTS,
                )
                if callee_name == "import_module":
                    assert node.args, "import_module requires an explicit target"
                    first_arg = node.args[0]
                    if isinstance(first_arg, ast.Constant) and isinstance(
                        first_arg.value,
                        str,
                    ):
                        import_target = first_arg.value
                    elif isinstance(first_arg, ast.Name):
                        import_target = dynamic_import_targets.get(first_arg.id)
                    else:
                        import_target = None
                    assert import_target in ALLOWED_DYNAMIC_IMPORT_TARGETS, (
                        "import_module target must be allowlisted",
                        import_target,
                    )


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


def assert_source_declares_safety_fields(module_name: str, source: str) -> None:
    for field_name in SAFETY_DATACLASS_FIELDS:
        assert field_name in source, (module_name, field_name)


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


@pytest.mark.parametrize("module_name", PLANNED_RECOMMENDATION_MODULE_NAMES)
def test_planned_recommendation_module_source_boundary_when_present(
    module_name: str,
) -> None:
    path = module_path(module_name)
    if not path.exists():
        return

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    assert_source_declares_safety_fields(module_name, source)
    for forbidden_term in FORBIDDEN_LIVE_EXECUTION_TERMS:
        assert forbidden_term not in source.lower(), (module_name, forbidden_term)
    assert_recommendation_tree_omits_forbidden_import_prefixes(module_name, tree)
    assert_recommendation_tree_omits_forbidden_names_and_calls(tree)


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


@pytest.mark.parametrize("module_name", RECOMMENDATION_MODULE_NAMES)
def test_recommendation_layer_imports_only_allowlisted_dependencies(
    module_name: str,
) -> None:
    tree = parse_module(module_path(module_name))

    assert_recommendation_module_imports_are_allowed(module_name, tree)


@pytest.mark.parametrize("module_name", RECOMMENDATION_MODULE_NAMES)
def test_recommendation_layer_ast_omits_live_execution_names_and_calls(
    module_name: str,
) -> None:
    tree = parse_module(module_path(module_name))

    assert_recommendation_tree_omits_forbidden_names_and_calls(tree)


@pytest.mark.parametrize(
    ("bad_source", "module_name"),
    (
        pytest.param(
            "from polymarket_alpha_lab.auth import ApiKey\n",
            "strategy_recommendation_bundle",
            id="first-party-auth-import",
        ),
        pytest.param(
            "import requests\n",
            "strategy_recommendation_log",
            id="network-import",
        ),
        pytest.param(
            "from http.client import HTTPConnection\n",
            "strategy_recommendation_log",
            id="stdlib-network-import",
        ),
        pytest.param(
            "import smtplib\n",
            "strategy_recommendation_log",
            id="stdlib-smtp-import",
        ),
        pytest.param(
            "import ftplib\n",
            "strategy_recommendation_log",
            id="stdlib-ftp-import",
        ),
        pytest.param(
            "from ctypes import CDLL\n",
            "strategy_recommendation_log",
            id="stdlib-ctypes-import",
        ),
        pytest.param(
            "from pickle import loads\n",
            "strategy_recommendation_log",
            id="stdlib-pickle-import",
        ),
        pytest.param(
            "from polymarket_alpha_lab.paper_execution import "
            "execute_paper_trade_from_screening\n",
            "strategy_recommendation_bundle",
            id="first-party-paper-execution-import",
        ),
        pytest.param(
            "from pathlib import Path, PurePath\n",
            "strategy_recommendation_log",
            id="non-allowlisted-imported-symbol",
        ),
    ),
)
def test_recommendation_layer_import_scope_guard_rejects_forbidden_imports(
    bad_source: str,
    module_name: str,
) -> None:
    with pytest.raises(AssertionError):
        assert_recommendation_module_imports_are_allowed(
            module_name,
            ast.parse(bad_source),
        )


def test_recommendation_layer_import_scope_guard_allows_allowlisted_stdlib_imports() -> None:
    assert_recommendation_module_imports_are_allowed(
        "strategy_recommendation_log",
        ast.parse(
            """
from pathlib import Path
from decimal import Decimal
""",
        ),
    )


@pytest.mark.parametrize(
    "bad_source",
    (
        pytest.param(
            """
def build_wallet_order(report):
    return report
""",
            id="forbidden-function-name",
        ),
        pytest.param(
            """
def build_report(path):
    return __import__("polymarket_alpha_lab.auth")
""",
            id="dynamic-import-call",
        ),
        pytest.param(
            """
from importlib import import_module
RECOMMENDATION_MODULE_NAME = "polymarket_alpha_lab.auth"

def build_report():
    return import_module(RECOMMENDATION_MODULE_NAME)
""",
            id="forbidden-import-module-target",
        ),
        pytest.param(
            """
def build_report(client):
    return client.post_order()
""",
            id="forbidden-attribute-call",
        ),
        pytest.param(
            """
def build_report(regex):
    return regex.compile("pattern")
""",
            id="non-re-compile-call",
        ),
    ),
)
def test_recommendation_layer_name_scope_guard_rejects_forbidden_names(
    bad_source: str,
) -> None:
    with pytest.raises(AssertionError):
        assert_recommendation_tree_omits_forbidden_names_and_calls(
            ast.parse(bad_source),
        )


def test_recommendation_layer_name_scope_guard_allows_non_forbidden_substrings() -> None:
    assert_recommendation_tree_omits_forbidden_names_and_calls(
        ast.parse(
            """
def summarize_capital(report):
    capital_score = 1
    return capital_score
""",
        ),
    )


def test_recommendation_layer_name_scope_guard_allows_regex_compile_call() -> None:
    assert_recommendation_tree_omits_forbidden_names_and_calls(
        ast.parse(
            r"""
import re

_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
""",
        ),
    )


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
