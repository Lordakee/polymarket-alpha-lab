from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

import pytest

from polymarket_alpha_lab.paper_trade_cost_audit import PaperTradeCostAuditReport
from polymarket_alpha_lab.paper_trade_cost_audit_db_row import (
    PaperTradeCostAuditReportDbRow,
    paper_trade_cost_audit_report_from_db_row,
    paper_trade_cost_audit_report_to_db_row,
)


GENERATED_AT = datetime(2026, 6, 20, 0, 30, tzinfo=UTC)
CONFIG_VERSION = "paper-trade-cost-audit-db-v0"
MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "supabase"
    / "migrations"
    / "20260620000006_paper_trade_cost_audit_reports.sql"
)


class PaperTradeCostAuditReportSubclass(PaperTradeCostAuditReport):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _report(
    *,
    generated_at: datetime = GENERATED_AT,
) -> PaperTradeCostAuditReport:
    return PaperTradeCostAuditReport(
        generated_at=generated_at,
        config_version=CONFIG_VERSION,
        trade_count=3,
        total_filled_size=d("240"),
        total_requested_size=d("300"),
        fill_rate=d("0.800000"),
        mean_theoretical_edge=d("0.060000"),
        mean_cost_adjusted_edge=d("0.030000"),
        mean_edge_cost_drag=d("0.030000"),
        total_edge_cost_drag=d("6.600000"),
        mean_research_slippage=d("0.004667"),
        mean_fill_slippage=d("0.009000"),
        partial_fill_count=1,
        negative_cost_adjusted_edge_count=1,
        largest_single_trade_cost_drag=d("3.000000"),
    )


