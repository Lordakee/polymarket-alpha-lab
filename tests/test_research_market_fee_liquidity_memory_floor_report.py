from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import ROUND_DOWN, ROUND_UP, Decimal, localcontext
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_market_fee_liquidity_memory_floor_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_fee_liquidity_memory_floor_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "watch_fee_rate": d("0.010000"),
        "block_fee_rate": d("0.020000"),
        "max_spread_rate": d("0.030000"),
        "min_memory_sample_count": d("3"),
    }
    values.update(overrides)
    return module.ResearchMarketFeeLiquidityMemoryFloorReportConfig(**values)


def item(**overrides: object):
    module = api()
    values = {
        "candidate_key": "candidate-alpha",
        "market_key": "market-alpha",
        "raw_reference": (
            "https://source.example/fee-liquidity?token=super-token "
            "postgresql://private.example/raw_text fees_table"
        ),
        "observed_at": GENERATED_AT - timedelta(minutes=5),
        "fee_rate": d("0.004000"),
        "liquidity_depth": d("1200.000000"),
        "liquidity_memory_floor": d("1000.000000"),
        "spread_rate": d("0.010000"),
        "memory_sample_count": d("8"),
    }
    values.update(overrides)
    return module.ResearchMarketFeeLiquidityMemoryFloorInput(**values)


