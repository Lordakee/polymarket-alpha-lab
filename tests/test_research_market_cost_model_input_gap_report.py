from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_market_cost_model_input_gap_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    try:
        return importlib.import_module(
            "polymarket_alpha_lab.research_market_cost_model_input_gap_report",
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"missing report module: {exc.name}")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-market-cost-model-input-gap-report-v0",
        "watch_component_gap_score": d("0.300000"),
        "block_component_gap_score": d("0.750000"),
        "watch_aggregate_gap_score": d("0.250000"),
        "block_aggregate_gap_score": d("0.600000"),
    }
    values.update(overrides)
    return module.ResearchMarketCostModelInputGapConfig(**values)


def observation(**overrides: object):
    module = api()
    values = {
        "cost_model_bucket": "bucket_alpha",
        "observed_at": GENERATED_AT - timedelta(minutes=5),
        "fee_missing_score": d("0.000000"),
        "fee_stale_score": d("0.050000"),
        "spread_missing_score": d("0.000000"),
        "spread_stale_score": d("0.020000"),
        "slippage_missing_score": d("0.000000"),
        "slippage_stale_score": d("0.030000"),
        "settlement_friction_missing_score": d("0.000000"),
        "settlement_friction_stale_score": d("0.040000"),
        "quote_depth_missing_score": d("0.000000"),
        "quote_depth_stale_score": d("0.010000"),
        "reason_codes": (),
    }
    values.update(overrides)
    return module.ResearchMarketCostModelInputGapObservation(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_cost_model_input_gap_report(
        items,
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


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is Decimal:
        return
    if isinstance(value, datetime):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == "payload":
                continue
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def assert_public_payload_has_no_forbidden_surface(value: object) -> None:
    forbidden = (
        "raw",
        "candidate_id",
        "market_id",
        "condition_id",
        "market_slug",
        "slug",
        "question",
        "http://",
        "https://",
        "url",
        "source_text",
        "source text",
        "dsn",
        "table_name",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "trading",
        "private_key",
        "buy",
        "sell",
        "recommend",
        "sizing",
        "bucket_alpha",
        "bucket_beta",
        "bucket_gamma",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lower_key = str(key).lower()
            assert not any(fragment in lower_key for fragment in forbidden), lower_key
            assert_public_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, str):
        lower_value = value.lower()
        assert not any(fragment in lower_value for fragment in forbidden), lower_value


def test_public_api_declares_readonly_report_contract() -> None:
    module = api()

    assert module.DEFAULT_RESEARCH_MARKET_COST_MODEL_INPUT_GAP_CONFIG_VERSION == (
        "research-market-cost-model-input-gap-report-v0"
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_MARKET_COST_MODEL_INPUT_GAP_CONFIG_VERSION",
        "ResearchMarketCostModelInputGapConfig",
        "ResearchMarketCostModelInputGapObservation",
        "ResearchMarketCostModelInputGapComponentSummary",
        "ResearchMarketCostModelInputGapRow",
        "ResearchMarketCostModelInputGapDigest",
        "ResearchMarketCostModelInputGapReport",
        "build_research_market_cost_model_input_gap_report",
        "research_market_cost_model_input_gap_report_payload",
        "research_market_cost_model_input_gap_digest_payload",
    )

    for cls_name in (
        "ResearchMarketCostModelInputGapConfig",
        "ResearchMarketCostModelInputGapObservation",
        "ResearchMarketCostModelInputGapComponentSummary",
        "ResearchMarketCostModelInputGapRow",
        "ResearchMarketCostModelInputGapDigest",
        "ResearchMarketCostModelInputGapReport",
    ):
        cls = getattr(module, cls_name)
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    field_defaults = {
        field.name: field.default
        for field in fields(module.ResearchMarketCostModelInputGapConfig)
    }
    assert field_defaults["paper_only"] is True
    assert field_defaults["report_only"] is True
    assert field_defaults["readonly"] is True


def test_builds_pass_watch_and_block_rows_from_sanitized_gap_components() -> None:
    report = build_report(
        observation(cost_model_bucket="bucket_alpha"),
        observation(
            cost_model_bucket="bucket_beta",
            fee_missing_score=d("0.350000"),
            fee_stale_score=d("0.100000"),
            spread_missing_score=d("0.100000"),
            spread_stale_score=d("0.350000"),
            slippage_missing_score=d("0.200000"),
            slippage_stale_score=d("0.150000"),
            settlement_friction_missing_score=d("0.250000"),
            settlement_friction_stale_score=d("0.350000"),
            quote_depth_missing_score=d("0.200000"),
            quote_depth_stale_score=d("0.350000"),
        ),
        observation(
            cost_model_bucket="bucket_gamma",
            fee_missing_score=d("0.800000"),
            fee_stale_score=d("0.300000"),
            spread_missing_score=d("0.100000"),
            spread_stale_score=d("0.800000"),
            slippage_missing_score=d("0.750000"),
            slippage_stale_score=d("0.100000"),
            settlement_friction_missing_score=d("0.600000"),
            settlement_friction_stale_score=d("0.850000"),
            quote_depth_missing_score=d("0.900000"),
            quote_depth_stale_score=d("0.200000"),
        ),
    )

    assert is_dataclass(report)
    assert report.status == "block"
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_aggregate_gap_score == d("0.390000")
    assert report.max_aggregate_gap_score == d("0.820000")
    assert report.reason_codes == (
        "cost_model_input_gap_report_block_rows",
        "cost_model_input_gap_report_watch_rows",
    )

    assert tuple(row.cost_model_bucket for row in report.rows) == (
        "bucket_alpha",
        "bucket_beta",
        "bucket_gamma",
    )
    assert tuple(row.status for row in report.rows) == ("pass", "watch", "block")
    assert report.rows[0].fee_gap_score == d("0.050000")
    assert report.rows[0].aggregate_gap_score == d("0.030000")
    assert report.rows[0].reason_codes == ("cost_model_input_gap_pass",)
    assert report.rows[1].aggregate_gap_score == d("0.320000")
    assert report.rows[1].reason_codes == (
        "fee_missing_gap_watch",
        "spread_stale_gap_watch",
        "settlement_friction_stale_gap_watch",
        "quote_depth_stale_gap_watch",
        "aggregate_gap_watch",
        "cost_model_input_gap_watch",
    )
    assert report.rows[2].aggregate_gap_score == d("0.820000")
    assert report.rows[2].reason_codes == (
        "fee_missing_gap_block",
        "spread_stale_gap_block",
        "slippage_missing_gap_block",
        "settlement_friction_stale_gap_block",
        "quote_depth_missing_gap_block",
        "aggregate_gap_block",
        "cost_model_input_gap_block",
    )

    summaries = {summary.component: summary for summary in report.component_summaries}
    assert tuple(summaries) == (
        "fee",
        "spread",
        "slippage",
        "settlement_friction",
        "quote_depth",
    )
    assert summaries["fee"].missing_gap_count == d("2.000000")
    assert summaries["fee"].stale_gap_count == d("1.000000")
    assert summaries["fee"].max_gap_score == d("0.800000")
    assert summaries["fee"].status == "block"
    assert summaries["quote_depth"].missing_gap_count == d("1.000000")
    assert summaries["quote_depth"].stale_gap_count == d("1.000000")
    assert summaries["quote_depth"].status == "block"


def test_empty_report_blocks_and_statuses_are_public_only() -> None:
    module = api()
    empty = build_report()

    assert empty.status == "block"
    assert empty.input_count == d("0.000000")
    assert empty.rows == ()
    assert empty.component_summaries == ()
    assert empty.reason_codes == ("no_cost_model_input_gap_observations",)

    watch = build_report(
        observation(cost_model_bucket="bucket_watch", fee_stale_score=d("0.300000")),
    )
    assert watch.status == "watch"
    assert watch.rows[0].reason_codes == (
        "fee_stale_gap_watch",
        "cost_model_input_gap_watch",
    )

    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(watch.rows[0], status="blocked")
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(watch.digest, status="ready")
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        module.ResearchMarketCostModelInputGapReport(
            **{**watch.__dict__, "status": "review"},
        )


@pytest.mark.parametrize(
    ("factory", "message"),
    (
        (
            lambda: observation(fee_missing_score=1),
            "fee_missing_score must be exactly Decimal",
        ),
        (
            lambda: observation(spread_stale_score=0.25),
            "spread_stale_score must be exactly Decimal",
        ),
        (
            lambda: observation(slippage_missing_score=_DecimalSubclass("0.25")),
            "slippage_missing_score must be exactly Decimal",
        ),
        (
            lambda: observation(quote_depth_stale_score=d("0.1234567")),
            "quote_depth_stale_score must use six decimal places or fewer",
        ),
        (
            lambda: observation(settlement_friction_missing_score=d("-0.100000")),
            "settlement_friction_missing_score must be between 0.000000 and 1.000000",
        ),
        (
            lambda: config(
                watch_component_gap_score=d("0.800000"),
                block_component_gap_score=d("0.700000"),
            ),
            "watch_component_gap_score must not exceed block_component_gap_score",
        ),
        (
            lambda: build_report(
                observation(),
                generated_at=datetime(2026, 7, 8, 12, 0),
            ),
            "generated_at must be timezone-aware",
        ),
    ),
)
def test_decimal_and_type_validation_rejects_public_numeric_shortcuts(
    factory: Any,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        factory()


def test_rejects_unsafe_identifiers_values_and_payload_tampering() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public payload"):
        observation(cost_model_bucket="raw_market_id_alpha")
    with pytest.raises(ValueError, match="unsafe public payload"):
        config(config_version="dsn-prod")
    with pytest.raises(ValueError, match="unsafe public payload"):
        observation(reason_codes=("source_url",))

    report = build_report(observation())
    payload = dict(report.payload)
    payload["market_id"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_market_cost_model_input_gap_report_payload(payload)

    row_payload = dict(report.payload)
    row_payload["rows"] = [dict(row_payload["rows"][0])]
    row_payload["rows"][0]["wallet"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_market_cost_model_input_gap_report_payload(row_payload)

    assert_public_payload_has_no_forbidden_surface(report.payload)
    encoded = json.dumps(report.payload, sort_keys=True).lower()
    assert "bucket_alpha" not in encoded


def test_hard_flags_are_enforced_and_public_dataclasses_are_frozen() -> None:
    module = api()
    cfg = config()
    item = observation()
    report = build_report(item)
    row = report.rows[0]
    summary = report.component_summaries[0]
    digest = report.digest

    for value in (cfg, item, row, summary, digest, report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        assert_public_numeric_values_are_decimal(value)

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.ResearchMarketCostModelInputGapConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(item, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)


def test_payload_and_digest_are_deterministic_decimal_stringed_and_consistent() -> None:
    module = api()
    left = observation(cost_model_bucket="bucket_left")
    right = observation(
        cost_model_bucket="bucket_right",
        fee_missing_score=d("0.350000"),
        spread_stale_score=d("0.350000"),
        settlement_friction_stale_score=d("0.350000"),
        quote_depth_stale_score=d("0.350000"),
    )

    report_a = build_report(right, left)
    report_b = build_report(left, right)
    payload = module.research_market_cost_model_input_gap_report_payload(report_a)
    digest_payload = module.research_market_cost_model_input_gap_digest_payload(
        report_a.digest,
    )

    assert report_a.payload == report_b.payload
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert report_a.digest == report_b.digest
    assert payload["input_count"] == "2.000000"
    assert payload["rows"][0]["aggregate_gap_score"] == "0.030000"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["derived_validation_digest"] == report_a.derived_validation_digest
    assert payload["digest"] == digest_payload
    assert digest_payload["derived_validation_digest"] == (
        report_a.digest.derived_validation_digest
    )
    assert digest_payload["status"] == report_a.status
    assert digest_payload["input_count"] == payload["input_count"]
    assert set(payload["rows"][0]) >= {"cost_model_bucket_digest"}
    assert_no_float_values(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    statuses = {report_a.status, report_a.digest.status}
    statuses.update(row.status for row in report_a.rows)
    statuses.update(summary.status for summary in report_a.component_summaries)
    assert statuses <= {"pass", "watch", "block"}


def test_report_and_digest_validation_rejects_tampering() -> None:
    module = api()
    report = build_report(
        observation(),
        observation(
            cost_model_bucket="bucket_watch",
            fee_missing_score=d("0.350000"),
        ),
    )

    with pytest.raises(ValueError, match="pass_count must match rows"):
        replace(report, pass_count=d("0.000000"))
    with pytest.raises(ValueError, match="average_aggregate_gap_score must match rows"):
        replace(report, average_aggregate_gap_score=d("0.500000"))
    with pytest.raises(ValueError, match="digest must match report summary"):
        replace(report, digest=build_report().digest)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)

    payload = dict(report.payload)
    payload["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest must match payload fields"):
        module.research_market_cost_model_input_gap_report_payload(payload)

    digest_payload = dict(report.digest.payload)
    digest_payload["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest must match payload fields"):
        module.research_market_cost_model_input_gap_digest_payload(digest_payload)


def test_module_stays_report_only_without_network_storage_or_execution_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
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
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    forbidden_source_fragments = (
        "position sizing",
        "trade execution",
        "place_order",
        "submit_order",
    )
    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sql",
        "subprocess",
        "urllib",
    )
    forbidden_call_fragments = (
        "connect",
        "delete",
        "execute",
        "insert",
        "open",
        "patch",
        "post",
        "put",
        "request",
        "send",
        "sign",
        "submit",
        "update",
        "write",
    )
    forbidden_attribute_fragments = (
        "private_key",
        "place_order",
        "submit_order",
        "wallet",
    )

    assert float_constants == []
    assert not any(fragment in source for fragment in forbidden_source_fragments)
    assert not any(
        fragment in imported.lower()
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(
        fragment in call.lower()
        for call in call_names
        for fragment in forbidden_call_fragments
    )
    assert not any(
        fragment in attribute.lower()
        for attribute in attribute_names
        for fragment in forbidden_attribute_fragments
    )