def _empty_report() -> PaperTradeCostAuditReport:
    return PaperTradeCostAuditReport(
        generated_at=GENERATED_AT,
        config_version=CONFIG_VERSION,
        trade_count=0,
        total_filled_size=d("0"),
        total_requested_size=d("0"),
        fill_rate=None,
        mean_theoretical_edge=None,
        mean_cost_adjusted_edge=None,
        mean_edge_cost_drag=None,
        total_edge_cost_drag=None,
        mean_research_slippage=None,
        mean_fill_slippage=None,
        partial_fill_count=0,
        negative_cost_adjusted_edge_count=0,
        largest_single_trade_cost_drag=None,
    )


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("DB payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def _canonical_payload_sha256(payload_json: dict[str, object]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _unchecked_row(row: object, **overrides: object) -> object:
    values = dict(row.__dict__)
    values.update(overrides)
    unchecked = object.__new__(type(row))
    for field_name, value in values.items():
        object.__setattr__(unchecked, field_name, value)
    return unchecked


def _migration_table_body() -> str:
    sql = MIGRATION.read_text(encoding="utf-8")
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.paper_trade_cost_audit_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, "migration must create public.paper_trade_cost_audit_reports"
    return re.sub(r"\s+", " ", match.group(1).strip().lower())


def _migration_sql() -> str:
    return re.sub(r"\s+", " ", MIGRATION.read_text(encoding="utf-8").strip().lower())


def test_db_row_serializes_core_cost_evidence_payload_and_round_trips() -> None:
    report = _report(
        generated_at=datetime(2026, 6, 19, 20, 30, tzinfo=timezone(timedelta(hours=-4))),
    )

    row = paper_trade_cost_audit_report_to_db_row(report)

    assert type(row) is PaperTradeCostAuditReportDbRow
    assert len(row.report_sha256) == 64
    assert row.report_sha256 == row.report_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.config_version == CONFIG_VERSION
    assert row.trade_count == 3
    assert row.total_filled_size == d("240")
    assert row.total_requested_size == d("300")
    assert row.fill_rate == d("0.800000")
    assert row.mean_theoretical_edge == d("0.060000")
    assert row.mean_cost_adjusted_edge == d("0.030000")
    assert row.mean_edge_cost_drag == d("0.030000")
    assert row.total_edge_cost_drag == d("6.600000")
    assert row.mean_research_slippage == d("0.004667")
    assert row.mean_fill_slippage == d("0.009000")
    assert row.partial_fill_count == 1
    assert row.negative_cost_adjusted_edge_count == 1
    assert row.largest_single_trade_cost_drag == d("3.000000")
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json == {
        "generated_at": "2026-06-20T00:30:00+00:00",
        "config_version": CONFIG_VERSION,
        "trade_count": 3,
        "total_filled_size": "240",
        "total_requested_size": "300",
        "fill_rate": "0.800000",
        "mean_theoretical_edge": "0.060000",
        "mean_cost_adjusted_edge": "0.030000",
        "mean_edge_cost_drag": "0.030000",
        "total_edge_cost_drag": "6.600000",
        "mean_research_slippage": "0.004667",
        "mean_fill_slippage": "0.009000",
        "partial_fill_count": 1,
        "negative_cost_adjusted_edge_count": 1,
        "largest_single_trade_cost_drag": "3.000000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    _assert_no_floats(row.payload_json)

    assert paper_trade_cost_audit_report_from_db_row(row) == report


def test_db_row_preserves_empty_report_null_metrics_and_round_trips() -> None:
    row = paper_trade_cost_audit_report_to_db_row(_empty_report())

    assert row.trade_count == 0
    assert row.total_filled_size == d("0")
    assert row.total_requested_size == d("0")
    assert row.fill_rate is None
    assert row.mean_theoretical_edge is None
    assert row.mean_cost_adjusted_edge is None
    assert row.mean_edge_cost_drag is None
    assert row.total_edge_cost_drag is None
    assert row.mean_research_slippage is None
    assert row.mean_fill_slippage is None
    assert row.largest_single_trade_cost_drag is None
    assert row.payload_json["mean_fill_slippage"] is None

    assert paper_trade_cost_audit_report_from_db_row(row) == _empty_report()


def test_db_row_hash_uses_full_canonical_payload_and_is_deterministic() -> None:
    report = _report()
    same_report = PaperTradeCostAuditReport(**report.__dict__)
    different_payload_same_summary = replace(report, config_version="paper-trade-cost-audit-db-v1")

    first = paper_trade_cost_audit_report_to_db_row(report)
    second = paper_trade_cost_audit_report_to_db_row(same_report)
    different = paper_trade_cost_audit_report_to_db_row(different_payload_same_summary)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != different.report_sha256
    assert first.trade_count == different.trade_count
    assert first.total_edge_cost_drag == different.total_edge_cost_drag


def test_db_row_is_frozen() -> None:
    row = paper_trade_cost_audit_report_to_db_row(_empty_report())

    with pytest.raises(FrozenInstanceError):
        row.trade_count = 1  # type: ignore[misc]


def test_db_row_rejects_wrong_report_type_and_subclasses() -> None:
    with pytest.raises(ValueError, match="PaperTradeCostAuditReport"):
        paper_trade_cost_audit_report_to_db_row(object())

    report = _empty_report()
    subclass = PaperTradeCostAuditReportSubclass(**report.__dict__)
    with pytest.raises(ValueError, match="PaperTradeCostAuditReport"):
        paper_trade_cost_audit_report_to_db_row(subclass)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_db_row_rejects_false_report_flags(flag_name: str) -> None:
    report = _empty_report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        paper_trade_cost_audit_report_to_db_row(report)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_db_row_rejects_false_stored_payload_flags(flag_name: str) -> None:
    row = paper_trade_cost_audit_report_to_db_row(_empty_report())

    with pytest.raises(ValueError, match=flag_name):
        PaperTradeCostAuditReportDbRow(
            report_sha256="a" * 64,
            generated_at=row.generated_at,
            config_version=row.config_version,
            trade_count=row.trade_count,
            total_filled_size=row.total_filled_size,
            total_requested_size=row.total_requested_size,
            fill_rate=row.fill_rate,
            mean_theoretical_edge=row.mean_theoretical_edge,
            mean_cost_adjusted_edge=row.mean_cost_adjusted_edge,
            mean_edge_cost_drag=row.mean_edge_cost_drag,
            total_edge_cost_drag=row.total_edge_cost_drag,
            mean_research_slippage=row.mean_research_slippage,
            mean_fill_slippage=row.mean_fill_slippage,
            partial_fill_count=row.partial_fill_count,
            negative_cost_adjusted_edge_count=row.negative_cost_adjusted_edge_count,
            largest_single_trade_cost_drag=row.largest_single_trade_cost_drag,
            payload_json={**row.payload_json, flag_name: False},
        )


def test_db_row_wraps_payload_recovery_errors_as_value_error() -> None:
    row = paper_trade_cost_audit_report_to_db_row(_empty_report())
    malformed = object.__new__(PaperTradeCostAuditReportDbRow)
    for field_name, value in row.__dict__.items():
        object.__setattr__(malformed, field_name, value)
    object.__setattr__(malformed, "report_sha256", "a" * 64)
    object.__setattr__(
        malformed,
        "payload_json",
        {key: value for key, value in row.payload_json.items() if key != "trade_count"},
    )

    with pytest.raises(ValueError, match="payload_json"):
        paper_trade_cost_audit_report_from_db_row(malformed)


def test_db_row_validates_shape_floats_and_summary_matches_payload() -> None:
    row = paper_trade_cost_audit_report_to_db_row(_report())

    with pytest.raises(ValueError, match="report_sha256"):
        replace(row, report_sha256="bad")

    with pytest.raises(ValueError, match="payload_json"):
        replace(row, payload_json={**row.payload_json, "bad_float": 0.1})

    with pytest.raises(ValueError, match="trade_count must match payload_json"):
        replace(row, trade_count=2)

    with pytest.raises(ValueError, match="report_sha256 must match payload_json"):
        replace(row, report_sha256="b" * 64)


def test_db_row_readback_rejects_object_new_bypass_mismatch() -> None:
    row = paper_trade_cost_audit_report_to_db_row(_report())
    malformed = _unchecked_row(row, trade_count=2)

    with pytest.raises(ValueError, match="trade_count"):
        paper_trade_cost_audit_report_from_db_row(malformed)


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("total_filled_size", d("240.000000")),
        ("total_requested_size", d("300.000000")),
        ("fill_rate", d("0.8000000")),
        ("mean_theoretical_edge", d("0.0600000")),
        ("mean_cost_adjusted_edge", d("0.0300000")),
        ("mean_edge_cost_drag", d("0.0300000")),
        ("total_edge_cost_drag", d("6.6000000")),
        ("mean_research_slippage", d("0.0046670")),
        ("mean_fill_slippage", d("0.0090000")),
        ("largest_single_trade_cost_drag", d("3.0000000")),
    ),
)
def test_db_row_from_db_row_rejects_bypassed_noncanonical_materialized_decimal(
    field_name: str,
    value: Decimal,
) -> None:
    row = paper_trade_cost_audit_report_to_db_row(_report())
    malformed = _unchecked_row(row, **{field_name: value})

    with pytest.raises(ValueError, match=field_name):
        paper_trade_cost_audit_report_from_db_row(malformed)


