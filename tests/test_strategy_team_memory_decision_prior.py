from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_team_memory_decision_prior import (
    DEFAULT_STRATEGY_TEAM_MEMORY_DECISION_PRIOR_CONFIG_VERSION,
    StrategyTeamMemoryDecisionPrior,
    StrategyTeamMemoryDecisionPriorConfig,
    StrategyTeamMemoryDecisionPriorInput,
    build_strategy_team_memory_decision_prior,
)


MODULE_PATH = Path("src/polymarket_alpha_lab/strategy_team_memory_decision_prior.py")


def test_builds_readonly_decimal_pass_prior_for_decision_matrix() -> None:
    prior = build_strategy_team_memory_decision_prior(
        memory=StrategyTeamMemoryDecisionPriorInput(
            team_id="crypto_btc",
            team_memory_score=Decimal("0.900000"),
            calibration_score=Decimal("0.850000"),
            sample_size=Decimal("40"),
            recent_error_score=Decimal("0.100000"),
            domain_experience_score=Decimal("0.800000"),
        ),
        config=StrategyTeamMemoryDecisionPriorConfig(),
    )

    assert prior == StrategyTeamMemoryDecisionPrior(
        config_version=DEFAULT_STRATEGY_TEAM_MEMORY_DECISION_PRIOR_CONFIG_VERSION,
        team_id="crypto_btc",
        team_memory_score=Decimal("0.900000"),
        calibration_score=Decimal("0.850000"),
        sample_size=Decimal("40"),
        recent_error_score=Decimal("0.100000"),
        domain_experience_score=Decimal("0.800000"),
        sample_size_score=Decimal("1.000000"),
        recent_error_component_score=Decimal("0.900000"),
        prior_score=Decimal("0.890000"),
        prior_status="pass",
        reason_codes=("strategy_team_memory_prior_ready",),
    )
    assert prior.paper_only is True
    assert prior.report_only is True
    assert prior.readonly is True
    assert all(isinstance(value, Decimal) for value in _decimal_prior_values(prior))


def test_watch_prior_exposes_reason_codes_for_weak_components() -> None:
    prior = build_strategy_team_memory_decision_prior(
        memory=StrategyTeamMemoryDecisionPriorInput(
            team_id="politics",
            team_memory_score=Decimal("0.720000"),
            calibration_score=Decimal("0.800000"),
            sample_size=Decimal("20"),
            recent_error_score=Decimal("0.250000"),
            domain_experience_score=Decimal("0.600000"),
        ),
        config=StrategyTeamMemoryDecisionPriorConfig(),
    )

    assert prior.prior_status == "watch"
    assert prior.sample_size_score == Decimal("0.666667")
    assert prior.recent_error_component_score == Decimal("0.750000")
    assert prior.prior_score == Decimal("0.707333")
    assert prior.reason_codes == (
        "strategy_team_memory_prior_sample_size_low",
        "strategy_team_memory_prior_domain_experience_score_low",
        "strategy_team_memory_prior_aggregate_score_low",
    )


def test_blocked_prior_for_low_sample_size_and_high_recent_error() -> None:
    prior = build_strategy_team_memory_decision_prior(
        memory=StrategyTeamMemoryDecisionPriorInput(
            team_id="macro_rates",
            team_memory_score=Decimal("0.900000"),
            calibration_score=Decimal("0.900000"),
            sample_size=Decimal("5"),
            recent_error_score=Decimal("0.700000"),
            domain_experience_score=Decimal("0.800000"),
        ),
        config=StrategyTeamMemoryDecisionPriorConfig(),
    )

    assert prior.prior_status == "blocked"
    assert prior.sample_size_score == Decimal("0.166667")
    assert prior.recent_error_component_score == Decimal("0.300000")
    assert prior.reason_codes == (
        "strategy_team_memory_prior_sample_size_low",
        "strategy_team_memory_prior_recent_error_score_high",
        "strategy_team_memory_prior_aggregate_score_low",
    )


def test_config_rejects_non_decimal_thresholds_incoherent_thresholds_and_flags() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        StrategyTeamMemoryDecisionPriorConfig(pass_threshold=0.8)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="watch_threshold"):
        StrategyTeamMemoryDecisionPriorConfig(
            pass_threshold=Decimal("0.700000"),
            watch_threshold=Decimal("0.800000"),
        )

    with pytest.raises(ValueError, match="minimum_sample_size"):
        StrategyTeamMemoryDecisionPriorConfig(
            minimum_sample_size=Decimal("30"),
            target_sample_size=Decimal("10"),
        )

    with pytest.raises(ValueError, match="paper_only"):
        StrategyTeamMemoryDecisionPriorConfig(paper_only=False)


