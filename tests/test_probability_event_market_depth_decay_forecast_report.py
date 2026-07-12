from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from typing import get_type_hints

import pytest

from polymarket_alpha_lab.probability_event_market_depth_decay_forecast_report import (
    ProbabilityEventMarketDepthDecayForecastReport,
    build_probability_event_market_depth_decay_forecast_report,
    probability_event_market_depth_decay_forecast_payload_digest,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_market_depth_decay_forecast_report.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def report(**overrides: object) -> ProbabilityEventMarketDepthDecayForecastReport:
    values = {
        "current_depth_probability": d("0.820000"),
        "historical_depth_probability": d("0.750000"),
        "depth_decay_probability": d("0.040000"),
        "spread_probability": d("0.030000"),
        "market_close_hours": d("72.000000"),
    }
    values.update(overrides)
    return build_probability_event_market_depth_decay_forecast_report(**values)


def test_stable_depth_forecast_payload_digest_and_public_schema() -> None:
    first = report()
    second = report()

    assert type(first) is ProbabilityEventMarketDepthDecayForecastReport
    assert is_dataclass(first)
    assert first.__dataclass_params__.frozen is True
    assert first.depth_decay_status == "stable"
    assert first.forecast_depth_probability == d("0.805000")
    assert first.reason_codes == ("depth_decay_forecast_stable",)
    assert first.manual_next_step == "continue_manual_market_depth_monitoring"
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second
    assert first.payload_digest == second.payload_digest
    assert probability_event_market_depth_decay_forecast_payload_digest(first) == (
        first.payload_digest
    )

    payload = first.public_payload
    assert payload == {
        "current_depth_probability": "0.820000",
        "historical_depth_probability": "0.750000",
        "depth_decay_probability": "0.040000",
        "spread_probability": "0.030000",
        "market_close_hours": "72.000000",
        "depth_decay_status": "stable",
        "forecast_depth_probability": "0.805000",
        "reason_codes": ("depth_decay_forecast_stable",),
        "manual_next_step": "continue_manual_market_depth_monitoring",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "payload_digest": first.payload_digest,
    }
    json.dumps(payload, sort_keys=True)
    expected_digest = sha256(
        json.dumps(
            {**payload, "payload_digest": ""},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    assert first.payload_digest == expected_digest
    assert _float_or_int_paths(payload) == ()

    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["depth_decay_status"] = "blocked"


def test_watch_and_block_depth_decay_statuses_are_reasoned_from_inputs() -> None:
    watched = report(
        current_depth_probability=d("0.620000"),
        historical_depth_probability=d("0.750000"),
        depth_decay_probability=d("0.120000"),
        spread_probability=d("0.080000"),
        market_close_hours=d("20.000000"),
    )
    blocked = report(
        current_depth_probability=d("0.310000"),
        historical_depth_probability=d("0.760000"),
        depth_decay_probability=d("0.260000"),
        spread_probability=d("0.180000"),
        market_close_hours=d("4.000000"),
    )

    assert watched.depth_decay_status == "watch"
    assert watched.forecast_depth_probability == d("0.460000")
    assert watched.reason_codes == (
        "current_depth_below_historical_watch",
        "depth_decay_probability_watch",
        "spread_probability_watch",
        "market_close_hours_watch",
    )
    assert watched.manual_next_step == "review_market_depth_decay_forecast_manually"

    assert blocked.depth_decay_status == "blocked"
    assert blocked.forecast_depth_probability == d("0.000000")
    assert blocked.reason_codes == (
        "current_depth_below_historical_block",
        "depth_decay_probability_block",
        "spread_probability_block",
        "market_close_hours_block",
    )
    assert blocked.manual_next_step == "pause_and_escalate_market_depth_review"


def test_frozen_decimal_only_exact_types_and_hard_flags() -> None:
    result = report()

    with pytest.raises(FrozenInstanceError):
        result.depth_decay_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="current_depth_probability"):
        report(current_depth_probability=0.82)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="historical_depth_probability"):
        report(historical_depth_probability=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="depth_decay_probability"):
        report(depth_decay_probability=Decimal("NaN"))
    with pytest.raises(ValueError, match="market_close_hours"):
        report(market_close_hours=d("-1.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(result, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="forecast_depth_probability"):
        replace(result, forecast_depth_probability=d("0.500000"))
    with pytest.raises(ValueError, match="payload_digest"):
        replace(result, payload_digest="0" * 64)

    hints = get_type_hints(ProbabilityEventMarketDepthDecayForecastReport)
    for field in fields(ProbabilityEventMarketDepthDecayForecastReport):
        value = getattr(result, field.name)
        if field.name.endswith("_probability") or field.name == "market_close_hours":
            assert type(value) is Decimal
            assert hints[field.name] is Decimal
        elif type(value) in (int, float):
            pytest.fail(f"runtime public numeric field is not Decimal: {field.name}")


def test_module_is_readonly_report_only_and_has_no_execution_or_persistence_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "web3",
        "private_key",
        "wallet",
        "authentication",
        "live",
        "sign",
        "jsonl",
        "place_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "auto_execute",
        "database",
        "network",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "urllib",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "web3",
    }
    forbidden_call_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "delete",
        "execute",
        "executemany",
        "fetch",
        "insert",
        "open",
        "post",
        "put",
        "rollback",
        "sell",
        "send",
        "sign",
        "upsert",
        "write",
        "write_text",
        "write_bytes",
    }
    imported_roots: set[str] = set()
    call_names: set[str] = set()
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.add(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.add(function.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    assert not imported_roots.intersection(forbidden_imports)
    assert not call_names.intersection(forbidden_call_names)
    assert float_constants == []


def _float_or_int_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if type(value) in (int, float, Decimal):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_or_int_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, (list, tuple)):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_or_int_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()
