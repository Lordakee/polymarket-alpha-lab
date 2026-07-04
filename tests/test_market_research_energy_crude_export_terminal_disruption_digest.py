from __future__ import annotations

import ast
import importlib
import importlib.util
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import numbers
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "market_research_energy_crude_export_terminal_disruption_digest"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_research_energy_crude_export_terminal_disruption_digest.py"
)
GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_MARKET_RESEARCH_ENERGY_CRUDE_EXPORT_TERMINAL_DISRUPTION_DIGEST_CONFIG_VERSION
        ),
        "watch_disruption_probability": d("0.300000"),
        "blocked_disruption_probability": d("0.700000"),
        "watch_capacity_loss_ratio": d("0.200000"),
        "blocked_capacity_loss_ratio": d("0.500000"),
        "long_outage_hours": d("24.000000"),
        "vessel_delay_watch_hours": d("12.000000"),
        "stale_after_hours": d("6.000000"),
        "min_source_count": d("2.000000"),
    }
    values.update(overrides)
    return module.MarketResearchEnergyCrudeExportTerminalDisruptionDigestConfig(
        **values,
    )


def input_row(
    signal_id: str = "signal-alpha",
    *,
    terminal_id: str = "corpus-christi",
    terminal_name: str = "Corpus Christi Crude Terminal",
    region: str = "us-gulf",
    market_slug: str = "corpus-christi-crude-export-disruption",
    observed_at: datetime = GENERATED_AT - timedelta(hours=2),
    source_count: Decimal = d("3.000000"),
    disruption_probability: Decimal = d("0.100000"),
    export_capacity_loss_ratio: Decimal = d("0.050000"),
    expected_outage_hours: Decimal = d("8.000000"),
    affected_export_capacity_bpd: Decimal = d("100000.000000"),
    vessel_queue_delay_hours: Decimal = d("1.000000"),
    evidence_title: str = "Terminal bulletin references analyst@example.com and https://example.com/private",
) -> Any:
    module = api()
    return module.MarketResearchEnergyCrudeExportTerminalDisruptionInput(
        signal_id=signal_id,
        terminal_id=terminal_id,
        terminal_name=terminal_name,
        region=region,
        market_slug=market_slug,
        observed_at=observed_at,
        source_count=source_count,
        disruption_probability=disruption_probability,
        export_capacity_loss_ratio=export_capacity_loss_ratio,
        expected_outage_hours=expected_outage_hours,
        affected_export_capacity_bpd=affected_export_capacity_bpd,
        vessel_queue_delay_hours=vessel_queue_delay_hours,
        evidence_title=evidence_title,
    )


