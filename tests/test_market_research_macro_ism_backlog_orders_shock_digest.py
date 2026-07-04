from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

GENERATED_AT = datetime(2026, 7, 4, 16, 30, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab"
        ".market_research_macro_ism_backlog_orders_shock_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "source-alpha",
    *,
    release_id: str = "ism-manufacturing-pmi",
    sector: str = "manufacturing",
    market_slug: str = "ism-manufacturing-backlog-orders-above-forecast",
    backlog_orders_index_surprise: str | Decimal = "1.500000",
    new_orders_index_surprise: str | Decimal = "0.800000",
    production_constraint_pressure: str | Decimal = "1.200000",
    supplier_deliveries_stress: str | Decimal = "0.400000",
    source_age_hours: str | Decimal = "6.000000",
    source_quorum_count: str | Decimal = "3.000000",
    source_disagreement: str | Decimal = "0.700000",
    source_timestamp: datetime = datetime(2026, 7, 4, 15, 0, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = ("official_ism_release",),
):
    module = digest()
    return module.MacroIsmBacklogOrdersShockObservation(
        source_id=source_id,
        release_id=release_id,
        sector=sector,
        market_slug=market_slug,
        backlog_orders_index_surprise=(
            backlog_orders_index_surprise
            if isinstance(backlog_orders_index_surprise, Decimal)
            else d(backlog_orders_index_surprise)
        ),
        new_orders_index_surprise=(
            new_orders_index_surprise
            if isinstance(new_orders_index_surprise, Decimal)
            else d(new_orders_index_surprise)
        ),
        production_constraint_pressure=(
            production_constraint_pressure
            if isinstance(production_constraint_pressure, Decimal)
            else d(production_constraint_pressure)
        ),
        supplier_deliveries_stress=(
            supplier_deliveries_stress
            if isinstance(supplier_deliveries_stress, Decimal)
            else d(supplier_deliveries_stress)
        ),
        source_age_hours=(
            source_age_hours if isinstance(source_age_hours, Decimal) else d(source_age_hours)
        ),
        source_quorum_count=(
            source_quorum_count
            if isinstance(source_quorum_count, Decimal)
            else d(source_quorum_count)
        ),
        source_disagreement=(
            source_disagreement
            if isinstance(source_disagreement, Decimal)
            else d(source_disagreement)
        ),
        source_timestamp=source_timestamp,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*rows: object, cfg: object | None = None):
    module = digest()
    return module.build_market_research_macro_ism_backlog_orders_shock_digest(
        rows,
        config=cfg or module.MacroIsmBacklogOrdersShockDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(digest_report, module.MacroIsmBacklogOrdersShockDigestReport)
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-macro-ism-backlog-orders-shock-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_macro_ism_backlog_orders_shock_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.backlog_shock_count == d("0.000000")
    assert digest_report.demand_confirmation_count == d("0.000000")
    assert digest_report.supply_constraint_count == d("0.000000")
    assert digest_report.source_quality_gap_count == d("0.000000")
    assert digest_report.stale_source_count == d("0.000000")
    assert digest_report.max_backlog_orders_surprise == d("0.000000")
    assert digest_report.average_backlog_orders_surprise == d("0.000000")
    assert digest_report.shock_risk_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == ("macro_ism_backlog_orders_shock_digest_empty",)
    assert digest_report.reason_code_counts == (
        module.MacroIsmBacklogOrdersShockReasonCodeCount(
            reason_code="macro_ism_backlog_orders_shock_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_backlog_orders_shock_blocks_macro_event_screening() -> None:
    digest_report = report(
        observation(
            "source-manufacturing",
            market_slug="ism-manufacturing-backlog-orders-above-forecast",
            backlog_orders_index_surprise="5.600000",
            new_orders_index_surprise="2.600000",
            production_constraint_pressure="3.800000",
            supplier_deliveries_stress="2.700000",
            source_age_hours="3.000000",
            source_quorum_count="4.000000",
            source_disagreement="1.100000",
        ),
        observation(
            "source-services",
            release_id="ism-services-pmi",
            sector="services",
            market_slug="ism-services-backlog-orders-above-forecast",
            backlog_orders_index_surprise="2.700000",
            new_orders_index_surprise="1.800000",
            production_constraint_pressure="0.800000",
            supplier_deliveries_stress="2.200000",
            source_timestamp=datetime(
                2026,
                7,
                4,
                10,
                30,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        observation(
            "source-stale",
            market_slug="ism-backlog-source-quality-watch",
            backlog_orders_index_surprise="0.500000",
            new_orders_index_surprise="0.100000",
            production_constraint_pressure="0.200000",
            supplier_deliveries_stress="0.100000",
            source_age_hours="72.000000",
            source_quorum_count="1.000000",
            source_disagreement="4.500000",
            upstream_reason_codes=("stale_release_cache", "vendor_revision"),
        ),
        observation(
            "source-inline",
            market_slug="ism-backlog-inline-surprise",
            backlog_orders_index_surprise="-0.400000",
            new_orders_index_surprise="-0.100000",
            production_constraint_pressure="0.100000",
            supplier_deliveries_stress="0.200000",
            source_age_hours="2.000000",
            source_quorum_count="3.000000",
            source_disagreement="0.200000",
            upstream_reason_codes=(),
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_macro_ism_backlog_orders_shock_screening"
    )
    assert digest_report.input_count == d("4.000000")
    assert digest_report.row_count == d("4.000000")
    assert digest_report.blocked_count == d("2.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.backlog_shock_count == d("2.000000")
    assert digest_report.demand_confirmation_count == d("2.000000")
    assert digest_report.supply_constraint_count == d("2.000000")
    assert digest_report.source_quality_gap_count == d("1.000000")
    assert digest_report.stale_source_count == d("1.000000")
    assert digest_report.max_backlog_orders_surprise == d("5.600000")
    assert digest_report.average_backlog_orders_surprise == d("2.200000")
    assert digest_report.shock_risk_score == d("1.000000")
    assert digest_report.reason_codes == (
        "macro_ism_backlog_orders_shock_blocked_present",
        "macro_ism_backlog_orders_shock_watch_present",
        "macro_ism_backlog_orders_new_orders_confirmed_present",
        "macro_ism_backlog_orders_production_constraint_present",
        "macro_ism_backlog_orders_supplier_deliveries_stress_present",
        "macro_ism_backlog_orders_source_stale_present",
        "macro_ism_backlog_orders_quorum_gap_present",
        "macro_ism_backlog_orders_source_disagreement_present",
        "macro_ism_backlog_orders_upstream_reasons_present",
    )
    assert tuple(row.market_slug for row in digest_report.rows) == (
        "ism-manufacturing-backlog-orders-above-forecast",
        "ism-backlog-source-quality-watch",
        "ism-services-backlog-orders-above-forecast",
        "ism-backlog-inline-surprise",
    )

    blocked, source_quality, watch, passed = digest_report.rows
    assert blocked.shock_status == "blocked"
    assert blocked.positive_backlog_orders_surprise == d("5.600000")
    assert blocked.source_timestamp == datetime(2026, 7, 4, 15, 0, tzinfo=UTC)
    assert blocked.reason_codes == (
        "macro_ism_backlog_orders_blocked_shock",
        "macro_ism_backlog_orders_new_orders_confirmation",
        "macro_ism_backlog_orders_production_constraint",
        "macro_ism_backlog_orders_supplier_deliveries_stress",
        "macro_ism_backlog_orders_upstream_reasons",
    )
    assert source_quality.shock_status == "blocked"
    assert source_quality.reason_codes == (
        "macro_ism_backlog_orders_inline",
        "macro_ism_backlog_orders_source_stale",
        "macro_ism_backlog_orders_quorum_missing",
        "macro_ism_backlog_orders_source_disagreement",
        "macro_ism_backlog_orders_upstream_reasons",
    )
    assert watch.shock_status == "watch"
    assert watch.source_timestamp == datetime(2026, 7, 4, 14, 30, tzinfo=UTC)
    assert watch.reason_codes == (
        "macro_ism_backlog_orders_watch_shock",
        "macro_ism_backlog_orders_new_orders_confirmation",
        "macro_ism_backlog_orders_supplier_deliveries_stress",
        "macro_ism_backlog_orders_upstream_reasons",
    )
    assert passed.shock_status == "pass"
    assert passed.reason_codes == ("macro_ism_backlog_orders_inline",)


def test_rows_reason_codes_and_counts_are_sorted_deterministically() -> None:
    first = observation(
        "source-watch-b",
        market_slug="zeta-watch",
        backlog_orders_index_surprise="2.600000",
    )
    second = observation(
        "source-blocked",
        market_slug="beta-blocked",
        backlog_orders_index_surprise="4.500000",
        production_constraint_pressure="3.200000",
        supplier_deliveries_stress="2.100000",
    )
    third = observation(
        "source-watch-a",
        market_slug="alpha-watch",
        backlog_orders_index_surprise="2.600000",
    )

    forward = report(first, second, third)
    reverse = report(third, second, first)

    assert forward == reverse
    assert tuple(row.market_slug for row in forward.rows) == (
        "beta-blocked",
        "alpha-watch",
        "zeta-watch",
    )
    assert forward.reason_codes == (
        "macro_ism_backlog_orders_shock_blocked_present",
        "macro_ism_backlog_orders_shock_watch_present",
        "macro_ism_backlog_orders_production_constraint_present",
        "macro_ism_backlog_orders_supplier_deliveries_stress_present",
        "macro_ism_backlog_orders_upstream_reasons_present",
    )
    assert tuple(item.reason_code for item in forward.reason_code_counts) == (
        "macro_ism_backlog_orders_shock_blocked_present",
        "macro_ism_backlog_orders_shock_watch_present",
        "macro_ism_backlog_orders_production_constraint_present",
        "macro_ism_backlog_orders_supplier_deliveries_stress_present",
        "macro_ism_backlog_orders_upstream_reasons_present",
    )
    assert tuple(item.count for item in forward.reason_code_counts) == (
        d("1.000000"),
        d("2.000000"),
        d("1.000000"),
        d("1.000000"),
        d("3.000000"),
    )
    assert tuple(item.row_ratio for item in forward.reason_code_counts) == (
        d("0.333333"),
        d("0.666667"),
        d("0.333333"),
        d("0.333333"),
        d("1.000000"),
    )


def test_non_default_thresholds_can_downgrade_moderate_backlog_shock_risk() -> None:
    module = digest()
    cfg = module.MacroIsmBacklogOrdersShockDigestConfig(
        watch_backlog_orders_surprise=d("4.000000"),
        blocked_backlog_orders_surprise=d("7.000000"),
        production_constraint_threshold=d("5.000000"),
        supplier_deliveries_stress_threshold=d("4.000000"),
    )

    digest_report = report(
        observation(
            "source-moderate",
            backlog_orders_index_surprise="2.700000",
            new_orders_index_surprise="1.800000",
            production_constraint_pressure="3.100000",
            supplier_deliveries_stress="2.300000",
        ),
        cfg=cfg,
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_macro_ism_backlog_orders_shock_screening"
    )
    assert digest_report.rows[0].shock_status == "pass"
    assert digest_report.rows[0].reason_codes == (
        "macro_ism_backlog_orders_inline",
        "macro_ism_backlog_orders_new_orders_confirmation",
        "macro_ism_backlog_orders_upstream_reasons",
    )
    assert digest_report.shock_risk_score == d("0.000000")
    assert digest_report.reason_codes == (
        "macro_ism_backlog_orders_new_orders_confirmed_present",
        "macro_ism_backlog_orders_upstream_reasons_present",
    )


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = digest()

    with pytest.raises(
        ValueError,
        match="backlog_orders_index_surprise must be a Decimal",
    ):
        observation(backlog_orders_index_surprise=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="source_age_hours must be nonnegative"):
        observation(source_age_hours="-1.000000")
    with pytest.raises(ValueError, match="source_timestamp must be timezone-aware"):
        observation(source_timestamp=datetime(2026, 7, 4, 15, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_macro_ism_backlog_orders_shock_digest(
            (),
            config=module.MacroIsmBacklogOrdersShockDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 16, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("source-dupe"), observation("source-dupe"))
    with pytest.raises(ValueError, match="watch_backlog_orders_surprise"):
        module.MacroIsmBacklogOrdersShockDigestConfig(
            watch_backlog_orders_surprise=d("8.000000"),
            blocked_backlog_orders_surprise=d("7.000000"),
        )

    valid_row = report(observation("source-valid")).rows[0]
    with pytest.raises(
        ValueError,
        match="positive_backlog_orders_surprise must match",
    ):
        replace(valid_row, positive_backlog_orders_surprise=d("999.000000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            valid_row,
            reason_codes=(
                "macro_ism_backlog_orders_inline",
                "macro_ism_backlog_orders_blocked_shock",
            ),
        )

    frozen_observation = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_hard_flags_are_enforced_on_config_observations_rows_and_report() -> None:
    module = digest()

    digest_report = report(observation("source-hard-flags"))
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in digest_report.rows)

    with pytest.raises(ValueError, match="config paper_only must be True"):
        module.MacroIsmBacklogOrdersShockDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("source-report-only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_payload_uses_string_numerics_and_module_has_no_durable_or_live_surfaces() -> None:
    module = digest()
    digest_report = report(observation("source-payload"))

    payload = module.market_research_macro_ism_backlog_orders_shock_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["backlog_orders_index_surprise"] == "1.500000"
    assert payload["rows"][0]["source_timestamp"] == "2026-07-04T15:00:00+00:00"

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "auth" not in lowered
                assert "submit_order" not in lowered
                assert "cancel_order" not in lowered
                assert "replace_order" not in lowered
                assert "order_id" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)

    for public_record in (
        module.MacroIsmBacklogOrdersShockDigestConfig(),
        observation("source-dataclass"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if _is_public_numeric(field_value):
                assert type(field_value) is Decimal, field.name

    source = Path(
        "src/polymarket_alpha_lab"
        "/market_research_macro_ism_backlog_orders_shock_digest.py",
    ).read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "private_key",
        "wallet",
        "urlopen",
        "connect(",
        "execute(",
        "live trading",
        "submit_order",
        "cancel_order",
        "replace_order",
        "authentication",
        "api_key",
        "fast_mode",
        "exchange",
    ):
        assert forbidden not in source.lower()


def _is_public_numeric(value: object) -> bool:
    return isinstance(value, Decimal)
