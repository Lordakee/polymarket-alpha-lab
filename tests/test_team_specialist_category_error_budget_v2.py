from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.team_specialist_category_error_budget_v2 import (
    TeamSpecialistCategoryErrorBudgetV2Observation,
    TeamSpecialistCategoryErrorBudgetV2Report,
    build_team_specialist_category_error_budget_v2_report,
    team_specialist_category_error_budget_v2_payload,
)


GENERATED_AT = datetime(2026, 2, 15, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    specialist_id: str,
    category_id: str,
    market_id: str,
    forecast_probability: str,
    resolved_probability: str,
    *,
    team_id: str = "team-alpha",
    category_importance: str = "0.500000",
    source_contradiction_miss: str = "0.000000",
    observed_at: datetime | None = None,
) -> TeamSpecialistCategoryErrorBudgetV2Observation:
    return TeamSpecialistCategoryErrorBudgetV2Observation(
        team_id=team_id,
        specialist_id=specialist_id,
        category_id=category_id,
        market_id=market_id,
        forecast_probability=d(forecast_probability),
        resolved_probability=d(resolved_probability),
        category_importance=d(category_importance),
        source_contradiction_miss=d(source_contradiction_miss),
        observed_at=observed_at or GENERATED_AT - timedelta(days=1),
    )


def report(
    *rows: TeamSpecialistCategoryErrorBudgetV2Observation,
) -> TeamSpecialistCategoryErrorBudgetV2Report:
    return build_team_specialist_category_error_budget_v2_report(
        rows,
        generated_at=GENERATED_AT,
    )


def test_builds_error_budget_prioritizing_recent_misses_and_contradictions() -> None:
    alpha_recent_high = observation(
        "specialist-alpha",
        "category-sports",
        "market-alpha-1",
        "0.900000",
        "0.000000",
        category_importance="0.950000",
        source_contradiction_miss="1.000000",
        observed_at=GENERATED_AT - timedelta(days=1),
    )
    alpha_recent_mid = observation(
        "specialist-alpha",
        "category-sports",
        "market-alpha-2",
        "0.800000",
        "0.000000",
        category_importance="0.950000",
        source_contradiction_miss="1.000000",
        observed_at=GENERATED_AT - timedelta(days=2),
    )
    alpha_older = observation(
        "specialist-alpha",
        "category-sports",
        "market-alpha-3",
        "0.550000",
        "0.000000",
        category_importance="0.950000",
        observed_at=GENERATED_AT - timedelta(days=20),
    )
    beta_rows = (
        observation(
            "specialist-beta",
            "category-politics",
            "market-beta-1",
            "0.550000",
            "0.500000",
            team_id="team-beta",
            category_importance="0.400000",
        ),
        observation(
            "specialist-beta",
            "category-politics",
            "market-beta-2",
            "0.600000",
            "0.500000",
            team_id="team-beta",
            category_importance="0.400000",
        ),
        observation(
            "specialist-beta",
            "category-politics",
            "market-beta-3",
            "0.700000",
            "0.500000",
            team_id="team-beta",
            category_importance="0.400000",
        ),
    )

    result = report(alpha_older, *beta_rows, alpha_recent_mid, alpha_recent_high)
    repeat_result = report(alpha_recent_high, alpha_recent_mid, alpha_older, *reversed(beta_rows))

    assert result.error_budget_status == "blocked"
    assert result.row_count == d("2.000000")
    assert result.observation_count == d("6.000000")
    assert result.recent_forecast_miss_count == d("2.000000")
    assert result.source_contradiction_miss_count == d("2.000000")
    assert result.average_brier_like_error == d("0.300833")
    assert result.derived_validation_digest == repeat_result.derived_validation_digest

    alpha, beta = result.rows
    assert (alpha.team_id, alpha.specialist_id, alpha.category_id) == (
        "team-alpha",
        "specialist-alpha",
        "category-sports",
    )
    assert alpha.rank == d("1.000000")
    assert alpha.sample_size == d("3.000000")
    assert alpha.recent_forecast_miss_count == d("2.000000")
    assert alpha.brier_like_error == d("0.584167")
    assert alpha.category_importance == d("0.950000")
    assert alpha.source_contradiction_miss_count == d("2.000000")
    assert alpha.recovery_priority_score == d("0.811667")
    assert alpha.recovery_priority == "critical"
    assert alpha.error_budget_status == "blocked"
    assert alpha.reason_codes == (
        "error_budget_blocked",
        "sample_size_sufficient",
        "recent_forecast_misses_blocked",
        "brier_like_error_high",
        "category_importance_high",
        "source_contradiction_misses_blocked",
        "recovery_priority_critical",
    )

    assert (beta.team_id, beta.specialist_id, beta.category_id) == (
        "team-beta",
        "specialist-beta",
        "category-politics",
    )
    assert beta.rank == d("2.000000")
    assert beta.brier_like_error == d("0.017500")
    assert beta.recovery_priority_score == d("0.071500")
    assert beta.recovery_priority == "low"
    assert beta.error_budget_status == "pass"
    assert beta.reason_codes == (
        "error_budget_pass",
        "sample_size_sufficient",
        "recent_forecast_misses_clear",
        "brier_like_error_low",
        "category_importance_medium",
        "source_contradiction_misses_clear",
        "recovery_priority_low",
    )