def digest(
    *rows: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_market_research_energy_crude_export_terminal_disruption_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_module_exists_for_phase1_crude_export_terminal_disruption_digest() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_disruption_digest_reduces_terminal_signals_deterministically_and_redacts() -> None:
    module = api()

    report = digest(
        input_row(
            "signal-watch",
            disruption_probability=d("0.450000"),
            export_capacity_loss_ratio=d("0.250000"),
            expected_outage_hours=d("16.000000"),
            affected_export_capacity_bpd=d("250000.000000"),
            vessel_queue_delay_hours=d("4.000000"),
        ),
        input_row(
            "signal-blocked",
            terminal_id="freeport-tx",
            terminal_name="Freeport Crude Export Terminal",
            market_slug="freeport-crude-export-disruption",
            observed_at=datetime(2026, 7, 4, 7, 0, tzinfo=timezone(timedelta(hours=-4))),
            source_count=d("1.000000"),
            disruption_probability=d("0.820000"),
            export_capacity_loss_ratio=d("0.600000"),
            expected_outage_hours=d("42.000000"),
            affected_export_capacity_bpd=d("750000.000000"),
            vessel_queue_delay_hours=d("18.000000"),
            evidence_title=(
                "Freeport bulletin references 0x1234567890abcdef1234567890abcdef12345678"
            ),
        ),
        input_row("signal-pass"),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )

    assert type(report) is (
        module.MarketResearchEnergyCrudeExportTerminalDisruptionDigestReport
    )
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen is True
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-energy-crude-export-terminal-disruption-digest-v0"
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_energy_crude_export_terminal_disruption_screening"
    )
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.blocked_count == d("1.000000")
    assert report.thin_source_count == d("1.000000")
    assert report.total_expected_outage_hours == d("66.000000")
    assert report.total_affected_export_capacity_bpd == d("1100000.000000")
    assert report.max_disruption_probability == d("0.820000")
    assert report.max_capacity_loss_ratio == d("0.600000")
    assert report.max_vessel_queue_delay_hours == d("18.000000")
    assert report.average_disruption_probability == d("0.456667")
    assert report.unresolved_input_ratio == d("0.666667")
    assert report.reason_codes == (
        "crude_export_terminal_disruption_blocked_probability",
        "crude_export_terminal_disruption_blocked_capacity_loss",
        "crude_export_terminal_disruption_watch_probability",
        "crude_export_terminal_disruption_watch_capacity_loss",
        "crude_export_terminal_disruption_long_outage",
        "crude_export_terminal_disruption_vessel_delay",
        "crude_export_terminal_disruption_thin_sources",
    )
    assert tuple(row.signal_id for row in report.rows) == (
        "signal-blocked",
        "signal-watch",
        "signal-pass",
    )

    blocked = report.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.observed_at == datetime(2026, 7, 4, 11, 0, tzinfo=UTC)
    assert blocked.evidence_age_hours == d("1.000000")
    assert blocked.reason_codes == (
        "crude_export_terminal_disruption_blocked_probability",
        "crude_export_terminal_disruption_blocked_capacity_loss",
        "crude_export_terminal_disruption_long_outage",
        "crude_export_terminal_disruption_vessel_delay",
        "crude_export_terminal_disruption_thin_sources",
    )
    assert "[REDACTED_WALLET]" in blocked.redacted_evidence_title
    assert "0x1234567890abcdef1234567890abcdef12345678" not in repr(blocked)

    watch = report.rows[1]
    assert watch.digest_status == "watch"
    assert watch.reason_codes == (
        "crude_export_terminal_disruption_watch_probability",
        "crude_export_terminal_disruption_watch_capacity_loss",
    )
    assert "[REDACTED_EMAIL]" in watch.redacted_evidence_title
    assert "[REDACTED_URL]" in watch.redacted_evidence_title
    assert "analyst@example.com" not in repr(watch)
    assert "https://example.com/private" not in repr(watch)

    assert report.terminal_summaries == (
        module.MarketResearchEnergyCrudeExportTerminalDisruptionTerminalSummary(
            terminal_id="corpus-christi",
            terminal_name="Corpus Christi Crude Terminal",
            region="us-gulf",
            input_count=d("2.000000"),
            watch_count=d("1.000000"),
            blocked_count=d("0.000000"),
            max_disruption_probability=d("0.450000"),
            max_capacity_loss_ratio=d("0.250000"),
            total_expected_outage_hours=d("24.000000"),
            total_affected_export_capacity_bpd=d("350000.000000"),
            max_vessel_queue_delay_hours=d("4.000000"),
        ),
        module.MarketResearchEnergyCrudeExportTerminalDisruptionTerminalSummary(
            terminal_id="freeport-tx",
            terminal_name="Freeport Crude Export Terminal",
            region="us-gulf",
            input_count=d("1.000000"),
            watch_count=d("0.000000"),
            blocked_count=d("1.000000"),
            max_disruption_probability=d("0.820000"),
            max_capacity_loss_ratio=d("0.600000"),
            total_expected_outage_hours=d("42.000000"),
            total_affected_export_capacity_bpd=d("750000.000000"),
            max_vessel_queue_delay_hours=d("18.000000"),
        ),
    )
    assert tuple(item.reason_code for item in report.reason_code_counts) == report.reason_codes
    assert report.reason_code_counts[0].count == d("1.000000")
    assert report.reason_code_counts[0].row_ratio == d("0.333333")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_and_clear_inputs_return_conservative_report_only_outputs() -> None:
    empty = digest()

    assert empty.digest_status == "blocked"
    assert empty.recommended_next_step == (
        "block_report_only_energy_crude_export_terminal_disruption_screening"
    )
    assert empty.reason_codes == ("crude_export_terminal_disruption_digest_empty",)
    assert empty.input_count == d("0.000000")
    assert empty.row_count == d("0.000000")
    assert empty.pass_count == d("0.000000")
    assert empty.watch_count == d("0.000000")
    assert empty.blocked_count == d("0.000000")
    assert empty.total_expected_outage_hours == d("0.000000")
    assert empty.total_affected_export_capacity_bpd == d("0.000000")
    assert empty.max_disruption_probability == d("0.000000")
    assert empty.average_disruption_probability == d("0.000000")
    assert empty.unresolved_input_ratio == d("0.000000")
    assert empty.rows == ()
    assert empty.terminal_summaries == ()
    assert tuple(item.reason_code for item in empty.reason_code_counts) == (
        "crude_export_terminal_disruption_digest_empty",
    )
    assert empty.reason_code_counts[0].count == d("1.000000")
    assert empty.reason_code_counts[0].row_ratio == d("0.000000")

    clear = digest(
        input_row("clear-b", terminal_id="loop", terminal_name="LOOP Terminal"),
        input_row("clear-a"),
        generated_at=datetime(
            2026,
            7,
            4,
            8,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert clear.generated_at == GENERATED_AT
    assert clear.digest_status == "pass"
    assert clear.recommended_next_step == (
        "allow_report_only_energy_crude_export_terminal_disruption_screening"
    )
    assert clear.reason_codes == ("crude_export_terminal_disruption_digest_passed",)
    assert clear.input_count == d("2.000000")
    assert clear.pass_count == d("2.000000")
    assert clear.average_disruption_probability == d("0.100000")
    assert clear.unresolved_input_ratio == d("0.000000")
    assert clear.terminal_summaries == ()


def test_stale_evidence_watches_and_rows_sort_by_status_severity_then_id() -> None:
    report = digest(
        input_row(
            "pass-late",
            observed_at=datetime(2026, 7, 4, 11, 0, tzinfo=UTC),
        ),
        input_row(
            "watch-stale",
            observed_at=datetime(2026, 7, 4, 3, 0, tzinfo=UTC),
        ),
        input_row(
            "watch-probability",
            disruption_probability=d("0.600000"),
            export_capacity_loss_ratio=d("0.100000"),
        ),
    )

    assert tuple(row.signal_id for row in report.rows) == (
        "watch-probability",
        "watch-stale",
        "pass-late",
    )
    assert report.reason_codes == (
        "crude_export_terminal_disruption_watch_probability",
        "crude_export_terminal_disruption_stale_evidence",
    )
    assert report.rows[1].reason_codes == (
        "crude_export_terminal_disruption_stale_evidence",
    )
    assert report.watch_count == d("2.000000")


def test_validation_rejects_bad_inputs_flags_and_inconsistent_public_records() -> None:
    report = digest(input_row())

    with pytest.raises(FrozenInstanceError):
        report.digest_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].digest_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="generated_at"):
        digest(input_row(), generated_at="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        digest(
            input_row(),
            generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        input_row(observed_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="source_count"):
        input_row(source_count=d("1.500000"))
    with pytest.raises(ValueError, match="disruption_probability"):
        input_row(disruption_probability=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="export_capacity_loss_ratio"):
        input_row(export_capacity_loss_ratio=d("0.1000001"))
    with pytest.raises(ValueError, match="expected_outage_hours"):
        input_row(expected_outage_hours=d("-0.000001"))
    with pytest.raises(ValueError, match="watch_disruption_probability"):
        config(
            watch_disruption_probability=d("0.800000"),
            blocked_disruption_probability=d("0.700000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="inputs must contain"):
        digest("not-an-input")
    with pytest.raises(ValueError, match="duplicate signal_id"):
        digest(input_row("duplicate"), input_row("duplicate"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            report.rows[0],
            reason_codes=(
                "crude_export_terminal_disruption_watch_probability",
                "crude_export_terminal_disruption_digest_passed",
            ),
        )


def test_payload_uses_string_numerics_and_public_surface_is_report_only() -> None:
    module = api()
    report = digest(
        input_row(
            "payload-row",
            disruption_probability=d("0.450000"),
            export_capacity_loss_ratio=d("0.250000"),
        ),
    )
    payload = module.market_research_energy_crude_export_terminal_disruption_digest_payload(
        report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["disruption_probability"] == "0.450000"
    assert payload["rows"][0]["affected_export_capacity_bpd"] == "100000.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-04T10:00:00+00:00"
    assert payload["terminal_summaries"][0]["input_count"] == "1.000000"
    assert payload["reason_code_counts"][0]["row_ratio"] == "1.000000"

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "order" not in lowered
                assert "auth" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)

    public_instances = (
        config(),
        input_row(),
        report.rows[0],
        report.terminal_summaries[0],
        report.reason_code_counts[0],
        report,
    )
    for instance in public_instances:
        assert is_dataclass(instance)
        assert instance.__dataclass_params__.frozen is True
        for field in fields(instance):
            value = getattr(instance, field.name)
            if isinstance(value, numbers.Number) and type(value) is not bool:
                assert type(value) is Decimal, f"{type(instance).__name__}.{field.name}"

    assert module.__all__ == (
        "DEFAULT_MARKET_RESEARCH_ENERGY_CRUDE_EXPORT_TERMINAL_DISRUPTION_DIGEST_CONFIG_VERSION",
        "MarketResearchEnergyCrudeExportTerminalDisruptionDigestConfig",
        "MarketResearchEnergyCrudeExportTerminalDisruptionInput",
        "MarketResearchEnergyCrudeExportTerminalDisruptionDigestRow",
        "MarketResearchEnergyCrudeExportTerminalDisruptionTerminalSummary",
        "MarketResearchEnergyCrudeExportTerminalDisruptionReasonCodeCount",
        "MarketResearchEnergyCrudeExportTerminalDisruptionDigestReport",
        "build_market_research_energy_crude_export_terminal_disruption_digest",
        "market_research_energy_crude_export_terminal_disruption_digest_payload",
    )

    source = MODULE_PATH.read_text(encoding="utf-8")
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
        "db",
        "env",
        "cli",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "supabase",
        "web3",
        "wallet",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "private_key",
        "api_key",
        "auth",
        "wallet",
        "urlopen",
        "connect(",
        "execute(",
        "live trading",
        "submit_order",
        "cancel_order",
        "replace_order",
        "exchange mutation",
        "database",
        "postgres",
        "supabase",
        "requests",
        "httpx",
        "socket",
        "fast",
    ):
        assert forbidden not in source.lower()
