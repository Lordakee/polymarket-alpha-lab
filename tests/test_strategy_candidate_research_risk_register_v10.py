from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 10, 15, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    module_name = "polymarket_alpha_lab.strategy_candidate_research_risk_register_v10"
    assert importlib.util.find_spec(module_name) is not None
    return importlib.import_module(module_name)


def d(value: str) -> Decimal:
    return Decimal(value)


def risk(**overrides: object):
    module = api()
    values = {
        "market_id": "market-alpha",
        "risk_items": ("thin-evidence",),
        "severity_score": d("0.200000"),
        "likelihood_score": d("0.300000"),
        "owner_team": "policy_research",
        "time_to_resolution_minutes": d("360"),
        "mitigation_status": "mitigated",
    }
    values.update(overrides)
    return module.StrategyCandidateResearchRiskItem(**values)


def report(*items: object, generated_at: datetime = GENERATED_AT, cfg: object | None = None):
    module = api()
    return module.build_strategy_candidate_research_risk_register(
        items,
        config=cfg if cfg is not None else module.StrategyCandidateResearchRiskRegisterConfig(),
        generated_at=generated_at,
    )


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def test_register_summarizes_candidate_research_risks_by_priority() -> None:
    result = report(
        risk(
            market_id="market-block",
            risk_items=("source-conflict", "manual-review"),
            severity_score=d("0.900000"),
            likelihood_score=d("0.800000"),
            owner_team="policy_research",
            time_to_resolution_minutes=d("45"),
            mitigation_status="open",
        ),
        risk(
            market_id="market-watch",
            risk_items=("slow-review",),
            severity_score=d("0.500000"),
            likelihood_score=d("0.600000"),
            owner_team="crypto_research",
            time_to_resolution_minutes=d("180"),
            mitigation_status="in_progress",
        ),
        risk(
            market_id="market-pass",
            risk_items=("resolved-gap",),
            severity_score=d("0.200000"),
            likelihood_score=d("0.300000"),
            owner_team="sports_research",
            time_to_resolution_minutes=d("0"),
            mitigation_status="mitigated",
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.generated_at.tzinfo is UTC
    assert result.config_version == "strategy-candidate-research-risk-register-v10"
    assert result.risk_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.max_risk_score == d("0.720000")
    assert result.register_status == "block"
    assert result.mitigation_priority == "urgent"
    assert result.reason_codes == (
        "candidate_research_risk_register_block",
        "research_risk_score_block",
        "research_resolution_due_soon_block",
        "unmitigated_research_risk",
        "research_risk_score_watch",
        "research_resolution_due_soon_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.register_status for row in result.risk_rows) == (
        "block",
        "watch",
        "pass",
    )
    blocked, watched, passed = result.risk_rows
    assert blocked.market_id == "market-block"
    assert blocked.risk_item_count == d("2")
    assert blocked.risk_score == d("0.720000")
    assert blocked.mitigation_priority == "urgent"
    assert blocked.reason_codes == (
        "research_risk_score_block",
        "research_resolution_due_soon_block",
        "unmitigated_research_risk",
    )
    assert watched.risk_score == d("0.300000")
    assert watched.mitigation_priority == "elevated"
    assert passed.risk_score == d("0.060000")
    assert passed.reason_codes == ("candidate_research_risk_pass",)

    assert tuple(row.market_id for row in result.top_risks) == (
        "market-block",
        "market-watch",
        "market-pass",
    )


def test_empty_register_is_readonly_and_zeroed_with_decimal_values() -> None:
    result = report()

    assert result.risk_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.max_risk_score == ZERO
    assert result.register_status == "pass"
    assert result.mitigation_priority == "none"
    assert result.reason_codes == ("candidate_research_risk_register_empty",)
    assert result.top_risks == ()
    assert result.risk_rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    populated = report(risk())
    for value in (result, populated, *populated.risk_rows):
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name.endswith(("_count", "_score", "_minutes")):
                assert type(item_value) is Decimal


def test_payload_is_json_ready_readonly_and_uses_decimal_strings() -> None:
    module = api()
    result = report(
        risk(
            market_id="payload-market",
            risk_items=("resolution-gap",),
            severity_score=d("0.750000"),
            likelihood_score=d("0.800000"),
            owner_team="macro_research",
            time_to_resolution_minutes=d("30"),
            mitigation_status="open",
        ),
        generated_at=datetime(2026, 7, 6, 6, 15, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = module.strategy_candidate_research_risk_register_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload["generated_at"] == "2026-07-06T10:15:00+00:00"
    assert payload["risk_count"] == "1"
    assert payload["max_risk_score"] == "0.600000"
    assert payload["register_status"] == "block"
    assert payload["mitigation_priority"] == "urgent"
    assert payload["top_risks"][0]["risk_score"] == "0.600000"
    assert payload["top_risks"][0]["time_to_resolution_minutes"] == "30"
    assert payload["top_risks"][0]["risk_items"] == ["resolution-gap"]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_int_or_float_values(payload)
    for forbidden in ("auth", "wallet", "broker", "order placement", "private_key"):
        assert forbidden not in rendered


def test_rejects_invalid_inputs_thresholds_datetimes_duplicates_and_flags() -> None:
    module = api()
    valid = risk()

    with pytest.raises(ValueError, match="risk_items"):
        risk(risk_items=())
    with pytest.raises(ValueError, match="severity_score"):
        risk(severity_score=d("1.000001"))
    with pytest.raises(ValueError, match="likelihood_score must be a Decimal"):
        risk(likelihood_score=1)
    with pytest.raises(ValueError, match="exact Decimal"):
        risk(severity_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="time_to_resolution_minutes must be integral"):
        risk(time_to_resolution_minutes=d("1.5"))
    with pytest.raises(ValueError, match="mitigation_status"):
        risk(mitigation_status="unknown")
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(valid, generated_at=datetime(2026, 7, 6, 10, 15))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(valid, generated_at=_DatetimeSubclass(2026, 7, 6, 10, 15, tzinfo=UTC))
    with pytest.raises(ValueError, match="duplicate market risk"):
        report(valid, valid)
    with pytest.raises(ValueError, match="paper_only"):
        replace(valid, paper_only=False)
    with pytest.raises(ValueError, match="block_risk_score"):
        module.StrategyCandidateResearchRiskRegisterConfig(
            watch_risk_score=d("0.700000"),
            block_risk_score=d("0.600000"),
        )
    with pytest.raises(ValueError, match="report"):
        module.strategy_candidate_research_risk_register_payload(object())


def test_dataclasses_are_frozen_exact_and_report_validation_is_strict() -> None:
    module = api()
    item = risk()
    result = report(item)
    row = result.risk_rows[0]

    with pytest.raises(FrozenInstanceError):
        row.register_status = "block"  # type: ignore[misc]

    for klass in (
        module.StrategyCandidateResearchRiskRegisterConfig,
        module.StrategyCandidateResearchRiskItem,
        module.StrategyCandidateResearchRiskRow,
        module.StrategyCandidateResearchRiskRegisterReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(ValueError, match="risk_score"):
        replace(row, risk_score=d("0.900000"))
    with pytest.raises(ValueError, match="risk_count"):
        replace(result, risk_count=d("2"))
    with pytest.raises(ValueError, match="top_risks"):
        replace(result, top_risks=(row, row))


def test_source_has_no_io_persistence_network_or_live_action_surface() -> None:
    module = api()
    source_path = Path(module.__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"

    banned_import_roots = {
        "asyncio",
        "builtins.open",
        "csv",
        "http",
        "json",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    assert not (set(imports) & banned_import_roots)

    lowered = source.lower()
    for term in (
        "database",
        "persist",
        "storage",
        "network",
        "live",
        "trade",
        "auth",
        "wallet",
        "broker",
        "order placement",
        "private_key",
        "requests",
        "http",
    ):
        assert term not in lowered
