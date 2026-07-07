from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 2, 14, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.liquidity_rotation_capacity_alerts",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def summary(
    category_id: str,
    team_id: str,
    *,
    rotation_status: str = "stable",
    liquidity_share_ratio_delta: str = "0.000000",
    ending_liquidity_share_ratio: str = "0.000000",
    capacity_pressure_ratio: str = "0.000000",
    slot_coverage_ratio: str = "1.000000",
    capacity_gap_count: str = "0",
    source_row_count: str = "1",
    source_missing: bool = False,
):
    alerts = api()
    return alerts.LiquidityRotationCapacitySummary(
        category_id=category_id,
        team_id=team_id,
        rotation_status=rotation_status,
        liquidity_share_ratio_delta=d(liquidity_share_ratio_delta),
        ending_liquidity_share_ratio=d(ending_liquidity_share_ratio),
        capacity_pressure_ratio=d(capacity_pressure_ratio),
        slot_coverage_ratio=d(slot_coverage_ratio),
        capacity_gap_count=d(capacity_gap_count),
        source_row_count=d(source_row_count),
        source_missing=source_missing,
    )


def report(*summaries):
    alerts = api()
    return alerts.build_liquidity_rotation_capacity_alerts_report(
        summaries,
        config=alerts.LiquidityRotationCapacityAlertsConfig(),
        generated_at=GENERATED_AT,
    )


def test_report_reduces_supplied_rotation_summaries_to_capacity_alerts() -> None:
    capacity_report = report(
        summary(
            "crypto",
            "crypto_btc",
            rotation_status="rotating_in",
            liquidity_share_ratio_delta="0.120000",
            ending_liquidity_share_ratio="0.450000",
            capacity_pressure_ratio="2.500000",
            slot_coverage_ratio="0.300000",
            capacity_gap_count="2",
        ),
        summary(
            "politics",
            "politics",
            rotation_status="rotating_in",
            liquidity_share_ratio_delta="0.080000",
            ending_liquidity_share_ratio="0.250000",
            capacity_pressure_ratio="1.200000",
            slot_coverage_ratio="0.700000",
        ),
        summary(
            "sports",
            "sports_soccer",
            rotation_status="rotating_out",
            liquidity_share_ratio_delta="-0.070000",
            ending_liquidity_share_ratio="0.100000",
            capacity_pressure_ratio="0.400000",
            slot_coverage_ratio="2.000000",
        ),
        summary(
            "macro",
            "macro_rates",
            rotation_status="stable",
            liquidity_share_ratio_delta="0.000000",
            ending_liquidity_share_ratio="0.200000",
            capacity_pressure_ratio="0.200000",
            slot_coverage_ratio="3.000000",
        ),
    )

    assert is_dataclass(capacity_report)
    assert capacity_report.generated_at == GENERATED_AT
    assert capacity_report.config_version == "liquidity-rotation-capacity-alerts-v0"
    assert capacity_report.source_summary_count == d("4")
    assert capacity_report.alert_row_count == d("4")
    assert capacity_report.pass_alert_count == d("2")
    assert capacity_report.watch_alert_count == d("1")
    assert capacity_report.blocked_alert_count == d("1")
    assert capacity_report.source_missing_count == d("0")
    assert capacity_report.status == "blocked"
    assert capacity_report.reason_codes == ("liquidity_rotation_capacity_blocked",)
    assert capacity_report.paper_only is True
    assert capacity_report.report_only is True
    assert capacity_report.readonly is True

    blocked = capacity_report.alert_rows[0]
    assert blocked.redacted_category_ref == "<redacted-category-001>"
    assert blocked.redacted_team_ref == "<redacted-team-001>"
    assert blocked.rotation_status == "rotating_in"
    assert blocked.liquidity_share_ratio_delta == d("0.120000")
    assert blocked.capacity_pressure_ratio == d("2.500000")
    assert blocked.slot_coverage_ratio == d("0.300000")
    assert blocked.capacity_gap_count == d("2")
    assert blocked.alert_status == "blocked"
    assert blocked.reason_codes == (
        "rotating_in_capacity_blocked",
        "capacity_gap_present",
        "low_slot_coverage",
        "capacity_pressure_blocked",
    )

    watch = capacity_report.alert_rows[1]
    assert watch.redacted_category_ref == "<redacted-category-003>"
    assert watch.alert_status == "watch"
    assert watch.reason_codes == (
        "rotating_in_capacity_watch",
        "capacity_pressure_watch",
    )

    released = capacity_report.alert_rows[2]
    assert released.redacted_category_ref == "<redacted-category-004>"
    assert released.alert_status == "pass"
    assert released.reason_codes == ("rotating_out_capacity_release",)

    report_text = repr(capacity_report)
    for sensitive_token in (
        "crypto_btc",
        "politics",
        "sports_soccer",
        "macro_rates",
    ):
        assert sensitive_token not in report_text


