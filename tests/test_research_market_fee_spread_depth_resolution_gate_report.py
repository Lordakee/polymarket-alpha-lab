from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_fee_spread_depth_resolution_gate_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_FEE_SPREAD_DEPTH_RESOLUTION_GATE_REPORT_CONFIG_VERSION
        ),
        "maximum_pass_fee_drag_ratio": d("0.010000"),
        "maximum_watch_fee_drag_ratio": d("0.030000"),
        "maximum_pass_spread_width_ratio": d("0.030000"),
        "maximum_watch_spread_width_ratio": d("0.080000"),
        "minimum_pass_available_depth": d("1000.000000"),
        "minimum_watch_available_depth": d("250.000000"),
        "maximum_pass_resolution_friction_ratio": d("0.050000"),
        "maximum_watch_resolution_friction_ratio": d("0.150000"),
        "maximum_pass_settlement_delay_hours": d("24.000000"),
        "maximum_watch_settlement_delay_hours": d("72.000000"),
        "minimum_pass_gate_score": d("0.750000"),
        "minimum_watch_gate_score": d("0.450000"),
        "fee_drag_weight": d("0.200000"),
        "spread_width_weight": d("0.200000"),
        "available_depth_weight": d("0.250000"),
        "resolution_friction_weight": d("0.200000"),
        "settlement_timing_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchMarketFeeSpreadDepthResolutionGateConfig(**values)


