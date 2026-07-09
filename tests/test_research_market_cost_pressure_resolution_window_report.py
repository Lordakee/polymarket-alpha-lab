from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_market_cost_pressure_resolution_window_report"
)
GENERATED_AT = datetime(2026, 7, 8, 19, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_COST_PRESSURE_RESOLUTION_WINDOW_REPORT_CONFIG_VERSION
        ),
        "maximum_pass_fee_pressure_ratio": d("0.010000"),
        "maximum_watch_fee_pressure_ratio": d("0.030000"),
        "maximum_pass_spread_pressure_ratio": d("0.020000"),
        "maximum_watch_spread_pressure_ratio": d("0.060000"),
        "maximum_pass_slippage_pressure_ratio": d("0.015000"),
        "maximum_watch_slippage_pressure_ratio": d("0.050000"),
        "minimum_pass_available_depth": d("1000.000000"),
        "minimum_watch_available_depth": d("250.000000"),
        "maximum_pass_settlement_friction_ratio": d("0.050000"),
        "maximum_watch_settlement_friction_ratio": d("0.150000"),
        "minimum_pass_remaining_resolution_hours": d("24.000000"),
        "minimum_watch_remaining_resolution_hours": d("6.000000"),
        "minimum_pass_window_cost_score": d("0.750000"),
        "minimum_watch_window_cost_score": d("0.450000"),
        "fee_pressure_weight": d("0.180000"),
        "spread_pressure_weight": d("0.180000"),
        "slippage_pressure_weight": d("0.180000"),
        "available_depth_weight": d("0.180000"),
        "settlement_friction_weight": d("0.180000"),
        "remaining_window_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchMarketCostPressureResolutionWindowConfig(**values)