def test_empty_report_is_readonly_pass_with_decimal_zero_counts() -> None:
    capacity_report = report()

    assert capacity_report.source_summary_count == d("0")
    assert capacity_report.alert_row_count == d("0")
    assert capacity_report.pass_alert_count == d("0")
    assert capacity_report.watch_alert_count == d("0")
    assert capacity_report.blocked_alert_count == d("0")
    assert capacity_report.source_missing_count == d("0")
    assert capacity_report.status == "pass"
    assert capacity_report.reason_codes == ("liquidity_rotation_capacity_clear",)
    assert capacity_report.alert_rows == ()
    assert capacity_report.paper_only is True
    assert capacity_report.report_only is True
    assert capacity_report.readonly is True


def test_source_missing_is_watch_only_and_keeps_public_output_redacted() -> None:
    secret_category = "secret-category-liquidity"
    secret_team = "secret-team-capacity"
    capacity_report = report(
        summary(
            secret_category,
            secret_team,
            rotation_status="rotating_in",
            liquidity_share_ratio_delta="0.400000",
            ending_liquidity_share_ratio="0.500000",
            capacity_pressure_ratio="9.000000",
            slot_coverage_ratio="0.000000",
            capacity_gap_count="9",
            source_row_count="0",
            source_missing=True,
        ),
    )

    row = capacity_report.alert_rows[0]
    assert capacity_report.status == "watch"
    assert capacity_report.reason_codes == (
        "liquidity_rotation_capacity_watch",
        "liquidity_rotation_capacity_source_missing",
    )
    assert capacity_report.source_missing_count == d("1")
    assert row.alert_status == "watch"
    assert row.reason_codes == ("liquidity_rotation_capacity_source_missing",)
    assert row.redacted_category_ref == "<redacted-category-001>"
    assert row.redacted_team_ref == "<redacted-team-001>"
    assert secret_category not in repr(capacity_report)
    assert secret_team not in repr(capacity_report)


def test_payload_is_json_ready_redacted_and_omits_trading_or_advice_surfaces() -> None:
    alerts = api()
    capacity_report = report(
        summary(
            "crypto",
            "crypto_eth",
            rotation_status="rotating_in",
            liquidity_share_ratio_delta="0.100000",
            ending_liquidity_share_ratio="0.300000",
            capacity_pressure_ratio="1.200000",
            slot_coverage_ratio="0.800000",
        ),
    )

    payload = alerts.liquidity_rotation_capacity_alerts_payload(capacity_report)
    payload_text = repr(payload).lower()

    assert "crypto_eth" not in payload_text
    assert "market_slug" not in payload_text
    assert "question" not in payload_text
    assert "recommend" not in payload_text
    assert "advice" not in payload_text
    assert "wallet" not in payload_text
    assert "order" not in payload_text
    assert payload["source_summary_count"] == "1"
    assert payload["alert_rows"][0]["redacted_category_ref"] == "<redacted-category-001>"
    assert payload["alert_rows"][0]["capacity_pressure_ratio"] == "1.200000"
    assert payload["derived_validation_digest"] == capacity_report.derived_validation_digest
    assert payload["paper_only"] is True


def test_report_uses_deterministic_derived_validation_digest_and_rejects_tampering() -> None:
    capacity_report = report(
        summary(
            "crypto",
            "crypto_eth",
            rotation_status="rotating_in",
            liquidity_share_ratio_delta="0.100000",
            ending_liquidity_share_ratio="0.300000",
            capacity_pressure_ratio="1.200000",
            slot_coverage_ratio="0.800000",
        ),
    )
    rebuilt_report = report(
        summary(
            "crypto",
            "crypto_eth",
            rotation_status="rotating_in",
            liquidity_share_ratio_delta="0.100000",
            ending_liquidity_share_ratio="0.300000",
            capacity_pressure_ratio="1.200000",
            slot_coverage_ratio="0.800000",
        ),
    )

    assert len(capacity_report.derived_validation_digest) == 64
    assert all(
        character in "0123456789abcdef"
        for character in capacity_report.derived_validation_digest
    )
    assert capacity_report.derived_validation_digest == rebuilt_report.derived_validation_digest

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(capacity_report, derived_validation_digest="0" * 64)