def test_dataclasses_are_frozen_tuple_only_and_validate_decimal_consistency() -> None:
    memory = StrategyTeamMemoryDecisionPriorInput(
        team_id="sports_soccer",
        team_memory_score=Decimal("1.000000"),
        calibration_score=Decimal("1.000000"),
        sample_size=Decimal("30"),
        recent_error_score=Decimal("0.000000"),
        domain_experience_score=Decimal("1.000000"),
    )
    prior = build_strategy_team_memory_decision_prior(
        memory=memory,
        config=StrategyTeamMemoryDecisionPriorConfig(),
    )

    with pytest.raises(FrozenInstanceError):
        prior.prior_score = Decimal("0.500000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="Decimal"):
        replace(memory, team_memory_score=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="integral"):
        replace(memory, sample_size=Decimal("1.100000"))

    with pytest.raises(ValueError, match="tuple"):
        replace(prior, reason_codes=["strategy_team_memory_prior_ready"])  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="prior_score"):
        replace(prior, prior_score=Decimal("0.900000"))


def test_rejects_non_prior_inputs_and_unsafe_input_flags() -> None:
    with pytest.raises(ValueError, match="memory"):
        build_strategy_team_memory_decision_prior(
            memory=object(),  # type: ignore[arg-type]
            config=StrategyTeamMemoryDecisionPriorConfig(),
        )

    with pytest.raises(ValueError, match="config"):
        build_strategy_team_memory_decision_prior(
            memory=StrategyTeamMemoryDecisionPriorInput(
                team_id="crypto_btc",
                team_memory_score=Decimal("1.000000"),
                calibration_score=Decimal("1.000000"),
                sample_size=Decimal("30"),
                recent_error_score=Decimal("0.000000"),
                domain_experience_score=Decimal("1.000000"),
            ),
            config=object(),  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="readonly"):
        build_strategy_team_memory_decision_prior(
            memory=replace(
                StrategyTeamMemoryDecisionPriorInput(
                    team_id="crypto_btc",
                    team_memory_score=Decimal("1.000000"),
                    calibration_score=Decimal("1.000000"),
                    sample_size=Decimal("30"),
                    recent_error_score=Decimal("0.000000"),
                    domain_experience_score=Decimal("1.000000"),
                ),
                readonly=False,
            ),
            config=StrategyTeamMemoryDecisionPriorConfig(),
        )


def test_public_surface_is_pure_readonly_decimal_tuple_only() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_call_names = {"__import__", "eval", "exec", "open", "print"}
    forbidden_source_fragments = (
        "account",
        "advice",
        "auth",
        "buy",
        "cancel",
        "credential",
        "dotenv",
        "environ",
        "invest",
        "live",
        "order",
        "private_key",
        "recommend",
        "request",
        "sell",
        "socket",
        "store",
        "submit",
        "supabase",
        "trade",
        "urllib",
        "wallet",
    )

    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module] if node.module is not None else []
        else:
            names = []
        for name in names:
            root = name.split(".", maxsplit=1)[0]
            if root in forbidden_import_roots:
                violations.append(f"forbidden import {name}")

        if isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name in forbidden_call_names:
                violations.append(f"forbidden call {call_name}")

    lowered_source = source.lower()
    for fragment in forbidden_source_fragments:
        if fragment in lowered_source:
            violations.append(f"forbidden source fragment {fragment}")

    assert sorted(set(violations)) == []

    import polymarket_alpha_lab.strategy_team_memory_decision_prior as api

    assert api.__all__ == (
        "DEFAULT_STRATEGY_TEAM_MEMORY_DECISION_PRIOR_CONFIG_VERSION",
        "STRATEGY_TEAM_MEMORY_DECISION_PRIOR_REASON_CODES",
        "STRATEGY_TEAM_MEMORY_DECISION_PRIOR_STATUSES",
        "StrategyTeamMemoryDecisionPrior",
        "StrategyTeamMemoryDecisionPriorConfig",
        "StrategyTeamMemoryDecisionPriorInput",
        "build_strategy_team_memory_decision_prior",
    )
    assert all(
        field.type in (str, Decimal, tuple[str, ...], bool)
        for field in fields(api.StrategyTeamMemoryDecisionPrior)
    )


def _decimal_prior_values(prior: StrategyTeamMemoryDecisionPrior) -> tuple[Decimal, ...]:
    return (
        prior.team_memory_score,
        prior.calibration_score,
        prior.sample_size,
        prior.recent_error_score,
        prior.domain_experience_score,
        prior.sample_size_score,
        prior.recent_error_component_score,
        prior.prior_score,
    )


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None
