from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.team_specialist_forecast_error_memory_rank_v2 import (
    TeamSpecialistForecastErrorMemoryPublicPayloadItem,
    TeamSpecialistForecastErrorMemoryRankConfig,
    TeamSpecialistForecastErrorMemoryRankRecord,
    TeamSpecialistForecastErrorMemoryRankReport,
    build_team_specialist_forecast_error_memory_rank_v2_report,
    team_specialist_forecast_error_memory_rank_v2_payload,
)


GENERATED_AT = datetime(2026, 1, 10, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def record(
    specialist_id: str,
    forecast_probability: str,
    resolved_probability: str,
    *,
    team_id: str = "team-alpha",
    market_id: str | None = None,
    prior_absolute_error: str | None = None,
    observed_at: datetime | None = None,
):
    return TeamSpecialistForecastErrorMemoryRankRecord(
        team_id=team_id,
        specialist_id=specialist_id,
        market_id=market_id or f"market-{specialist_id}",
        forecast_probability=d(forecast_probability),
        resolved_probability=d(resolved_probability),
        prior_absolute_error=(
            None if prior_absolute_error is None else d(prior_absolute_error)
        ),
        observed_at=observed_at or GENERATED_AT - timedelta(hours=1),
    )


def report(*records: object, **overrides: object) -> TeamSpecialistForecastErrorMemoryRankReport:
    values = {
        "records": records,
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return build_team_specialist_forecast_error_memory_rank_v2_report(**values)


def test_forecast_error_memory_ranking_penalizes_repeated_errors() -> None:
    result = report(
        record("alpha", "0.700000", "1.000000", market_id="market-a1"),
        record("alpha", "0.200000", "1.000000", market_id="market-a2"),
        record("beta", "0.550000", "1.000000", market_id="market-b1"),
        record("beta", "0.600000", "1.000000", market_id="market-b2"),
    )

    assert result.memory_status == "watch"
    assert result.specialist_count == d("2.000000")
    assert result.record_count == d("4.000000")
    assert tuple(row.specialist_id for row in result.rows) == ("beta", "alpha")

    beta, alpha = result.rows
    assert beta.rank == d("1.000000")
    assert beta.average_absolute_error == d("0.425000")
    assert beta.repeated_error_count == d("1.000000")
    assert beta.repeated_error_penalty == d("0.100000")
    assert beta.memory_score == d("0.475000")
    assert beta.reason_codes == ("recent_error_watch",)

    assert alpha.rank == d("2.000000")
    assert alpha.average_absolute_error == d("0.550000")
    assert alpha.repeated_error_count == d("2.000000")
    assert alpha.repeated_error_penalty == d("0.200000")
    assert alpha.memory_score == d("0.250000")
    assert "repeated_error_penalty_applied" in alpha.reason_codes


def test_recent_improvement_boost_lifts_otherwise_similar_specialist() -> None:
    result = report(
        record(
            "improving",
            "0.700000",
            "1.000000",
            market_id="market-improving",
            prior_absolute_error="0.700000",
            observed_at=GENERATED_AT - timedelta(days=1),
        ),
        record(
            "steady",
            "0.700000",
            "1.000000",
            market_id="market-steady",
            prior_absolute_error="0.300000",
            observed_at=GENERATED_AT - timedelta(days=1),
        ),
    )

    improving, steady = result.rows
    assert (improving.specialist_id, steady.specialist_id) == ("improving", "steady")
    assert improving.recent_improvement_count == d("1.000000")
    assert improving.recent_improvement_boost == d("0.100000")
    assert improving.memory_score == d("0.800000")
    assert "recent_improvement_boost_applied" in improving.reason_codes
    assert steady.memory_score == d("0.700000")


def test_serialization_stringifies_decimals_and_rejects_float_payloads() -> None:
    result = report(
        record("alpha", "0.750000", "1.000000"),
        public_payload=(
            TeamSpecialistForecastErrorMemoryPublicPayloadItem(
                key="source_label",
                value="internal_public_report",
            ),
        ),
    )

    payload = team_specialist_forecast_error_memory_rank_v2_payload(result)
    assert payload == result.payload
    assert payload["specialist_count"] == "1.000000"
    assert payload["rows"][0]["memory_score"] == "0.750000"
    assert payload["public_payload"][0]["value"] == "internal_public_report"
    assert not _contains_float(payload)
    json.dumps(payload, sort_keys=True)

    with pytest.raises(ValueError, match="float"):
        team_specialist_forecast_error_memory_rank_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "score": 0.1,
            },
        )


def test_dataclasses_are_frozen_and_hard_flags_are_enforced() -> None:
    result = report(record("alpha", "0.750000", "1.000000"))

    assert is_dataclass(result)
    assert is_dataclass(result.rows[0])
    for value in (result, result.rows[0], record("gamma", "0.600000", "1.000000")):
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    with pytest.raises(ValueError, match="paper_only"):
        replace(result, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        TeamSpecialistForecastErrorMemoryRankRecord(
            team_id="team-alpha",
            specialist_id="alpha",
            market_id="market-alpha",
            forecast_probability=d("0.750000"),
            resolved_probability=d("1.000000"),
            observed_at=GENERATED_AT,
            readonly=False,
        )


def test_digest_tampering_and_numeric_type_downgrades_are_rejected() -> None:
    result = report(record("alpha", "0.750000", "1.000000"))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="forecast_probability"):
        TeamSpecialistForecastErrorMemoryRankRecord(
            team_id="team-alpha",
            specialist_id="alpha",
            market_id="market-alpha",
            forecast_probability=_DecimalSubclass("0.750000"),
            resolved_probability=d("1.000000"),
            observed_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="resolved_probability"):
        TeamSpecialistForecastErrorMemoryRankRecord(
            team_id="team-alpha",
            specialist_id="alpha",
            market_id="market-alpha",
            forecast_probability=d("0.750000"),
            resolved_probability=1,  # type: ignore[arg-type]
            observed_at=GENERATED_AT,
        )


def test_unsafe_public_keys_and_values_are_rejected() -> None:
    for term in (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            TeamSpecialistForecastErrorMemoryPublicPayloadItem(
                key=f"{term}_field",
                value="safe_value",
            )
        with pytest.raises(ValueError, match="unsafe"):
            TeamSpecialistForecastErrorMemoryPublicPayloadItem(
                key="safe_field",
                value=f"contains_{term}_term",
            )

    with pytest.raises(ValueError, match="unsafe"):
        report(record("alpha", "0.750000", "1.000000", market_id="market-wallet"))
    with pytest.raises(ValueError, match="unsafe"):
        team_specialist_forecast_error_memory_rank_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet_field": "safe_value",
            },
        )


def test_static_module_surface_has_no_unsafe_io_or_trading_entrypoints() -> None:
    source = Path(
        "src/polymarket_alpha_lab/team_specialist_forecast_error_memory_rank_v2.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_modules = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
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
    )
    forbidden_public_fragments = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
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
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_call_names
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


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False