def gate_input(
    private_event_ref: str = "private-alpha",
    *,
    observed_at: datetime = GENERATED_AT,
    fee_drag_ratio: Decimal = d("0.005000"),
    spread_width_ratio: Decimal = d("0.010000"),
    available_depth: Decimal = d("1500.000000"),
    resolution_friction_ratio: Decimal = d("0.020000"),
    settlement_delay_hours: Decimal = d("12.000000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketFeeSpreadDepthResolutionGateInput(
        private_event_ref=private_event_ref,
        observed_at=observed_at,
        fee_drag_ratio=fee_drag_ratio,
        spread_width_ratio=spread_width_ratio,
        available_depth=available_depth,
        resolution_friction_ratio=resolution_friction_ratio,
        settlement_delay_hours=settlement_delay_hours,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg: object | None = None) -> Any:
    module = api()
    return module.build_research_market_fee_spread_depth_resolution_gate_report(
        items,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_empty_report_blocks_without_sensitive_public_identifiers() -> None:
    module = api()
    built = report()

    assert module.FEE_SPREAD_DEPTH_RESOLUTION_GATE_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "FEE_SPREAD_DEPTH_RESOLUTION_GATE_STATUSES",
        "DEFAULT_RESEARCH_MARKET_FEE_SPREAD_DEPTH_RESOLUTION_GATE_REPORT_CONFIG_VERSION",
        "ResearchMarketFeeSpreadDepthResolutionGateConfig",
        "ResearchMarketFeeSpreadDepthResolutionGateInput",
        "ResearchMarketFeeSpreadDepthResolutionGateReasonCodeCount",
        "ResearchMarketFeeSpreadDepthResolutionGateReport",
        "ResearchMarketFeeSpreadDepthResolutionGateRow",
        "build_research_market_fee_spread_depth_resolution_gate_report",
        "research_market_fee_spread_depth_resolution_gate_report_payload",
        "validate_research_market_fee_spread_depth_resolution_gate_report_payload",
    )
    assert built.generated_at == GENERATED_AT
    assert built.status == "block"
    assert built.input_count == ZERO
    assert built.row_count == ZERO
    assert built.pass_count == ZERO
    assert built.watch_count == ZERO
    assert built.block_count == ZERO
    assert built.average_gate_score == ZERO
    assert built.reason_codes == ("gate_no_inputs",)
    assert built.reason_code_counts == (
        module.ResearchMarketFeeSpreadDepthResolutionGateReasonCodeCount(
            reason_code="gate_no_inputs",
            count=ONE,
        ),
    )
    assert built.rows == ()
    assert len(built.derived_validation_digest) == 64
    int(built.derived_validation_digest, 16)
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True


def test_scores_fee_spread_depth_resolution_and_settlement_gate_rows() -> None:
    built = report(
        gate_input(
            "block-private",
            fee_drag_ratio=d("0.040000"),
            spread_width_ratio=d("0.100000"),
            available_depth=d("100.000000"),
            resolution_friction_ratio=d("0.200000"),
            settlement_delay_hours=d("96.000000"),
            reason_codes=("manual_check",),
        ),
        gate_input(
            "watch-private",
            fee_drag_ratio=d("0.020000"),
            spread_width_ratio=d("0.050000"),
            available_depth=d("625.000000"),
            resolution_friction_ratio=d("0.100000"),
            settlement_delay_hours=d("48.000000"),
        ),
        gate_input("pass-private"),
    )

    assert built.input_count == d("3.000000")
    assert built.row_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.status == "block"
    assert built.high_fee_drag_count == d("2.000000")
    assert built.wide_spread_count == d("2.000000")
    assert built.thin_depth_count == d("2.000000")
    assert built.high_resolution_friction_count == d("2.000000")
    assert built.delayed_settlement_count == d("2.000000")
    assert built.average_gate_score == d("0.506667")
    assert built.min_available_depth == d("100.000000")
    assert built.max_fee_drag_ratio == d("0.040000")
    assert built.max_spread_width_ratio == d("0.100000")
    assert built.max_resolution_friction_ratio == d("0.200000")
    assert built.max_settlement_delay_hours == d("96.000000")

    block_row, watch_row, pass_row = built.rows
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    assert block_row.gate_score == ZERO
    assert block_row.reason_codes == (
        "gate_available_depth_block",
        "gate_fee_drag_block",
        "gate_resolution_friction_block",
        "gate_settlement_timing_block",
        "gate_spread_width_block",
        "gate_status_block",
        "input_manual_check",
    )
    assert watch_row.fee_drag_score == d("0.500000")
    assert watch_row.spread_width_score == d("0.600000")
    assert watch_row.available_depth_score == d("0.500000")
    assert watch_row.resolution_friction_score == d("0.500000")
    assert watch_row.settlement_timing_score == d("0.500000")
    assert watch_row.gate_score == d("0.520000")
    assert pass_row.gate_score == ONE
    assert pass_row.reason_codes == (
        "gate_available_depth_pass",
        "gate_fee_drag_pass",
        "gate_resolution_friction_pass",
        "gate_settlement_timing_pass",
        "gate_spread_width_pass",
        "gate_status_pass",
    )


def test_resolution_friction_and_settlement_boundaries_are_inclusive() -> None:
    boundary = report(
        gate_input(
            "pass-boundary",
            resolution_friction_ratio=d("0.050000"),
            settlement_delay_hours=d("24.000000"),
        ),
        gate_input(
            "watch-boundary",
            resolution_friction_ratio=d("0.150000"),
            settlement_delay_hours=d("72.000000"),
        ),
        gate_input(
            "block-boundary",
            resolution_friction_ratio=d("0.150001"),
            settlement_delay_hours=d("72.000001"),
        ),
    )

    assert tuple(row.status for row in boundary.rows) == ("block", "watch", "pass")
    block_row, watch_row, pass_row = boundary.rows
    assert "gate_resolution_friction_block" in block_row.reason_codes
    assert "gate_settlement_timing_block" in block_row.reason_codes
    assert "gate_resolution_friction_watch" in watch_row.reason_codes
    assert "gate_settlement_timing_watch" in watch_row.reason_codes
    assert "gate_resolution_friction_pass" in pass_row.reason_codes
    assert "gate_settlement_timing_pass" in pass_row.reason_codes


def test_public_payload_is_deterministic_decimal_string_serialized_and_digest_validated() -> None:
    module = api()
    first = report(
        gate_input("zulu-private", reason_codes=("zeta", "alpha")),
        gate_input("alpha-private"),
    )
    second = report(
        gate_input("alpha-private"),
        gate_input("zulu-private", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_market_fee_spread_depth_resolution_gate_report_payload(
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
    assert first_payload["rows"][0]["fee_drag_ratio"] == "0.005000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(isinstance(value, Decimal) for value in walk_payload_values(first_payload))
    assert not any(
        isinstance(value, (float, int)) and not isinstance(value, bool)
        for value in walk_payload_values(first_payload)
    )
    assert module.validate_research_market_fee_spread_depth_resolution_gate_report_payload(
        first_payload,
    ) == first_payload

    tampered = dict(first_payload)
    tampered["row_count"] = "999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_market_fee_spread_depth_resolution_gate_report_payload(
            tampered,
        )


def test_public_payload_excludes_private_refs_sensitive_text_and_decision_surfaces() -> None:
    module = api()
    built = report(
        gate_input(
            "raw-candidate-id-123/market-id-99/will-this-question-resolve/"
            "https://example.test/source?token=secret&wallet=abc",
        ),
    )
    payload = module.research_market_fee_spread_depth_resolution_gate_report_payload(built)
    rendered = json.dumps(payload, sort_keys=True).lower()

    for forbidden in (
        "raw-candidate-id-123",
        "market-id-99",
        "will-this-question-resolve",
        "https://example.test",
        "source?token",
        "secret",
        "wallet",
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
        "order",
        "trade",
        "live",
        "recommend",
        "position",
        "sizing",
        "execution",
    ):
        assert forbidden not in rendered

    unsafe_report = replace(built)
    object.__setattr__(unsafe_report, "reason_codes", ("gate_status_pass", "token_seen"))
    object.__setattr__(unsafe_report, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_market_fee_spread_depth_resolution_gate_report_payload(
            unsafe_report,
        )


def test_rejects_bad_numeric_datetime_flag_status_digest_and_custom_config() -> None:
    module = api()

    with pytest.raises(ValueError, match="maximum_pass_fee_drag_ratio"):
        config(maximum_pass_fee_drag_ratio=DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="maximum_watch_spread_width_ratio"):
        config(maximum_watch_spread_width_ratio=0.08)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="maximum_pass_fee_drag_ratio"):
        config(maximum_pass_fee_drag_ratio=d("0.040000"))
    with pytest.raises(ValueError, match="minimum_pass_available_depth"):
        config(minimum_pass_available_depth=d("100.000000"))
    with pytest.raises(ValueError, match="maximum_pass_resolution_friction_ratio"):
        config(maximum_pass_resolution_friction_ratio=d("0.200000"))
    with pytest.raises(ValueError, match="maximum_pass_settlement_delay_hours"):
        config(maximum_pass_settlement_delay_hours=d("80.000000"))
    with pytest.raises(ValueError, match="weights must sum"):
        config(fee_drag_weight=d("0.300000"))
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_fee_spread_depth_resolution_gate_report(
            (gate_input(),),
            config=config(),
            generated_at=datetime(2026, 7, 8, 16, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_fee_spread_depth_resolution_gate_report(
            (gate_input(),),
            config=config(),
            generated_at=DatetimeSubclass(2026, 7, 8, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        gate_input(observed_at=datetime(2026, 7, 8, 16, 0))
    with pytest.raises(ValueError, match="fee_drag_ratio"):
        gate_input(fee_drag_ratio=d("NaN"))
    with pytest.raises(ValueError, match="spread_width_ratio"):
        gate_input(spread_width_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="available_depth"):
        gate_input(available_depth=-d("1.000000"))
    with pytest.raises(ValueError, match="resolution_friction_ratio"):
        gate_input(resolution_friction_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="settlement_delay_hours"):
        gate_input(settlement_delay_hours=DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        gate_input(reason_codes=("token_seen",))
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        report(gate_input(readonly=False))

    built = report(gate_input())
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="blocked")
    with pytest.raises(ValueError, match="gate_score"):
        replace(built.rows[0], gate_score=d("1.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(built, status="watch")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="report"):
        module.research_market_fee_spread_depth_resolution_gate_report_payload(object())

    unsafe_payload = dict(
        module.research_market_fee_spread_depth_resolution_gate_report_payload(built),
    )
    unsafe_payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.validate_research_market_fee_spread_depth_resolution_gate_report_payload(
            unsafe_payload,
        )

    custom_weight_report = report(
        gate_input(
            "custom-weight-row",
            fee_drag_ratio=d("0.020000"),
            spread_width_ratio=d("0.050000"),
            available_depth=d("625.000000"),
            resolution_friction_ratio=d("0.100000"),
            settlement_delay_hours=d("48.000000"),
        ),
        cfg=config(
            fee_drag_weight=d("0.150000"),
            spread_width_weight=d("0.400000"),
            available_depth_weight=d("0.150000"),
            resolution_friction_weight=d("0.150000"),
            settlement_timing_weight=d("0.150000"),
        ),
    )
    assert custom_weight_report.rows[0].gate_score == d("0.540000")


def test_public_objects_are_frozen_dataclasses_with_decimal_numeric_fields() -> None:
    module = api()
    built = report(gate_input())

    for item in (config(), gate_input(), built, *built.reason_code_counts, *built.rows):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True

    with pytest.raises(FrozenInstanceError):
        built.row_count = d("2.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].gate_score = ZERO  # type: ignore[misc]

    public_classes = (
        module.ResearchMarketFeeSpreadDepthResolutionGateConfig,
        module.ResearchMarketFeeSpreadDepthResolutionGateInput,
        module.ResearchMarketFeeSpreadDepthResolutionGateRow,
        module.ResearchMarketFeeSpreadDepthResolutionGateReasonCodeCount,
        module.ResearchMarketFeeSpreadDepthResolutionGateReport,
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


def test_owned_module_has_no_storage_network_or_decision_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_fee_spread_depth_resolution_gate_report.py"
    )
    text = module_path.read_text(encoding="utf-8").lower()
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
        assert forbidden not in text

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


def walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