def market_input(
    private_event_ref: str = "private-alpha",
    *,
    observed_at: datetime = GENERATED_AT,
    remaining_resolution_hours: Decimal = d("48.000000"),
    fee_pressure_ratio: Decimal = d("0.005000"),
    spread_pressure_ratio: Decimal = d("0.010000"),
    slippage_pressure_ratio: Decimal = d("0.010000"),
    available_depth: Decimal = d("1500.000000"),
    settlement_friction_ratio: Decimal = d("0.020000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketCostPressureResolutionWindowInput(
        private_event_ref=private_event_ref,
        observed_at=observed_at,
        remaining_resolution_hours=remaining_resolution_hours,
        fee_pressure_ratio=fee_pressure_ratio,
        spread_pressure_ratio=spread_pressure_ratio,
        slippage_pressure_ratio=slippage_pressure_ratio,
        available_depth=available_depth,
        settlement_friction_ratio=settlement_friction_ratio,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg: object | None = None) -> Any:
    module = api()
    return module.build_research_market_cost_pressure_resolution_window_report(
        items,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_payload_values(nested))
    if isinstance(value, list):
        return tuple(item for nested in value for item in walk_payload_values(nested))
    return (value,)


def with_recomputed_digest(payload: dict[str, Any]) -> dict[str, Any]:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    payload["derived_validation_digest"] = hashlib.sha256(
        encoded.encode("utf-8"),
    ).hexdigest()
    return payload


def test_scores_window_cost_pressure_pass_watch_and_block_rows() -> None:
    module = api()
    built = report(
        market_input(
            "block-private",
            remaining_resolution_hours=d("2.000000"),
            fee_pressure_ratio=d("0.040000"),
            spread_pressure_ratio=d("0.080000"),
            slippage_pressure_ratio=d("0.060000"),
            available_depth=d("100.000000"),
            settlement_friction_ratio=d("0.200000"),
            reason_codes=("manual_check",),
        ),
        market_input(
            "watch-private",
            remaining_resolution_hours=d("15.000000"),
            fee_pressure_ratio=d("0.020000"),
            spread_pressure_ratio=d("0.040000"),
            slippage_pressure_ratio=d("0.032500"),
            available_depth=d("625.000000"),
            settlement_friction_ratio=d("0.100000"),
        ),
        market_input("pass-private"),
    )

    assert type(built) is module.ResearchMarketCostPressureResolutionWindowReport
    assert module.COST_PRESSURE_RESOLUTION_WINDOW_STATUSES == ("pass", "watch", "block")
    assert built.generated_at == GENERATED_AT
    assert built.status == "block"
    assert built.input_count == d("3.000000")
    assert built.row_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.high_fee_pressure_count == d("2.000000")
    assert built.high_spread_pressure_count == d("2.000000")
    assert built.high_slippage_pressure_count == d("2.000000")
    assert built.thin_depth_count == d("2.000000")
    assert built.high_settlement_friction_count == d("2.000000")
    assert built.short_resolution_window_count == d("2.000000")
    assert built.average_window_cost_pressure_score == d("0.500000")
    assert built.min_remaining_resolution_hours == d("2.000000")
    assert built.min_available_depth == d("100.000000")
    assert built.max_fee_pressure_ratio == d("0.040000")
    assert built.max_spread_pressure_ratio == d("0.080000")
    assert built.max_slippage_pressure_ratio == d("0.060000")
    assert built.max_settlement_friction_ratio == d("0.200000")

    block_row, watch_row, pass_row = built.rows
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    assert block_row.window_cost_pressure_score == ZERO
    assert block_row.reason_codes == (
        "input_manual_check",
        "window_cost_available_depth_block",
        "window_cost_fee_pressure_block",
        "window_cost_remaining_window_block",
        "window_cost_settlement_friction_block",
        "window_cost_slippage_pressure_block",
        "window_cost_spread_pressure_block",
        "window_cost_status_block",
    )
    assert watch_row.fee_pressure_score == d("0.500000")
    assert watch_row.spread_pressure_score == d("0.500000")
    assert watch_row.slippage_pressure_score == d("0.500000")
    assert watch_row.available_depth_score == d("0.500000")
    assert watch_row.settlement_friction_score == d("0.500000")
    assert watch_row.remaining_window_score == d("0.500000")
    assert watch_row.window_cost_pressure_score == d("0.500000")
    assert pass_row.window_cost_pressure_score == ONE
    assert pass_row.reason_codes == (
        "window_cost_available_depth_pass",
        "window_cost_fee_pressure_pass",
        "window_cost_remaining_window_pass",
        "window_cost_settlement_friction_pass",
        "window_cost_slippage_pressure_pass",
        "window_cost_spread_pressure_pass",
        "window_cost_status_pass",
    )


def test_threshold_boundaries_are_inclusive_for_window_and_cost_pressure() -> None:
    boundary = report(
        market_input(
            "pass-boundary",
            remaining_resolution_hours=d("24.000000"),
            fee_pressure_ratio=d("0.010000"),
            spread_pressure_ratio=d("0.020000"),
            slippage_pressure_ratio=d("0.015000"),
            available_depth=d("1000.000000"),
            settlement_friction_ratio=d("0.050000"),
        ),
        market_input(
            "watch-boundary",
            remaining_resolution_hours=d("6.000000"),
        ),
        market_input(
            "block-boundary",
            remaining_resolution_hours=d("5.999999"),
        ),
    )

    assert tuple(row.status for row in boundary.rows) == ("block", "watch", "pass")
    block_row, watch_row, pass_row = boundary.rows
    assert "window_cost_remaining_window_block" in block_row.reason_codes
    assert "window_cost_remaining_window_watch" in watch_row.reason_codes
    assert "window_cost_remaining_window_pass" in pass_row.reason_codes
    assert "window_cost_fee_pressure_pass" in pass_row.reason_codes
    assert "window_cost_spread_pressure_pass" in pass_row.reason_codes
    assert "window_cost_slippage_pressure_pass" in pass_row.reason_codes
    assert "window_cost_available_depth_pass" in pass_row.reason_codes
    assert "window_cost_settlement_friction_pass" in pass_row.reason_codes


def test_public_payload_is_deterministic_and_digest_validated() -> None:
    module = api()
    first = report(
        market_input("zulu-private", reason_codes=("zeta", "alpha")),
        market_input("alpha-private", fee_pressure_ratio=d("0.020000")),
    )
    second = report(
        market_input("alpha-private", fee_pressure_ratio=d("0.020000")),
        market_input("zulu-private", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_market_cost_pressure_resolution_window_report_payload(
        first,
    )
    second_payload = second.public_payload
    digest_payload = dict(first_payload)
    provided_digest = digest_payload.pop("derived_validation_digest")
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert provided_digest == hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    assert first_payload["row_count"] == "2.000000"
    assert first_payload["rows"][0]["fee_pressure_ratio"] == "0.020000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(isinstance(value, Decimal) for value in walk_payload_values(first_payload))
    assert not any(
        isinstance(value, (float, int)) and not isinstance(value, bool)
        for value in walk_payload_values(first_payload)
    )
    assert (
        module.validate_research_market_cost_pressure_resolution_window_report_payload(
            first_payload,
        )
        == first_payload
    )

    tampered = dict(first_payload)
    tampered["row_count"] = "999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_market_cost_pressure_resolution_window_report_payload(
            tampered,
        )

    tampered_recomputed = with_recomputed_digest(
        dict(first_payload) | {"row_count": "999.000000"},
    )
    with pytest.raises(ValueError, match="row_count"):
        module.validate_research_market_cost_pressure_resolution_window_report_payload(
            tampered_recomputed,
        )

    extra_key_payload = with_recomputed_digest(
        dict(first_payload) | {"extra_safe_key": "safe_value"},
    )
    with pytest.raises(ValueError, match="payload keys"):
        module.validate_research_market_cost_pressure_resolution_window_report_payload(
            extra_key_payload,
        )

    non_json_payload = dict(first_payload)
    non_json_payload["row_count"] = d("2.000000")
    with pytest.raises(ValueError, match="JSON-ready"):
        module.validate_research_market_cost_pressure_resolution_window_report_payload(
            non_json_payload,
        )

    tampered_status = with_recomputed_digest(dict(first_payload) | {"status": "blocked"})
    with pytest.raises(ValueError, match="status"):
        module.validate_research_market_cost_pressure_resolution_window_report_payload(
            tampered_status,
        )


def test_public_payload_excludes_private_refs_and_decision_surfaces() -> None:
    module = api()
    built = report(
        market_input(
            "raw-candidate-id-123/market-id-99/will-this-question-resolve/"
            "https://example.test/source?token=secret&wallet=abc&order=1",
        ),
    )
    payload = module.research_market_cost_pressure_resolution_window_report_payload(built)
    rendered = json.dumps(payload, sort_keys=True).lower()

    for forbidden in (
        "raw-candidate-id-123",
        "market-id-99",
        "will-this-question-resolve",
        "https://example.test",
        "source?token",
        "secret",
        "wallet",
        "order",
        "private_event_ref",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "trade",
        "live",
        "recommend",
        "position",
        "sizing",
        "execution",
    ):
        assert forbidden not in rendered

    unsafe_report = replace(built)
    object.__setattr__(
        unsafe_report,
        "reason_codes",
        ("window_cost_status_pass", "token_seen"),
    )
    object.__setattr__(unsafe_report, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_market_cost_pressure_resolution_window_report_payload(
            unsafe_report,
        )


def test_custom_config_and_validation_reject_bad_boundaries_and_types() -> None:
    module = api()
    custom = config(
        maximum_pass_fee_pressure_ratio=d("0.020000"),
        maximum_watch_fee_pressure_ratio=d("0.040000"),
    )
    custom_report = report(
        market_input("custom-pass", fee_pressure_ratio=d("0.020000")),
        cfg=custom,
    )

    assert custom_report.status == "pass"
    assert custom_report.rows[0].fee_pressure_score == ONE
    with pytest.raises(ValueError, match="maximum_pass_fee_pressure_ratio"):
        config(maximum_pass_fee_pressure_ratio=DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="maximum_watch_spread_pressure_ratio"):
        config(maximum_watch_spread_pressure_ratio=0.06)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="maximum_pass_fee_pressure_ratio"):
        config(maximum_pass_fee_pressure_ratio=d("0.040000"))
    with pytest.raises(ValueError, match="minimum_pass_available_depth"):
        config(minimum_pass_available_depth=d("100.000000"))
    with pytest.raises(ValueError, match="maximum_pass_settlement_friction_ratio"):
        config(maximum_pass_settlement_friction_ratio=d("0.200000"))
    with pytest.raises(ValueError, match="minimum_pass_remaining_resolution_hours"):
        config(minimum_pass_remaining_resolution_hours=d("3.000000"))
    with pytest.raises(ValueError, match="weights must sum"):
        config(fee_pressure_weight=d("0.190000"))
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_cost_pressure_resolution_window_report(
            (market_input(),),
            config=config(),
            generated_at=datetime(2026, 7, 8, 19, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_cost_pressure_resolution_window_report(
            (market_input(),),
            config=config(),
            generated_at=DatetimeSubclass(2026, 7, 8, 19, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        market_input(observed_at=datetime(2026, 7, 8, 19, 0))
    with pytest.raises(ValueError, match="fee_pressure_ratio"):
        market_input(fee_pressure_ratio=d("NaN"))
    with pytest.raises(ValueError, match="spread_pressure_ratio"):
        market_input(spread_pressure_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="available_depth"):
        market_input(available_depth=-d("1.000000"))
    with pytest.raises(ValueError, match="settlement_friction_ratio"):
        market_input(settlement_friction_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        market_input(reason_codes=("token_seen",))
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        report(market_input(readonly=False))

    built = report(market_input())
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="blocked")
    with pytest.raises(ValueError, match="window_cost_pressure_score"):
        replace(built.rows[0], window_cost_pressure_score=ZERO)
    with pytest.raises(ValueError, match="status"):
        replace(built, status="watch")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="report"):
        module.research_market_cost_pressure_resolution_window_report_payload(object())


def test_public_objects_are_frozen_dataclasses_with_decimal_numeric_fields() -> None:
    module = api()
    built = report(market_input())

    for item in (config(), market_input(), built, *built.reason_code_counts, *built.rows):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True

    with pytest.raises(FrozenInstanceError):
        built.row_count = d("2.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].window_cost_pressure_score = ZERO  # type: ignore[misc]

    public_classes = (
        module.ResearchMarketCostPressureResolutionWindowConfig,
        module.ResearchMarketCostPressureResolutionWindowInput,
        module.ResearchMarketCostPressureResolutionWindowRow,
        module.ResearchMarketCostPressureResolutionWindowReasonCodeCount,
        module.ResearchMarketCostPressureResolutionWindowReport,
    )
    for klass in public_classes:
        assert klass.__dataclass_params__.frozen is True
        for field in fields(klass):
            if field.name in {
                "paper_only",
                "report_only",
                "readonly",
                "private_event_ref",
                "config_version",
                "public_row_ref",
                "status",
                "reason_code",
                "reason_codes",
                "reason_code_counts",
                "rows",
                "derived_validation_digest",
                "observed_at",
                "generated_at",
            }:
                continue
            assert field.type in (Decimal, "Decimal")


def test_owned_module_has_no_storage_network_wallet_or_decision_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_cost_pressure_resolution_window_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    tree = ast.parse(module_path.read_text(encoding="utf-8"))

    for forbidden in (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "read_text",
        "write_text",
        "connect(",
        "execute(",
        "database",
        "network",
        "auth",
        "private_key",
        "api_key",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recommend",
        "position",
        "sizing",
        "execution",
    ):
        assert forbidden not in source

    forbidden_calls = {
        "open",
        "connect",
        "execute",
        "request",
        "create_order",
        "submit_order",
        "place_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
