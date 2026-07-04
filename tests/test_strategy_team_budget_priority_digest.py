from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_team_budget_priority_digest.py"
)
GENERATED_AT = datetime(2026, 7, 3, 15, 0, tzinfo=timezone(timedelta(hours=2)))
OBSERVED_AT = datetime(2026, 7, 3, 12, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_team_budget_priority_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-team-budget-priority-digest-test-v0",
        "base_paper_budget": d("1000.000000"),
        "min_priority_score": d("0.250000"),
        "max_drawdown_pressure": d("0.700000"),
        "max_unresolved_exposure_share": d("0.600000"),
        "min_capacity_headroom": d("0.200000"),
    }
    values.update(overrides)
    return module.StrategyTeamBudgetPriorityDigestConfig(**values)


def team(**overrides: object):
    module = api()
    values = {
        "team_id": "macro_team",
        "team_reference": "macro-public",
        "observed_at": OBSERVED_AT,
        "forecast_confidence": d("0.800000"),
        "realized_learning_quality": d("0.700000"),
        "paper_learning_quality": d("0.600000"),
        "cost_aware_edge": d("0.080000"),
        "drawdown_pressure": d("0.200000"),
        "unresolved_exposure": d("120.000000"),
        "paper_budget": d("1000.000000"),
        "capacity_utilization": d("0.500000"),
        "reason_codes": ("team_budget_priority_input",),
    }
    values.update(overrides)
    return module.StrategyTeamBudgetPriorityDigestTeam(**values)


