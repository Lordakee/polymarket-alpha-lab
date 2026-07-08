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
    / "research_market_cost_input_drift_watch_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_cost_input_drift_watch_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-market-cost-input-drift-watch-report-test",
        "watch_spread_drift_bps": d("10"),
        "block_spread_drift_bps": d("50"),
        "watch_taker_fee_drift_bps": d("5"),
        "block_taker_fee_drift_bps": d("20"),
        "watch_depth_slope_drift_bps": d("20"),
        "block_depth_slope_drift_bps": d("80"),
        "watch_friction_drift_bps": d("10"),
        "block_friction_drift_bps": d("40"),
        "watch_total_friction_drift_bps": d("20"),
        "block_total_friction_drift_bps": d("80"),
        "watch_quote_age_seconds": d("300"),
        "block_quote_age_seconds": d("900"),
    }
    values.update(overrides)
    return module.ResearchMarketCostInputDriftWatchConfig(**values)


def observation(**overrides: object):
    module = api()
    values = {
        "cost_input_bucket": "bucket_alpha",
        "cost_surface_bucket": "surface_alpha",
        "observed_at": GENERATED_AT - timedelta(minutes=5),
        "baseline_spread_bps": d("20"),
        "current_spread_bps": d("22"),
        "baseline_taker_fee_bps": d("2"),
        "current_taker_fee_bps": d("3"),
        "baseline_depth_slope_bps": d("30"),
        "current_depth_slope_bps": d("35"),
        "baseline_gas_friction_bps": d("3"),
        "current_gas_friction_bps": d("4"),
        "baseline_deposit_friction_bps": d("2"),
        "current_deposit_friction_bps": d("3"),
        "baseline_settlement_friction_bps": d("5"),
        "current_settlement_friction_bps": d("6"),
        "quote_age_seconds": d("60"),
        "reason_codes": (),
    }
    values.update(overrides)
    return module.ResearchMarketCostInputObservation(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_cost_input_drift_watch_report(
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
        "market_slug",
        "condition_id",
        "slug",
        "question",
        "http://",
        "https://",
        "source_id",
        "source_ref",
        "source_url",
        "source_text",
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
        "private key",
        "buy",
        "sell",
        "recommend",
        "position",
        "bucket_alpha",
        "surface_alpha",
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

    assert module.DEFAULT_RESEARCH_MARKET_COST_INPUT_DRIFT_WATCH_CONFIG_VERSION == (
        "research-market-cost-input-drift-watch-report-v0"
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_MARKET_COST_INPUT_DRIFT_WATCH_CONFIG_VERSION",
        "ResearchMarketCostInputDriftWatchConfig",
        "ResearchMarketCostInputObservation",
        "ResearchMarketCostInputDriftWatchRow",
        "ResearchMarketCostInputDriftWatchDigest",
        "ResearchMarketCostInputDriftWatchReport",
        "build_research_market_cost_input_drift_watch_report",
        "research_market_cost_input_drift_watch_report_payload",
        "research_market_cost_input_drift_watch_digest_payload",
    )

    field_defaults = {
        field.name: field.default
        for field in fields(module.ResearchMarketCostInputDriftWatchConfig)
    }
    assert field_defaults["paper_only"] is True
    assert field_defaults["report_only"] is True
    assert field_defaults["readonly"] is True


def test_builds_pass_watch_and_block_rows_from_abstract_cost_inputs() -> None:
    report = build_report(
        observation(cost_input_bucket="bucket_alpha", cost_surface_bucket="surface_alpha"),
        observation(
            cost_input_bucket="bucket_beta",
            cost_surface_bucket="surface_beta",
            current_spread_bps=d("35"),
            current_taker_fee_bps=d("8"),
            current_depth_slope_bps=d("60"),
            current_gas_friction_bps=d("16"),
            current_deposit_friction_bps=d("7"),
            current_settlement_friction_bps=d("15"),
            quote_age_seconds=d("600"),
        ),
        observation(
            cost_input_bucket="bucket_gamma",
            cost_surface_bucket="surface_gamma",
            current_spread_bps=d("80"),
            current_taker_fee_bps=d("25"),
            current_depth_slope_bps=d("130"),
            current_gas_friction_bps=d("45"),
            current_deposit_friction_bps=d("45"),
            current_settlement_friction_bps=d("50"),
            quote_age_seconds=d("1200"),
        ),
    )

    assert is_dataclass(report)
    assert report.status == "block"
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_absolute_total_cost_drift_bps == d("134.333333")
    assert report.max_absolute_total_cost_drift_bps == d("313.000000")
    assert report.max_quote_age_seconds == d("1200.000000")
    assert report.reason_codes == (
        "cost_input_drift_report_block_rows",
        "cost_input_drift_report_watch_rows",
    )

    assert tuple((row.cost_input_bucket, row.cost_surface_bucket) for row in report.rows) == (
        ("bucket_alpha", "surface_alpha"),
        ("bucket_beta", "surface_beta"),
        ("bucket_gamma", "surface_gamma"),
    )
    assert tuple(row.status for row in report.rows) == ("pass", "watch", "block")
    assert report.rows[0].reason_codes == ("cost_input_drift_pass",)
    assert report.rows[0].baseline_total_cost_bps == d("62.000000")
    assert report.rows[0].current_total_cost_bps == d("73.000000")
    assert report.rows[1].reason_codes == (
        "spread_drift_watch",
        "taker_fee_drift_watch",
        "depth_slope_drift_watch",
        "gas_friction_drift_watch",
        "settlement_friction_drift_watch",
        "total_friction_drift_watch",
        "quote_staleness_watch",
        "cost_input_drift_watch",
    )
    assert report.rows[2].reason_codes == (
        "spread_drift_block",
        "taker_fee_drift_block",
        "depth_slope_drift_block",
        "gas_friction_drift_block",
        "deposit_friction_drift_block",
        "settlement_friction_drift_block",
        "total_friction_drift_block",
        "quote_staleness_block",
        "cost_input_drift_block",
    )


def test_empty_and_stale_reports_are_report_only_blocks() -> None:
    module = api()
    empty = build_report()

    assert empty.status == "block"
    assert empty.input_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == ("no_cost_input_drift_observations",)

    stale = build_report(observation(quote_age_seconds=d("300")))
    assert stale.status == "watch"
    assert stale.rows[0].reason_codes == (
        "quote_staleness_watch",
        "cost_input_drift_watch",
    )

    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(stale.rows[0], status="blocked")
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(stale.digest, status="ready")
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        module.ResearchMarketCostInputDriftWatchReport(
            **{**stale.__dict__, "status": "review"},
        )


@pytest.mark.parametrize(
    ("factory", "message"),
    (
        (
            lambda: observation(current_spread_bps=20),
            "current_spread_bps must be exactly Decimal",
        ),
        (
            lambda: observation(current_taker_fee_bps=2.5),
            "current_taker_fee_bps must be exactly Decimal",
        ),
        (
            lambda: observation(current_depth_slope_bps=_DecimalSubclass("31")),
            "current_depth_slope_bps must be exactly Decimal",
        ),
        (
            lambda: observation(current_gas_friction_bps=d("4.0000001")),
            "current_gas_friction_bps must use six decimal places or fewer",
        ),
        (
            lambda: observation(current_deposit_friction_bps=d("-0.1")),
            "current_deposit_friction_bps must be >= 0.000000",
        ),
        (
            lambda: config(watch_quote_age_seconds=d("900"), block_quote_age_seconds=d("300")),
            "watch_quote_age_seconds must not exceed block_quote_age_seconds",
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
        observation(cost_input_bucket="raw_market_id_alpha")
    with pytest.raises(ValueError, match="unsafe public payload"):
        observation(cost_surface_bucket="source_id_primary")
    with pytest.raises(ValueError, match="unsafe public payload"):
        config(config_version="dsn-prod")
    with pytest.raises(ValueError, match="unsafe public payload"):
        observation(reason_codes=("source_url",))

    report = build_report(observation())
    payload = dict(report.payload)
    payload["market_id"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_market_cost_input_drift_watch_report_payload(payload)

    row_payload = dict(report.payload)
    row_payload["rows"] = [dict(row_payload["rows"][0])]
    row_payload["rows"][0]["source_id"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_market_cost_input_drift_watch_report_payload(row_payload)

    assert_public_payload_has_no_forbidden_surface(report.payload)
    encoded = json.dumps(report.payload, sort_keys=True).lower()
    assert "bucket_alpha" not in encoded
    assert "surface_alpha" not in encoded


def test_hard_flags_are_enforced_and_public_dataclasses_are_frozen() -> None:
    module = api()
    cfg = config()
    item = observation()
    report = build_report(item)
    row = report.rows[0]
    digest = report.digest

    for value in (cfg, item, row, digest, report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        assert_public_numeric_values_are_decimal(value)

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.ResearchMarketCostInputDriftWatchConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(item, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)


def test_payload_and_digest_are_deterministic_decimal_stringed_and_consistent() -> None:
    module = api()
    left = observation(cost_input_bucket="bucket_left", cost_surface_bucket="surface_left")
    right = observation(
        cost_input_bucket="bucket_right",
        cost_surface_bucket="surface_right",
        current_spread_bps=d("35"),
        current_taker_fee_bps=d("8"),
        current_depth_slope_bps=d("60"),
        current_gas_friction_bps=d("16"),
        current_settlement_friction_bps=d("15"),
        quote_age_seconds=d("600"),
    )

    report_a = build_report(right, left)
    report_b = build_report(left, right)
    payload = module.research_market_cost_input_drift_watch_report_payload(report_a)
    digest_payload = module.research_market_cost_input_drift_watch_digest_payload(
        report_a.digest,
    )

    assert report_a.payload == report_b.payload
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert report_a.digest == report_b.digest
    assert payload["input_count"] == "2.000000"
    assert payload["rows"][0]["absolute_total_cost_drift_bps"] == "11.000000"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["derived_validation_digest"] == report_a.derived_validation_digest
    assert payload["digest"] == digest_payload
    assert digest_payload["derived_validation_digest"] == report_a.digest.derived_validation_digest
    assert digest_payload["status"] == report_a.status
    assert digest_payload["input_count"] == payload["input_count"]
    assert set(payload["rows"][0]) >= {"input_bucket_digest", "surface_bucket_digest"}
    assert_no_float_values(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    statuses = {report_a.status, report_a.digest.status}
    statuses.update(row.status for row in report_a.rows)
    assert statuses <= {"pass", "watch", "block"}


def test_report_and_digest_validation_rejects_tampering() -> None:
    module = api()
    report = build_report(
        observation(),
        observation(
            cost_input_bucket="bucket_watch",
            cost_surface_bucket="surface_watch",
            current_spread_bps=d("35"),
            current_taker_fee_bps=d("8"),
            current_depth_slope_bps=d("60"),
            current_gas_friction_bps=d("16"),
            current_settlement_friction_bps=d("15"),
            quote_age_seconds=d("600"),
        ),
    )

    with pytest.raises(ValueError, match="pass_count must match rows"):
        replace(report, pass_count=d("0.000000"))
    with pytest.raises(ValueError, match="average_absolute_total_cost_drift_bps must match rows"):
        replace(report, average_absolute_total_cost_drift_bps=d("0.500000"))
    with pytest.raises(ValueError, match="digest must match report summary"):
        replace(report, digest=build_report().digest)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)

    payload = dict(report.payload)
    payload["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest must match payload fields"):
        module.research_market_cost_input_drift_watch_report_payload(payload)

    digest_payload = dict(report.digest.payload)
    digest_payload["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest must match payload fields"):
        module.research_market_cost_input_drift_watch_digest_payload(digest_payload)


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
        "buy",
        "sell",
        "recommend",
        "position sizing",
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