@pytest.mark.parametrize(
    ("payload_updates", "expected_message"),
    (
        ({"partial_fill_count": True}, "partial_fill_count"),
        (
            {"negative_cost_adjusted_edge_count": True},
            "negative_cost_adjusted_edge_count",
        ),
        ({"fill_rate": "0.8000000"}, "canonical|fill_rate"),
    ),
)
def test_db_row_rejects_type_loose_or_noncanonical_payload_values(
    payload_updates: dict[str, object],
    expected_message: str,
) -> None:
    row = paper_trade_cost_audit_report_to_db_row(_report())
    payload = {**row.payload_json, **payload_updates}

    with pytest.raises(ValueError, match=expected_message):
        PaperTradeCostAuditReportDbRow(
            **{
                **row.__dict__,
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_db_row_rejects_nested_all_missing_hard_flags() -> None:
    row = paper_trade_cost_audit_report_to_db_row(_report())
    payload = {
        **row.payload_json,
        "source_report": {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "nested_report": {
                "generated_at": "2026-06-20T00:30:00+00:00",
                "config_version": "nested-v0",
                "reason_codes": [],
            },
        },
    }

    with pytest.raises(ValueError, match="nested_report paper_only"):
        PaperTradeCostAuditReportDbRow(
            **{
                **row.__dict__,
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_db_row_from_db_row_rejects_unchecked_raw_hash_bypass() -> None:
    row = paper_trade_cost_audit_report_to_db_row(_report())
    payload = {**row.payload_json, "fill_rate": "0.8000000"}
    malformed = _unchecked_row(
        row,
        report_sha256=_canonical_payload_sha256(payload),
        payload_json=payload,
    )

    with pytest.raises(ValueError, match="payload_json must be canonical|report_sha256"):
        paper_trade_cost_audit_report_from_db_row(malformed)


@pytest.mark.parametrize(
    "field_name",
    (
        "fill_rate",
        "mean_theoretical_edge",
        "mean_cost_adjusted_edge",
        "mean_edge_cost_drag",
        "total_edge_cost_drag",
        "mean_research_slippage",
        "largest_single_trade_cost_drag",
    ),
)
def test_db_row_rejects_positive_trade_count_rows_missing_required_metrics(
    field_name: str,
) -> None:
    row = paper_trade_cost_audit_report_to_db_row(_report())

    with pytest.raises(ValueError, match=field_name):
        replace(row, **{field_name: None})


@pytest.mark.parametrize(
    ("field_name", "updates"),
    (
        ("total_filled_size", {"total_filled_size": d("0")}),
        (
            "total_requested_size",
            {
                "total_filled_size": d("0"),
                "total_requested_size": d("0"),
                "fill_rate": d("0.000000"),
            },
        ),
    ),
)
def test_db_row_rejects_positive_trade_count_rows_without_positive_sizes(
    field_name: str,
    updates: dict[str, Decimal],
) -> None:
    row = paper_trade_cost_audit_report_to_db_row(_report())

    with pytest.raises(ValueError, match=field_name):
        replace(row, **updates)


def test_db_row_rejects_positive_trade_count_rows_with_mismatched_fill_rate() -> None:
    row = paper_trade_cost_audit_report_to_db_row(_report())

    with pytest.raises(ValueError, match="fill_rate"):
        replace(row, total_filled_size=d("250"), fill_rate=d("0.800000"))


def test_migration_enforces_positive_trade_count_shape_and_fill_rate_parity() -> None:
    body = _migration_table_body()

    expected_checks = (
        "check (trade_count = 0 or (total_filled_size > 0 and total_requested_size > 0 and fill_rate is not null and mean_theoretical_edge is not null and mean_cost_adjusted_edge is not null and mean_edge_cost_drag is not null and total_edge_cost_drag is not null and mean_research_slippage is not null and largest_single_trade_cost_drag is not null))",
        "check (trade_count = 0 or fill_rate = round(total_filled_size / nullif(total_requested_size, 0), 6))",
    )
    for check in expected_checks:
        assert check in body


def test_migration_uses_primary_key_without_redundant_report_sha256_unique_index() -> None:
    body = _migration_table_body()
    sql = _migration_sql()

    assert "report_sha256 text primary key" in body
    assert "create unique index if not exists idx_ptcar_report_sha256" not in sql