def report(*, teams=(), cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_team_budget_priority_digest(
        teams,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_digest_prioritizes_specialist_paper_budget_with_stable_reasons() -> None:
    result = report(
        teams=(
            team(
                team_id="macro_team",
                team_reference="macro-public",
                forecast_confidence=d("0.900000"),
                realized_learning_quality=d("0.800000"),
                paper_learning_quality=d("0.700000"),
                cost_aware_edge=d("0.120000"),
                drawdown_pressure=d("0.100000"),
                unresolved_exposure=d("100.000000"),
                paper_budget=d("1000.000000"),
                capacity_utilization=d("0.300000"),
            ),
            team(
                team_id="crypto_team",
                team_reference="secret-wallet-token-team",
                forecast_confidence=d("0.700000"),
                realized_learning_quality=d("0.600000"),
                paper_learning_quality=d("0.500000"),
                cost_aware_edge=d("0.050000"),
                drawdown_pressure=d("0.250000"),
                unresolved_exposure=d("500.000000"),
                paper_budget=d("1000.000000"),
                capacity_utilization=d("0.650000"),
            ),
            team(
                team_id="sports_team",
                team_reference="sports-public",
                forecast_confidence=d("0.400000"),
                realized_learning_quality=d("0.300000"),
                paper_learning_quality=d("0.200000"),
                cost_aware_edge=d("0.010000"),
                drawdown_pressure=d("0.800000"),
                unresolved_exposure=d("700.000000"),
                paper_budget=d("1000.000000"),
                capacity_utilization=d("0.900000"),
            ),
        ),
    )

    assert result.generated_at == datetime(2026, 7, 3, 13, 0, tzinfo=UTC)
    assert result.config_version == "strategy-team-budget-priority-digest-test-v0"
    assert result.team_count == d("3")
    assert result.prioritize_count == d("1")
    assert result.watch_count == d("1")
    assert result.deprioritize_count == d("1")
    assert result.total_recommended_paper_budget == d("1400.000000")
    assert result.max_priority_score == d("0.790000")
    assert result.status == "watch"
    assert result.reason_codes == (
        "team_budget_prioritized",
        "team_budget_watch",
        "team_budget_deprioritized",
        "drawdown_pressure_high",
        "unresolved_exposure_high",
        "capacity_headroom_low",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.team_id for row in result.rows) == (
        "macro_team",
        "crypto_team",
        "sports_team",
    )
    assert tuple(row.priority_status for row in result.rows) == (
        "prioritize",
        "watch",
        "deprioritize",
    )

    prioritized, watched, deprioritized = result.rows
    assert prioritized.priority_score == d("0.790000")
    assert prioritized.recommended_paper_budget == d("1200.000000")
    assert prioritized.capacity_headroom == d("0.700000")
    assert prioritized.unresolved_exposure_share == d("0.100000")
    assert prioritized.reason_codes == (
        "team_budget_priority_input",
        "team_budget_prioritized",
        "forecast_confidence_strong",
        "learning_quality_strong",
        "cost_aware_edge_positive",
        "drawdown_pressure_contained",
        "unresolved_exposure_contained",
        "capacity_available",
    )

    assert watched.redacted_team_reference.startswith("team_ref_")
    assert "secret" not in watched.redacted_team_reference
    assert "wallet" not in watched.redacted_team_reference
    assert "token" not in watched.redacted_team_reference
    assert watched.priority_score == d("0.472500")
    assert watched.recommended_paper_budget == d("200.000000")
    assert watched.unresolved_exposure_share == d("0.500000")
    assert watched.capacity_headroom == d("0.350000")
    assert watched.reason_codes == (
        "team_budget_priority_input",
        "team_budget_watch",
        "cost_aware_edge_positive",
        "drawdown_pressure_contained",
        "unresolved_exposure_contained",
        "capacity_available",
    )

    assert deprioritized.priority_score == d("0.080000")
    assert deprioritized.recommended_paper_budget == ZERO
    assert deprioritized.unresolved_exposure_share == d("0.700000")
    assert deprioritized.capacity_headroom == d("0.100000")
    assert deprioritized.reason_codes == (
        "team_budget_priority_input",
        "team_budget_deprioritized",
        "cost_aware_edge_positive",
        "drawdown_pressure_high",
        "unresolved_exposure_high",
        "capacity_headroom_low",
    )


def test_empty_report_is_watch_zeroed_decimal_and_readonly() -> None:
    empty = report()

    assert empty.team_count == d("0")
    assert empty.prioritize_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.deprioritize_count == d("0")
    assert empty.total_recommended_paper_budget == ZERO
    assert empty.max_priority_score == ZERO
    assert empty.status == "watch"
    assert empty.reason_codes == ("strategy_team_budget_priority_digest_empty",)
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    populated = report(teams=(team(),))
    for value in (empty, populated, *populated.rows):
        for item in fields(value):
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(
                (
                    "_count",
                    "_budget",
                    "_score",
                    "_confidence",
                    "_quality",
                    "_edge",
                    "_pressure",
                    "_exposure",
                    "_share",
                    "_utilization",
                    "_headroom",
                ),
            ):
                assert type(item_value) is Decimal


def test_payload_redacts_references_uses_decimal_strings_and_no_floats() -> None:
    module = api()
    result = report(
        teams=(
            team(
                team_id="crypto_team",
                team_reference="secret-wallet-token-team",
                forecast_confidence=d("0.700000"),
                realized_learning_quality=d("0.600000"),
                paper_learning_quality=d("0.500000"),
                cost_aware_edge=d("0.050000"),
                drawdown_pressure=d("0.250000"),
                unresolved_exposure=d("500.000000"),
                paper_budget=d("1000.000000"),
                capacity_utilization=d("0.650000"),
            ),
        ),
        generated_at=datetime(2026, 7, 3, 6, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.strategy_team_budget_priority_digest_payload(result)
    rendered = repr(payload).lower()
    assert payload["generated_at"] == "2026-07-03T13:00:00+00:00"
    assert payload["team_count"] == "1"
    assert payload["total_recommended_paper_budget"] == "200.000000"
    assert payload["max_priority_score"] == "0.472500"
    assert payload["rows"][0]["redacted_team_reference"].startswith("team_ref_")
    assert "secret-wallet" not in rendered
    assert "wallet" not in rendered
    assert "token" not in rendered
    assert_no_float_values(payload)


def test_payload_redacts_phase1_action_boundary_reference_tokens() -> None:
    module = api()
    result = report(
        teams=(
            team(
                team_id="action_surface_team",
                team_reference="auth-order-cancel-replace-live-trading",
            ),
        ),
    )

    payload = module.strategy_team_budget_priority_digest_payload(result)
    redacted_reference = payload["rows"][0]["redacted_team_reference"]
    rendered = repr(payload).lower()
    assert isinstance(redacted_reference, str)
    assert redacted_reference.startswith("team_ref_")
    for token in ("auth", "order", "cancel", "replace", "live", "trading"):
        assert token not in rendered


def test_validation_rejects_bad_types_precision_duplicates_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_strategy_team_budget_priority_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="forecast_confidence must be a Decimal"):
        team(forecast_confidence=0.8)

    with pytest.raises(ValueError, match="paper_budget must be finite"):
        team(paper_budget=Decimal("NaN"))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(generated_at=datetime(2026, 7, 3, 13, 0))

    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        team(observed_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC))

    with pytest.raises(ValueError, match="cost_aware_edge must be a Decimal"):
        team(cost_aware_edge=_DecimalSubclass("0.050000"))

    with pytest.raises(ValueError, match="drawdown_pressure must be a probability Decimal"):
        team(drawdown_pressure=d("1.000001"))

    with pytest.raises(ValueError, match="duplicate team_id"):
        report(
            teams=(
                team(team_id="macro_team", team_reference="first-public"),
                team(team_id="macro_team", team_reference="second-public"),
            ),
        )

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.StrategyTeamBudgetPriorityDigestConfig(paper_only=False)

    row = report(teams=(team(),)).rows[0]
    with pytest.raises(FrozenInstanceError):
        row.priority_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(row, readonly=False)


def test_payload_requires_report_type_and_hard_flags() -> None:
    module = api()
    result = report(teams=(team(),))

    with pytest.raises(ValueError, match="report must be"):
        module.strategy_team_budget_priority_digest_payload(object())

    with pytest.raises(ValueError, match="report_only must be True"):
        module.strategy_team_budget_priority_digest_payload(
            replace(result, report_only=False),
        )


def test_module_scope_has_no_live_trading_persistence_network_or_sensitive_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "db",
        "http",
        "network",
        "order",
        "psycopg",
        "request",
        "socket",
        "sql",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_names = {
        "open",
        "read",
        "write",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "sign",
        "trade",
    }
    forbidden_attr_fragments = (
        "account",
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "file",
        "network",
        "order",
        "persist",
        "request",
        "sign",
        "submit",
        "trade",
        "wallet",
        "write",
    )
    forbidden_attr_names = {
        "open",
        "read",
        "read_text",
        "read_bytes",
        "write",
        "write_text",
        "write_bytes",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert lowered not in forbidden_attr_names
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)

    assert imports
    for module_name in imports:
        assert not module_name.startswith("polymarket_alpha_lab.")
        lowered = module_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_import_fragments)