def test_dataclasses_validate_decimal_thresholds_flags_and_frozen_instances() -> None:
    alerts = api()
    row = report(summary("macro", "macro_rates")).alert_rows[0]

    assert is_dataclass(row)
    with pytest.raises(FrozenInstanceError):
        row.alert_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="capacity_pressure_ratio must be a Decimal"):
        alerts.LiquidityRotationCapacitySummary(
            category_id="crypto",
            team_id="crypto_btc",
            rotation_status="stable",
            liquidity_share_ratio_delta=d("0.000000"),
            ending_liquidity_share_ratio=d("0.000000"),
            capacity_pressure_ratio=1.0,
            slot_coverage_ratio=d("1.000000"),
            capacity_gap_count=d("0"),
        )

    class DerivedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="min_rotation_in_share_delta"):
        alerts.LiquidityRotationCapacityAlertsConfig(
            min_rotation_in_share_delta=DerivedDecimal("0.050000"),
        )

    with pytest.raises(ValueError, match="capacity_pressure_blocked_ratio"):
        alerts.LiquidityRotationCapacityAlertsConfig(
            capacity_pressure_watch_ratio=d("2.000000"),
            capacity_pressure_blocked_ratio=d("1.000000"),
        )

    with pytest.raises(ValueError, match="source_missing must be a bool"):
        alerts.LiquidityRotationCapacitySummary(
            category_id="crypto",
            team_id="crypto_btc",
            rotation_status="stable",
            liquidity_share_ratio_delta=d("0.000000"),
            ending_liquidity_share_ratio=d("0.000000"),
            capacity_pressure_ratio=d("0.000000"),
            slot_coverage_ratio=d("1.000000"),
            capacity_gap_count=d("0"),
            source_missing=1,
        )

    with pytest.raises(ValueError, match="duplicate category team pairs"):
        report(
            summary("crypto", "crypto_btc"),
            summary("crypto", "crypto_btc"),
        )

    with pytest.raises(ValueError, match="paper_only must be True"):
        alerts.LiquidityRotationCapacityAlertsConfig(paper_only=False)


def test_generated_at_is_normalized_to_utc_and_rejects_naive_datetime() -> None:
    alerts = api()
    capacity_report = alerts.build_liquidity_rotation_capacity_alerts_report(
        (),
        config=alerts.LiquidityRotationCapacityAlertsConfig(),
        generated_at=datetime(2026, 7, 2, 9, 0, tzinfo=timezone.utc),
    )

    assert capacity_report.generated_at == datetime(2026, 7, 2, 9, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        alerts.build_liquidity_rotation_capacity_alerts_report(
            (),
            config=alerts.LiquidityRotationCapacityAlertsConfig(),
            generated_at=datetime(2026, 7, 2, 9, 0),
        )


def test_module_scope_is_pure_report_reducer_with_local_exports_only() -> None:
    alerts = api()
    source = inspect.getsource(alerts)
    tree = ast.parse(source)

    assert alerts.__all__ == (
        "DEFAULT_LIQUIDITY_ROTATION_CAPACITY_ALERTS_CONFIG_VERSION",
        "ROTATION_STATUSES",
        "ALERT_STATUSES",
        "LiquidityRotationCapacityAlertsConfig",
        "LiquidityRotationCapacitySummary",
        "LiquidityRotationCapacityAlertRow",
        "LiquidityRotationCapacityAlertsReport",
        "build_liquidity_rotation_capacity_alerts_report",
        "liquidity_rotation_capacity_alerts_payload",
    )
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "typing",
        "polymarket_alpha_lab",
    }
    forbidden_source_terms = (
        "account",
        "auth",
        "database",
        "db",
        "httpx",
        "investment_advice",
        "live",
        "network",
        "order",
        "postgres",
        "private_key",
        "requests",
        "supabase",
        "trade",
        "trading",
        "wallet",
        "write",
    )
    for term in forbidden_source_terms:
        assert term not in source.lower()
