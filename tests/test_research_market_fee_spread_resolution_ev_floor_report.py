from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_market_fee_spread_resolution_ev_floor_report"
)
GENERATED_AT = datetime(2026, 7, 9, 14, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"{MODULE_NAME} must exist")
        raise


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_FEE_SPREAD_RESOLUTION_EV_FLOOR_REPORT_CONFIG_VERSION
        ),
        "pass_ev_floor_threshold": d("0.030000"),
        "watch_ev_floor_threshold": d("0.005000"),
        "block_total_drag_threshold": d("0.120000"),
    }
    values.update(overrides)
    return module.ResearchMarketFeeSpreadResolutionEvFloorConfig(**values)


def floor_input(
    private_research_ref: str = "private-alpha",
    *,
    observed_at: datetime = GENERATED_AT,
    gross_expected_value_edge: Decimal = d("0.070000"),
    fee_drag_ratio: Decimal = d("0.010000"),
    spread_width_ratio: Decimal = d("0.020000"),
    resolution_friction_ratio: Decimal = d("0.008000"),
    resolution_uncertainty_ratio: Decimal = d("0.007000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketFeeSpreadResolutionEvFloorInput(
        private_research_ref=private_research_ref,
        observed_at=observed_at,
        gross_expected_value_edge=gross_expected_value_edge,
        fee_drag_ratio=fee_drag_ratio,
        spread_width_ratio=spread_width_ratio,
        resolution_friction_ratio=resolution_friction_ratio,
        resolution_uncertainty_ratio=resolution_uncertainty_ratio,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg: object | None = None) -> Any:
    module = api()
    return module.build_research_market_fee_spread_resolution_ev_floor_report(
        items,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def walk_json(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for key, item in value.items():
            values.append(key)
            values.extend(walk_json(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_json(item))
    else:
        values.append(value)
    return tuple(values)


def test_empty_report_blocks_without_public_rows_or_sensitive_refs() -> None:
    module = api()
    built = report()

    assert module.EV_FLOOR_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "EV_FLOOR_STATUSES",
        "DEFAULT_RESEARCH_MARKET_FEE_SPREAD_RESOLUTION_EV_FLOOR_REPORT_CONFIG_VERSION",
        "ResearchMarketFeeSpreadResolutionEvFloorConfig",
        "ResearchMarketFeeSpreadResolutionEvFloorInput",
        "ResearchMarketFeeSpreadResolutionEvFloorReasonCodeCount",
        "ResearchMarketFeeSpreadResolutionEvFloorReport",
        "ResearchMarketFeeSpreadResolutionEvFloorRow",
        "build_research_market_fee_spread_resolution_ev_floor_report",
        "research_market_fee_spread_resolution_ev_floor_report_payload",
        "validate_research_market_fee_spread_resolution_ev_floor_report_payload",
    )
    assert built.generated_at == GENERATED_AT
    assert built.status == "block"
    assert built.input_count == ZERO
    assert built.row_count == ZERO
    assert built.pass_count == ZERO
    assert built.watch_count == ZERO
    assert built.block_count == ZERO
    assert built.average_ev_floor == ZERO
    assert built.top_ev_floor == ZERO
    assert built.min_ev_floor == ZERO
    assert built.max_total_drag == ZERO
    assert built.reason_codes == ("ev_floor_no_inputs",)
    assert built.reason_code_counts == (
        module.ResearchMarketFeeSpreadResolutionEvFloorReasonCodeCount(
            reason_code="ev_floor_no_inputs",
            count=ONE,
        ),
    )
    assert built.rows == ()
    assert len(built.derived_validation_digest) == 64
    int(built.derived_validation_digest, 16)
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True


def test_computes_fee_spread_resolution_ev_floor_and_statuses() -> None:
    built = report(
        floor_input(
            "block-private",
            gross_expected_value_edge=d("0.020000"),
            fee_drag_ratio=d("0.060000"),
            spread_width_ratio=d("0.060000"),
            resolution_friction_ratio=d("0.040000"),
            resolution_uncertainty_ratio=d("0.020000"),
            reason_codes=("manual_review",),
        ),
        floor_input(
            "watch-private",
            gross_expected_value_edge=d("0.050000"),
            fee_drag_ratio=d("0.010000"),
            spread_width_ratio=d("0.040000"),
            resolution_friction_ratio=d("0.006000"),
            resolution_uncertainty_ratio=d("0.004000"),
        ),
        floor_input("pass-private"),
    )

    assert built.input_count == d("3.000000")
    assert built.row_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.status == "block"
    assert built.average_ev_floor == d("-0.028333")
    assert built.top_ev_floor == d("0.035000")
    assert built.min_ev_floor == d("-0.130000")
    assert built.max_total_drag == d("0.150000")

    block_row, watch_row, pass_row = built.rows
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    assert tuple(row.public_row_ref for row in built.rows) == (
        "ev-floor-row-000001",
        "ev-floor-row-000003",
        "ev-floor-row-000002",
    )
    assert block_row.spread_cost_ratio == d("0.030000")
    assert block_row.total_fee_spread_resolution_drag == d("0.150000")
    assert block_row.ev_floor == d("-0.130000")
    assert block_row.reason_codes == (
        "ev_floor_below_watch_floor",
        "ev_floor_fee_drag_applied",
        "ev_floor_non_positive_floor",
        "ev_floor_resolution_friction_applied",
        "ev_floor_resolution_uncertainty_applied",
        "ev_floor_spread_drag_applied",
        "ev_floor_status_block",
        "ev_floor_total_drag_block",
        "input_manual_review",
    )
    assert watch_row.ev_floor == d("0.010000")
    assert watch_row.reason_codes[-1] == "ev_floor_status_watch"
    assert pass_row.ev_floor == d("0.035000")
    assert pass_row.reason_codes == (
        "ev_floor_fee_drag_applied",
        "ev_floor_positive_floor",
        "ev_floor_resolution_friction_applied",
        "ev_floor_resolution_uncertainty_applied",
        "ev_floor_spread_drag_applied",
        "ev_floor_status_pass",
    )


def test_threshold_boundaries_are_inclusive_and_floor_driven() -> None:
    boundary = report(
        floor_input(
            "pass-boundary",
            gross_expected_value_edge=d("0.060000"),
            fee_drag_ratio=d("0.010000"),
            spread_width_ratio=d("0.020000"),
            resolution_friction_ratio=d("0.005000"),
            resolution_uncertainty_ratio=d("0.005000"),
        ),
        floor_input(
            "watch-boundary",
            gross_expected_value_edge=d("0.030000"),
            fee_drag_ratio=d("0.010000"),
            spread_width_ratio=d("0.020000"),
            resolution_friction_ratio=d("0.003000"),
            resolution_uncertainty_ratio=d("0.002000"),
        ),
        floor_input(
            "block-boundary",
            gross_expected_value_edge=d("0.030000"),
            fee_drag_ratio=d("0.010000"),
            spread_width_ratio=d("0.020000"),
            resolution_friction_ratio=d("0.003001"),
            resolution_uncertainty_ratio=d("0.002000"),
        ),
    )

    assert tuple(row.status for row in boundary.rows) == ("block", "watch", "pass")
    block_row, watch_row, pass_row = boundary.rows
    assert block_row.ev_floor == d("0.004999")
    assert "ev_floor_below_watch_floor" in block_row.reason_codes
    assert watch_row.ev_floor == d("0.005000")
    assert "ev_floor_status_watch" in watch_row.reason_codes
    assert pass_row.ev_floor == d("0.030000")
    assert "ev_floor_status_pass" in pass_row.reason_codes


def test_public_payload_is_deterministic_decimal_string_serialized_and_digest_validated() -> None:
    module = api()
    raw_ref = (
        "raw candidate id market id slug question "
        "https://example.invalid/source?token=secret wallet order trade "
        "dsn=postgres table=markets"
    )
    first = report(
        floor_input("zulu-private", reason_codes=("zeta", "alpha")),
        floor_input(raw_ref),
    )
    second = report(
        floor_input(raw_ref),
        floor_input("zulu-private", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_market_fee_spread_resolution_ev_floor_report_payload(
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
    assert first_payload["rows"][0]["ev_floor"] == "0.035000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(isinstance(value, Decimal) for value in walk_json(first_payload))
    assert not any(
        isinstance(value, (float, int)) and not isinstance(value, bool)
        for value in walk_json(first_payload)
    )
    assert module.validate_research_market_fee_spread_resolution_ev_floor_report_payload(
        first_payload,
    ) == first_payload

    rendered = json.dumps(first_payload, sort_keys=True).lower()
    for forbidden in (
        raw_ref,
        "raw candidate id",
        "market id",
        "slug",
        "question",
        "https://",
        "source?",
        "token=secret",
        "wallet",
        "order",
        "trade",
        "dsn=",
        "table=markets",
        "private_research_ref",
        "candidate_id",
        "market_id",
        "market_slug",
        "source_url",
        "source_text",
    ):
        assert forbidden not in rendered

    tampered = dict(first_payload)
    tampered["row_count"] = "999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_market_fee_spread_resolution_ev_floor_report_payload(
            tampered,
        )


def test_rejects_bad_numeric_datetime_flags_status_digest_and_config() -> None:
    module = api()

    with pytest.raises(ValueError, match="pass_ev_floor_threshold"):
        config(pass_ev_floor_threshold=DecimalSubclass("0.030000"))
    with pytest.raises(ValueError, match="watch_ev_floor_threshold"):
        config(watch_ev_floor_threshold=0.005)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="pass_ev_floor_threshold"):
        config(
            pass_ev_floor_threshold=d("0.004000"),
            watch_ev_floor_threshold=d("0.005000"),
        )
    with pytest.raises(ValueError, match="block_total_drag_threshold"):
        config(block_total_drag_threshold=d("0.000000"))
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_fee_spread_resolution_ev_floor_report(
            (floor_input(),),
            config=config(),
            generated_at=datetime(2026, 7, 9, 14, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_fee_spread_resolution_ev_floor_report(
            (floor_input(),),
            config=config(),
            generated_at=DatetimeSubclass(2026, 7, 9, 14, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        floor_input(observed_at=datetime(2026, 7, 9, 14, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report(floor_input(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="gross_expected_value_edge"):
        floor_input(gross_expected_value_edge=d("NaN"))
    with pytest.raises(ValueError, match="fee_drag_ratio"):
        floor_input(fee_drag_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="spread_width_ratio"):
        floor_input(spread_width_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="resolution_friction_ratio"):
        floor_input(resolution_friction_ratio=-d("0.010000"))
    with pytest.raises(ValueError, match="resolution_uncertainty_ratio"):
        floor_input(resolution_uncertainty_ratio=DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="reason_codes"):
        floor_input(reason_codes=("token_seen",))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        report(floor_input(readonly=False))

    built = report(floor_input())
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="blocked")
    with pytest.raises(ValueError, match="ev_floor"):
        replace(built.rows[0], ev_floor=d("0.999999"))
    with pytest.raises(ValueError, match="status"):
        replace(built, status="watch")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="report"):
        module.research_market_fee_spread_resolution_ev_floor_report_payload(object())

    unsafe_payload = dict(
        module.research_market_fee_spread_resolution_ev_floor_report_payload(built),
    )
    unsafe_payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.validate_research_market_fee_spread_resolution_ev_floor_report_payload(
            unsafe_payload,
        )


def test_public_objects_are_frozen_dataclasses_with_decimal_numeric_fields() -> None:
    module = api()
    built = report(floor_input())

    for item in (config(), floor_input(), built, *built.reason_code_counts, *built.rows):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True

    with pytest.raises(FrozenInstanceError):
        built.row_count = d("2.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].ev_floor = ZERO  # type: ignore[misc]

    public_classes = (
        module.ResearchMarketFeeSpreadResolutionEvFloorConfig,
        module.ResearchMarketFeeSpreadResolutionEvFloorInput,
        module.ResearchMarketFeeSpreadResolutionEvFloorRow,
        module.ResearchMarketFeeSpreadResolutionEvFloorReasonCodeCount,
        module.ResearchMarketFeeSpreadResolutionEvFloorReport,
    )
    for klass in public_classes:
        assert klass.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(klass)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        for field in fields(klass):
            if field.name in {
                "paper_only",
                "report_only",
                "readonly",
                "private_research_ref",
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
        / "research_market_fee_spread_resolution_ev_floor_report.py"
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