def test_insufficient_sample_blocks_even_when_brier_error_is_low() -> None:
    result = report(
        observation(
            "specialist-alpha",
            "category-politics",
            "market-alpha-thin",
            "0.510000",
            "0.500000",
            category_importance="0.300000",
        ),
    )

    row = result.rows[0]
    assert result.error_budget_status == "blocked"
    assert row.sample_size == d("1.000000")
    assert row.brier_like_error == d("0.000100")
    assert row.error_budget_status == "blocked"
    assert row.recovery_priority == "high"
    assert "sample_size_thin" in row.reason_codes


def test_payload_stringifies_decimals_and_rejects_numeric_downgrades() -> None:
    result = report(
        observation(
            "specialist-alpha",
            "category-politics",
            "market-alpha",
            "0.550000",
            "0.500000",
        ),
        observation(
            "specialist-alpha",
            "category-politics",
            "market-beta",
            "0.600000",
            "0.500000",
        ),
        observation(
            "specialist-alpha",
            "category-politics",
            "market-gamma",
            "0.650000",
            "0.500000",
        ),
    )

    payload = team_specialist_category_error_budget_v2_payload(result)

    assert payload == result.payload
    assert payload["observation_count"] == "3.000000"
    assert payload["rows"][0]["brier_like_error"] == "0.011667"
    assert payload["rows"][0]["sample_size"] == "3.000000"
    assert not _contains_numeric_downgrade(payload)
    json.dumps(payload, sort_keys=True)

    with pytest.raises(ValueError, match="float"):
        team_specialist_category_error_budget_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "recovery_priority_score": 0.5,
            },
        )
    with pytest.raises(ValueError, match="numeric"):
        team_specialist_category_error_budget_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "observation_count": 3,
            },
        )


def test_dataclasses_are_frozen_digest_checked_and_flags_hard_true() -> None:
    result = report(
        observation(
            "specialist-alpha",
            "category-politics",
            "market-alpha",
            "0.550000",
            "0.500000",
        ),
    )

    assert is_dataclass(result)
    assert is_dataclass(result.rows[0])
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    with pytest.raises(FrozenInstanceError):
        result.readonly = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.rows[0].paper_only = False  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(result, paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="forecast_probability"):
        observation(
            "specialist-alpha",
            "category-politics",
            "market-alpha",
            "0.550000",
            "0.500000",
        ).__class__(
            team_id="team-alpha",
            specialist_id="specialist-alpha",
            category_id="category-politics",
            market_id="market-alpha",
            forecast_probability=_DecimalSubclass("0.550000"),
            resolved_probability=d("0.500000"),
            category_importance=d("0.500000"),
            source_contradiction_miss=d("0.000000"),
            observed_at=GENERATED_AT,
        )


def test_rejects_unsafe_values_future_rows_and_duplicates() -> None:
    with pytest.raises(ValueError, match="unsafe"):
        observation(
            "specialist-alpha",
            "category-politics",
            "market-wallet",
            "0.550000",
            "0.500000",
        )

    with pytest.raises(ValueError, match="after generated_at"):
        report(
            observation(
                "specialist-alpha",
                "category-politics",
                "market-alpha",
                "0.550000",
                "0.500000",
                observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )

    duplicate = observation(
        "specialist-alpha",
        "category-politics",
        "market-alpha",
        "0.550000",
        "0.500000",
        observed_at=GENERATED_AT - timedelta(days=1),
    )
    with pytest.raises(ValueError, match="duplicate"):
        report(duplicate, duplicate)


def test_empty_report_is_blocked_with_deterministic_digest() -> None:
    result = report()
    repeat_result = report()

    assert result.error_budget_status == "blocked"
    assert result.row_count == d("0.000000")
    assert result.observation_count == d("0.000000")
    assert result.reason_codes == ("empty_error_budget_observations",)
    assert result.derived_validation_digest == repeat_result.derived_validation_digest


def test_static_module_surface_has_no_io_network_auth_wallet_or_trading_hooks() -> None:
    source = Path(
        "src/polymarket_alpha_lab/team_specialist_category_error_budget_v2.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_modules = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "sqlite3",
        "psycopg",
        "supabase",
        "sqlalchemy",
    )
    forbidden_call_names = (
        "open",
        "connect",
        "request",
        "urlopen",
        "Session",
        "client",
        "place_order",
        "cancel_order",
        "insert",
        "execute",
        "commit",
        "write",
    )
    forbidden_public_fragments = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "db",
        "database",
        "persist",
        "signing",
        "buy",
        "sell",
        "trade",
    )

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imported = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
            )
            assert not any(
                name == forbidden or name.startswith(f"{forbidden}.")
                for name in imported
                for forbidden in forbidden_modules
            )
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_call_names
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_call_names
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float

    namespace: dict[str, object] = {}
    exec(compile(tree, "<surface>", "exec"), namespace)
    exported = namespace["__all__"]
    assert isinstance(exported, tuple)
    assert not any(
        fragment in public_name.lower()
        for public_name in exported
        for fragment in forbidden_public_fragments
    )


def _contains_numeric_downgrade(value: object) -> bool:
    if type(value) in (float, int):
        return True
    if isinstance(value, dict):
        return any(_contains_numeric_downgrade(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_numeric_downgrade(item) for item in value)
    return False