def build_report(*rows: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_fee_liquidity_memory_floor_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def payload_digest(payload: dict[str, object]) -> str:
    comparable = dict(payload)
    comparable.pop("derived_validation_digest", None)
    canonical = json.dumps(
        comparable,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def resign_payload(payload: dict[str, object]) -> dict[str, object]:
    payload["derived_validation_digest"] = payload_digest(payload)
    return payload


def assert_no_float_or_int_values(value: Any) -> None:
    if isinstance(value, float) or type(value) is int:
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_float_or_int_values(item_value)
    if isinstance(value, (list, tuple)):
        for item_value in value:
            assert_no_float_or_int_values(item_value)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item_value in value.values():
            assert_public_numeric_values_are_decimal(item_value)
        return
    if isinstance(value, (list, tuple)):
        for item_value in value:
            assert_public_numeric_values_are_decimal(item_value)


def test_report_scores_fee_liquidity_memory_floor_rows_and_summary_status() -> None:
    module = api()
    report = build_report(
        item(candidate_key="candidate-pass", market_key="market-pass"),
        item(
            candidate_key="candidate-watch",
            market_key="market-watch",
            fee_rate=d("0.012000"),
            memory_sample_count=d("2"),
        ),
        item(
            candidate_key="candidate-block",
            market_key="market-block",
            fee_rate=d("0.025000"),
            liquidity_depth=d("600.000000"),
            spread_rate=d("0.040000"),
        ),
    )

    assert module.STATUSES == ("pass", "watch", "block")
    assert report.report_status == "block"
    assert report.item_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.average_fee_rate == d("0.013667")
    assert report.average_spread_rate == d("0.020000")
    assert report.minimum_liquidity_floor_coverage_ratio == d("0.600000")
    assert tuple(sorted(row.row_status for row in report.rows)) == (
        "block",
        "pass",
        "watch",
    )
    assert report.reason_codes == (
        "cost_floor_pass",
        "fee_above_memory_floor",
        "fee_near_memory_floor",
        "liquidity_below_memory_floor",
        "spread_above_ceiling",
        "thin_memory_floor",
    )


def test_public_payload_is_deterministic_redacted_and_digest_validated() -> None:
    module = api()
    rows = (
        item(candidate_key="candidate-secret-alpha", market_key="market-secret-alpha"),
        item(
            candidate_key="candidate-secret-beta",
            market_key="market-secret-beta",
            fee_rate=d("0.012000"),
            raw_reference=(
                "raw source text https://source.example/private "
                "postgresql://dsn.example fees_table token=super-token"
            ),
        ),
    )

    first = module.research_market_fee_liquidity_memory_floor_report_payload(
        build_report(*rows),
    )
    second = module.research_market_fee_liquidity_memory_floor_report_payload(
        build_report(*reversed(rows), generated_at=GENERATED_AT.astimezone(UTC)),
    )

    assert first == second
    assert first["paper_only"] is True
    assert first["report_only"] is True
    assert first["readonly"] is True
    assert isinstance(first["derived_validation_digest"], str)
    assert len(first["derived_validation_digest"]) == 64
    assert_no_float_or_int_values(first)

    public_blob = json.dumps(first, sort_keys=True).lower()
    for forbidden in (
        "candidate-secret-alpha",
        "candidate-secret-beta",
        "market-secret-alpha",
        "market-secret-beta",
        "source.example",
        "postgresql://",
        "raw source text",
        "fees_table",
        "super-token",
        "candidate",
        "market",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
    ):
        assert forbidden not in public_blob

    tampered = dict(first)
    tampered["item_count"] = "9"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_fee_liquidity_memory_floor_report_payload(tampered)

    tampered_digest = dict(first)
    tampered_digest["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_fee_liquidity_memory_floor_report_payload(tampered_digest)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    sample_config = config()
    sample_item = item()
    sample_report = build_report(sample_item)
    sample_row = sample_report.rows[0]
    sample_reason_count = sample_report.reason_code_counts[0]

    for value in (sample_config, sample_item, sample_row, sample_reason_count, sample_report):
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        assert_public_numeric_values_are_decimal(value)

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        item(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build_report(item(readonly=False))


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        ("fee_rate", 0, "fee_rate must be exactly Decimal"),
        ("spread_rate", _DecimalSubclass("0.010000"), "spread_rate must be exactly Decimal"),
        ("liquidity_depth", d("-1.000000"), "liquidity_depth must be nonnegative"),
        ("liquidity_memory_floor", d("0.000000"), "liquidity_memory_floor must be positive"),
        ("memory_sample_count", d("2.5"), "memory_sample_count must be a whole Decimal"),
        ("fee_rate", Decimal("NaN"), "fee_rate must be finite"),
    ),
)
def test_validation_rejects_non_decimal_ranges_and_bad_counts(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        item(**{field_name: bad_value})


def test_report_and_payload_revalidate_tampered_public_objects() -> None:
    module = api()
    report = build_report(item())

    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values["derived_validation_digest"] = "f" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.ResearchMarketFeeLiquidityMemoryFloorReport(**values)

    object.__setattr__(report.rows[0], "row_status", "block")
    with pytest.raises(ValueError, match="row_status"):
        module.research_market_fee_liquidity_memory_floor_report_payload(report)


def test_payload_rejects_recomputed_dict_tampering() -> None:
    module = api()
    payload = module.research_market_fee_liquidity_memory_floor_report_payload(
        build_report(item()),
    )

    flag_tampered = resign_payload(dict(payload, paper_only=False))
    with pytest.raises(ValueError, match="paper_only"):
        module.research_market_fee_liquidity_memory_floor_report_payload(flag_tampered)

    numeric_tampered = resign_payload(dict(payload, item_count=1))
    with pytest.raises(ValueError, match="item_count"):
        module.research_market_fee_liquidity_memory_floor_report_payload(
            numeric_tampered,
        )

    extra_field_tampered = dict(payload)
    extra_field_tampered["safe_extra"] = "safe"
    resign_payload(extra_field_tampered)
    with pytest.raises(ValueError, match="payload keys"):
        module.research_market_fee_liquidity_memory_floor_report_payload(
            extra_field_tampered,
        )


def test_payload_rejects_noncanonical_decimal_strings() -> None:
    module = api()
    payload = module.research_market_fee_liquidity_memory_floor_report_payload(
        build_report(item()),
    )

    for field_name, bad_value in (
        ("item_count", "1.0"),
        ("average_fee_rate", "0.004"),
    ):
        tampered = resign_payload(dict(payload, **{field_name: bad_value}))
        with pytest.raises(ValueError, match=field_name):
            module.research_market_fee_liquidity_memory_floor_report_payload(tampered)

    row_tampered = dict(payload)
    row_tampered["rows"] = [
        dict(payload["rows"][0], memory_sample_count="8.0"),  # type: ignore[index]
    ]
    resign_payload(row_tampered)
    with pytest.raises(ValueError, match="memory_sample_count"):
        module.research_market_fee_liquidity_memory_floor_report_payload(row_tampered)

    empty_payload = module.research_market_fee_liquidity_memory_floor_report_payload(
        build_report(),
    )
    negative_zero = resign_payload(
        dict(empty_payload, average_fee_rate="-0.000000"),
    )
    with pytest.raises(ValueError, match="average_fee_rate"):
        module.research_market_fee_liquidity_memory_floor_report_payload(negative_zero)


def test_reducer_is_independent_of_ambient_decimal_context() -> None:
    module = api()
    sample = item(
        fee_rate=d("0.0000005"),
        liquidity_depth=d("1.000000"),
        liquidity_memory_floor=d("3.000000"),
        spread_rate=d("0.0000005"),
    )

    with localcontext() as context:
        context.prec = 12
        context.rounding = ROUND_DOWN
        first = module.research_market_fee_liquidity_memory_floor_report_payload(
            build_report(sample),
        )

    with localcontext() as context:
        context.prec = 48
        context.rounding = ROUND_UP
        second = module.research_market_fee_liquidity_memory_floor_report_payload(
            build_report(sample),
        )

    assert first == second
    assert first["rows"][0]["fee_rate"] == "0.000000"  # type: ignore[index]
    assert first["rows"][0]["liquidity_floor_coverage_ratio"] == "0.333333"  # type: ignore[index]


@pytest.mark.parametrize(
    "class_name",
    (
        "ResearchMarketFeeLiquidityMemoryFloorReportConfig",
        "ResearchMarketFeeLiquidityMemoryFloorInput",
        "ResearchMarketFeeLiquidityMemoryFloorRow",
        "ResearchMarketFeeLiquidityMemoryFloorReasonCodeCount",
        "ResearchMarketFeeLiquidityMemoryFloorReport",
    ),
)
def test_public_dataclasses_reject_subclassing(class_name: str) -> None:
    module = api()
    base = getattr(module, class_name)

    with pytest.raises(TypeError, match="does not support subclassing"):
        type(f"Unsafe{class_name}", (base,), {})


def test_rows_require_hex_digest_tokens_and_unique_identities() -> None:
    module = api()
    report = build_report(item())
    original_row = report.rows[0]
    row_values = {
        field.name: getattr(original_row, field.name)
        for field in fields(original_row)
    }
    row_values["identity_digest"] = "sha256:" + ("z" * 16)

    with pytest.raises(ValueError, match="identity_digest"):
        module.ResearchMarketFeeLiquidityMemoryFloorRow(**row_values)

    row_values["identity_digest"] = original_row.identity_digest
    row_values["row_status"] = "block"
    row_values["reason_codes"] = (
        module.FEE_NEAR_REASON,
        module.FEE_ABOVE_REASON,
    )
    with pytest.raises(ValueError, match="reason_codes"):
        module.ResearchMarketFeeLiquidityMemoryFloorRow(**row_values)

    row_values["reason_codes"] = (
        module.PASS_REASON,
        module.FEE_ABOVE_REASON,
    )
    with pytest.raises(ValueError, match="pass"):
        module.ResearchMarketFeeLiquidityMemoryFloorRow(**row_values)

    with pytest.raises(ValueError, match="identity_digest"):
        build_report(
            item(raw_reference="reference-one"),
            item(raw_reference="reference-two"),
        )


def test_report_rejects_recomputed_reason_code_count_tampering() -> None:
    module = api()
    report = build_report(item())
    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values["reason_code_counts"] = (
        module.ResearchMarketFeeLiquidityMemoryFloorReasonCodeCount(
            reason_code="cost_floor_pass",
            count=d("2"),
            item_ratio=d("2.000000"),
        ),
    )
    values["derived_validation_digest"] = module._payload_digest(
        module._payload_from_mapping(values),
    )

    with pytest.raises(ValueError, match="reason_code_counts"):
        module.ResearchMarketFeeLiquidityMemoryFloorReport(**values)


def test_module_scope_has_no_database_network_wallet_order_or_advice_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    string_constants: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            string_constants.append(node.value)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "database",
        "http",
        "network",
        "order",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "persist",
        "rollback",
        "send",
        "write",
    }
    forbidden_public_surface_fragments = (
        "auth",
        "database",
        "network",
        "wallet",
        "order",
        "live trading",
        "sizing",
        "recommendation",
    )

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert not any(
        fragment in constant.lower()
        for constant in string_constants
        for fragment in forbidden_public_surface_fragments
    )
