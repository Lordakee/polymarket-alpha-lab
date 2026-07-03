from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.paper_recommendation_risk_budget import (
    PaperRecommendationRiskBudgetReport,
)


GENERATED_AT = datetime(2026, 6, 20, 15, 30, tzinfo=UTC)


class RiskBudgetReportSubclass(PaperRecommendationRiskBudgetReport):
    pass


def _codec_module():
    from polymarket_alpha_lab import paper_recommendation_risk_budget_db_row

    return paper_recommendation_risk_budget_db_row


def _report() -> PaperRecommendationRiskBudgetReport:
    return PaperRecommendationRiskBudgetReport(
        generated_at=GENERATED_AT,
        config_version="risk-budget-v0",
        status="pass",
        reason_codes=("risk_budget_passed",),
        total_suggested_notional=Decimal("90.000000"),
        remaining_total_notional=Decimal("160.000000"),
        total_notional_utilization=Decimal("0.090000"),
        largest_single_recommendation_share=Decimal("0.050000"),
        selected_count=2,
        blocked_count=0,
        max_total_utilization=Decimal("0.250000"),
        max_single_recommendation_share=Decimal("0.100000"),
        min_remaining_notional=Decimal("50.000000"),
        max_selected_count=3,
        selected_position_notional_values=(
            Decimal("50.000000"),
            Decimal("40.000000"),
        ),
        nav_notional=Decimal("1000.000000"),
    )


def _row_values(row: object) -> dict[str, object]:
    return dict(row.__dict__)


def _bypassed_row(codec: object, row: object, **overrides: object) -> object:
    row_type = codec.PaperRecommendationRiskBudgetDbRow
    bypassed = object.__new__(row_type)
    bypassed.__dict__.update({**_row_values(row), **overrides})
    return bypassed


def _payload_sha256(payload_json: dict[str, object]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _payload_copy(row: object) -> dict[str, object]:
    return json.loads(json.dumps(row.payload_json, allow_nan=False))


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("DB payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_risk_budget_db_row_serializes_canonical_payload_and_round_trips():
    codec = _codec_module()
    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperRecommendationRiskBudgetDbRow
    assert len(row.report_sha256) == 64
    assert row.report_sha256 == row.report_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "risk-budget-v0"
    assert row.status == "pass"
    assert row.reason_codes_json == ["risk_budget_passed"]
    assert row.total_suggested_notional == Decimal("90.000000")
    assert row.remaining_total_notional == Decimal("160.000000")
    assert row.total_notional_utilization == Decimal("0.090000")
    assert row.largest_single_recommendation_share == Decimal("0.050000")
    assert row.selected_count == 2
    assert row.blocked_count == 0
    assert row.nav_notional == Decimal("1000.000000")
    assert row.max_total_utilization == Decimal("0.250000")
    assert row.max_single_recommendation_share == Decimal("0.100000")
    assert row.min_remaining_notional == Decimal("50.000000")
    assert row.max_selected_count == 3
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json["generated_at"] == "2026-06-20T15:30:00+00:00"
    assert row.payload_json["total_suggested_notional"] == "90.000000"
    assert row.payload_json["total_notional_utilization"] == "0.090000"
    assert row.payload_json["selected_position_notional_values"] == [
        "50.000000",
        "40.000000",
    ]
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    _assert_no_floats(row.payload_json)

    assert row.report_sha256 == _payload_sha256(row.payload_json)
    assert codec.from_db_row(row) == report
    assert codec.paper_recommendation_risk_budget_to_db_row(report) == row
    assert codec.paper_recommendation_risk_budget_from_db_row(row) == report


def test_risk_budget_db_row_normalizes_generated_at_to_utc_in_row_and_payload():
    codec = _codec_module()
    report = _report()
    naive_generated_at = datetime(2026, 6, 20, 15, 30)
    object.__setattr__(report, "generated_at", naive_generated_at)

    row = codec.to_db_row(report)

    assert row.generated_at == GENERATED_AT
    assert row.payload_json["generated_at"] == "2026-06-20T15:30:00+00:00"
    assert codec.from_db_row(row).generated_at == GENERATED_AT


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("total_suggested_notional", 90),
        ("remaining_total_notional", "160.000000"),
        ("total_notional_utilization", "0.090000"),
        ("largest_single_recommendation_share", 0.05),
        ("nav_notional", "1000.000000"),
        ("max_total_utilization", "0.250000"),
        ("max_single_recommendation_share", 0.1),
        ("min_remaining_notional", "50.000000"),
    ),
)
def test_risk_budget_db_row_requires_materialized_decimal_fields_to_be_raw_decimals(
    field_name: str,
    value: object,
):
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=field_name):
        codec.PaperRecommendationRiskBudgetDbRow(
            **{**_row_values(row), field_name: value},
        )


def test_risk_budget_db_row_redacts_secret_like_payload_values():
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload_json = {
        **row.payload_json,
        "audit_metadata": {
            "supabase_url": "http://localhost:54321",
            "supabase_service_role_key": "secret-service-role",
            "postgres_password": "secret-password",
        },
    }

    sanitized = codec.PaperRecommendationRiskBudgetDbRow(
        **{
            **_row_values(row),
            "report_sha256": _payload_sha256(
                {
                    **row.payload_json,
                    "audit_metadata": {
                        "supabase_url": "http://localhost:54321",
                        "supabase_service_role_key": "[REDACTED]",
                        "postgres_password": "[REDACTED]",
                    },
                },
            ),
            "payload_json": payload_json,
        },
    )

    assert sanitized.payload_json["audit_metadata"] == {
        "supabase_url": "http://localhost:54321",
        "supabase_service_role_key": "[REDACTED]",
        "postgres_password": "[REDACTED]",
    }
    assert "secret" not in json.dumps(sanitized.payload_json).lower()


@pytest.mark.parametrize(
    "storage_value",
    (
        "https://project.supabase.co",
        "http://localhost.evil.com/project.supabase.co",
        "postgres://user:pass@db.example.com:5432/postgres",
        "postgres://localhost.evil.com/db",
    ),
)
def test_risk_budget_db_row_rejects_remote_supabase_and_postgres_payload_assumptions(
    storage_value: str,
):
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload_json = {**row.payload_json, "storage_assumption": storage_value}

    with pytest.raises(ValueError, match="local|Supabase|Postgres"):
        codec.PaperRecommendationRiskBudgetDbRow(
            **{
                **_row_values(row),
                "report_sha256": _payload_sha256(payload_json),
                "payload_json": payload_json,
            },
        )


@pytest.mark.parametrize(
    "storage_value",
    (
        "http://localhost:54321/project.supabase.local",
        "http://127.0.0.1:54321/project.supabase.local",
        "postgres://localhost:5432/postgres",
        "postgresql://127.0.0.1:5432/postgres",
    ),
)
def test_risk_budget_db_row_accepts_local_supabase_and_postgres_payload_assumptions(
    storage_value: str,
):
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload_json = {**row.payload_json, "storage_assumption": storage_value}

    sanitized = codec.PaperRecommendationRiskBudgetDbRow(
        **{
            **_row_values(row),
            "report_sha256": _payload_sha256(payload_json),
            "payload_json": payload_json,
        },
    )

    assert sanitized.payload_json["storage_assumption"] == storage_value


@pytest.mark.parametrize(
    ("field_name", "terse_value", "fixed_value"),
    (
        ("total_suggested_notional", "90", "90.000000"),
        ("remaining_total_notional", "160", "160.000000"),
        ("total_notional_utilization", "0.09", "0.090000"),
        ("largest_single_recommendation_share", "0.05", "0.050000"),
        ("nav_notional", "1000", "1000.000000"),
        ("max_total_utilization", "0.25", "0.250000"),
        ("max_single_recommendation_share", "0.1", "0.100000"),
        ("min_remaining_notional", "50", "50.000000"),
    ),
)
def test_risk_budget_db_row_writes_fixed_six_place_decimal_payload_strings(
    field_name: str,
    terse_value: str,
    fixed_value: str,
):
    codec = _codec_module()
    terse_report = _report()
    fixed_report = _report()
    object.__setattr__(terse_report, field_name, Decimal(terse_value))
    object.__setattr__(fixed_report, field_name, Decimal(fixed_value))

    terse_row = codec.to_db_row(terse_report)
    fixed_row = codec.to_db_row(fixed_report)

    assert terse_row.payload_json[field_name] == fixed_value
    assert terse_row.payload_json == fixed_row.payload_json
    assert terse_row.report_sha256 == fixed_row.report_sha256


def test_risk_budget_db_row_writes_fixed_six_place_selected_notional_values():
    codec = _codec_module()
    terse_report = _report()
    fixed_report = _report()
    object.__setattr__(
        terse_report,
        "selected_position_notional_values",
        (Decimal("50"), Decimal("40")),
    )
    object.__setattr__(
        fixed_report,
        "selected_position_notional_values",
        (Decimal("50.000000"), Decimal("40.000000")),
    )

    terse_row = codec.to_db_row(terse_report)
    fixed_row = codec.to_db_row(fixed_report)

    assert terse_row.payload_json["selected_position_notional_values"] == [
        "50.000000",
        "40.000000",
    ]
    assert terse_row.payload_json == fixed_row.payload_json
    assert terse_row.report_sha256 == fixed_row.report_sha256


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("total_suggested_notional", "90.0000001"),
        ("total_notional_utilization", "0.0900001"),
    ),
)
def test_risk_budget_db_row_rejects_overprecision_decimal_writes_without_rounding(
    field_name: str,
    value: str,
):
    codec = _codec_module()
    report = _report()
    object.__setattr__(report, field_name, Decimal(value))

    with pytest.raises(ValueError, match=f"{field_name}|six decimal|quantized"):
        codec.to_db_row(report)


def test_risk_budget_db_row_hash_is_deterministic_for_equivalent_reports():
    codec = _codec_module()
    report = _report()
    same_report = PaperRecommendationRiskBudgetReport(**report.__dict__)
    different_report = PaperRecommendationRiskBudgetReport(
        **{**report.__dict__, "config_version": "risk-budget-v1"},
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_risk_budget_from_db_row_accepts_self_hashed_legacy_decimal_payload_strings():
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload_json = _payload_copy(row)
    payload_json["total_suggested_notional"] = "90"
    payload_json["remaining_total_notional"] = "160"
    payload_json["total_notional_utilization"] = "0.09"
    payload_json["largest_single_recommendation_share"] = "0.05"
    payload_json["selected_position_notional_values"] = ["50", "40.0"]
    payload_json["nav_notional"] = "1000"
    payload_json["max_total_utilization"] = "0.25"
    payload_json["max_single_recommendation_share"] = "0.1"
    payload_json["min_remaining_notional"] = "50"
    legacy_row = _bypassed_row(
        codec,
        row,
        report_sha256=_payload_sha256(payload_json),
        total_suggested_notional=Decimal("90"),
        remaining_total_notional=Decimal("160"),
        total_notional_utilization=Decimal("0.09"),
        largest_single_recommendation_share=Decimal("0.05"),
        nav_notional=Decimal("1000"),
        max_total_utilization=Decimal("0.25"),
        max_single_recommendation_share=Decimal("0.1"),
        min_remaining_notional=Decimal("50"),
        payload_json=payload_json,
    )

    assert codec.from_db_row(legacy_row) == _report()


def test_risk_budget_from_db_row_validates_raw_hash_before_legacy_normalization():
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload_json = _payload_copy(row)
    payload_json["total_suggested_notional"] = "90"
    stale_row = _bypassed_row(codec, row, payload_json=payload_json)

    with pytest.raises(ValueError, match="report_sha256"):
        codec.from_db_row(stale_row)


@pytest.mark.parametrize(
    ("field_name", "legacy_value"),
    (
        ("total_suggested_notional", "90.000001"),
        ("total_notional_utilization", "0.090001"),
    ),
)
def test_risk_budget_from_db_row_rejects_value_changing_legacy_decimal_payloads(
    field_name: str,
    legacy_value: str,
):
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload_json = _payload_copy(row)
    payload_json[field_name] = legacy_value
    malformed = _bypassed_row(
        codec,
        row,
        report_sha256=_payload_sha256(payload_json),
        payload_json=payload_json,
    )

    with pytest.raises(ValueError, match=field_name):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("field_name", "legacy_value"),
    (
        ("total_suggested_notional", "90.0000001"),
        ("total_notional_utilization", "0.0900001"),
    ),
)
def test_risk_budget_from_db_row_rejects_overprecision_legacy_decimal_payloads(
    field_name: str,
    legacy_value: str,
):
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload_json = _payload_copy(row)
    payload_json[field_name] = legacy_value
    malformed = _bypassed_row(
        codec,
        row,
        report_sha256=_payload_sha256(payload_json),
        payload_json=payload_json,
    )

    with pytest.raises(ValueError, match=f"{field_name}|six decimal"):
        codec.from_db_row(malformed)


def test_risk_budget_from_db_row_rejects_non_allowlisted_decimal_like_payloads():
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload_json = _payload_copy(row)
    payload_json["selected_count"] = "2.0"
    malformed = _bypassed_row(
        codec,
        row,
        report_sha256=_payload_sha256(payload_json),
        payload_json=payload_json,
    )

    with pytest.raises(ValueError, match="selected_count|payload_json"):
        codec.from_db_row(malformed)


def test_risk_budget_db_row_is_frozen():
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_risk_budget_db_row_rejects_wrong_report_types_and_subclasses():
    codec = _codec_module()

    with pytest.raises(ValueError, match="PaperRecommendationRiskBudgetReport"):
        codec.to_db_row(object())

    report = _report()
    with pytest.raises(ValueError, match="PaperRecommendationRiskBudgetReport"):
        codec.to_db_row(RiskBudgetReportSubclass(**report.__dict__))


def test_risk_budget_db_row_rejects_wrong_row_types_and_subclasses():
    codec = _codec_module()
    row = codec.to_db_row(_report())

    class RiskBudgetDbRowSubclass(codec.PaperRecommendationRiskBudgetDbRow):
        pass

    with pytest.raises(ValueError, match="PaperRecommendationRiskBudgetDbRow"):
        codec.from_db_row(object())
    with pytest.raises(ValueError, match="PaperRecommendationRiskBudgetDbRow"):
        codec.from_db_row(RiskBudgetDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_risk_budget_db_row_rejects_false_report_flags_before_write(
    flag_name: str,
):
    codec = _codec_module()
    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_risk_budget_db_row_constructor_rejects_top_level_payload_hard_flag_mismatch(
    flag_name: str,
):
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload_json = {**row.payload_json, flag_name: False}

    with pytest.raises(ValueError, match=flag_name):
        codec.PaperRecommendationRiskBudgetDbRow(
            **{
                **_row_values(row),
                "report_sha256": _payload_sha256(payload_json),
                "payload_json": payload_json,
            },
        )


def test_risk_budget_db_row_constructor_rejects_corrupted_nested_payload_flags():
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload_json = {
        **row.payload_json,
        "nested_audit": {"paper_only": True, "report_only": True, "readonly": False},
    }

    with pytest.raises(ValueError, match="readonly"):
        codec.PaperRecommendationRiskBudgetDbRow(
            **{
                **_row_values(row),
                "report_sha256": _payload_sha256(payload_json),
                "payload_json": payload_json,
            },
        )


def test_risk_budget_db_row_rejects_floats_in_json_payloads():
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="payload_json"):
        codec.PaperRecommendationRiskBudgetDbRow(
            **{**_row_values(row), "payload_json": {**row.payload_json, "bad_float": 0.1}},
        )


@pytest.mark.parametrize(
    ("field_name", "raw_value"),
    (
        ("total_suggested_notional", Decimal("90.000000")),
        ("generated_at", GENERATED_AT),
    ),
)
def test_risk_budget_db_row_constructor_rejects_raw_runtime_payload_values(
    field_name: str,
    raw_value: object,
):
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload_json = {**row.payload_json, field_name: raw_value}

    with pytest.raises(ValueError, match="payload_json"):
        codec.PaperRecommendationRiskBudgetDbRow(
            **{**_row_values(row), "payload_json": payload_json},
        )


@pytest.mark.parametrize(
    ("field_name", "raw_value"),
    (
        ("total_suggested_notional", Decimal("90.000000")),
        ("generated_at", GENERATED_AT),
        ("bad_float", 0.1),
    ),
)
def test_risk_budget_from_db_row_rejects_bypassed_raw_runtime_payload_values(
    field_name: str,
    raw_value: object,
):
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload_json = {**row.payload_json, field_name: raw_value}
    malformed = _bypassed_row(codec, row, payload_json=payload_json)

    with pytest.raises(ValueError, match="payload_json"):
        codec.from_db_row(malformed)


def test_risk_budget_db_row_from_db_row_rejects_bypassed_malformed_stored_payload():
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = _bypassed_row(
        codec,
        row,
        payload_json={
            key: value for key, value in row.payload_json.items() if key != "reason_codes"
        },
    )

    with pytest.raises(ValueError, match="payload_json"):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 20, 15, 31, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "risk-budget-v1"}, "config_version"),
        ({"status": "watch"}, "status"),
        ({"reason_codes_json": ["near_total_utilization_cap"]}, "reason_codes_json"),
        ({"total_suggested_notional": Decimal("91.000000")}, "total_suggested"),
        ({"remaining_total_notional": Decimal("159.000000")}, "remaining_total"),
        ({"total_notional_utilization": Decimal("0.091000")}, "total_notional"),
        (
            {"largest_single_recommendation_share": Decimal("0.060000")},
            "largest_single",
        ),
        ({"selected_count": 3}, "selected_count"),
        ({"blocked_count": 1}, "blocked_count"),
        ({"nav_notional": Decimal("999.000000")}, "nav_notional"),
        ({"max_total_utilization": Decimal("0.300000")}, "max_total"),
        (
            {"max_single_recommendation_share": Decimal("0.200000")},
            "max_single",
        ),
        ({"min_remaining_notional": Decimal("40.000000")}, "min_remaining"),
        ({"max_selected_count": 4}, "max_selected_count"),
    ),
)
def test_risk_budget_db_row_constructor_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
):
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperRecommendationRiskBudgetDbRow(
            **{**_row_values(row), **overrides},
        )


def test_risk_budget_db_row_constructor_rejects_none_materialized_payload_mismatch():
    codec = _codec_module()
    report = PaperRecommendationRiskBudgetReport(
        **{
            **_report().__dict__,
            "total_suggested_notional": Decimal("0.000000"),
            "remaining_total_notional": None,
            "total_notional_utilization": None,
            "largest_single_recommendation_share": None,
            "selected_position_notional_values": (),
            "selected_count": 0,
            "blocked_count": 1,
            "status": "blocked",
            "reason_codes": ("empty_selection",),
            "nav_notional": None,
        },
    )
    row = codec.to_db_row(report)

    with pytest.raises(ValueError, match="remaining_total_notional"):
        codec.PaperRecommendationRiskBudgetDbRow(
            **{
                **_row_values(row),
                "remaining_total_notional": Decimal("0.000000"),
            },
        )


def test_risk_budget_db_row_constructor_rejects_missing_none_payload_field():
    codec = _codec_module()
    report = PaperRecommendationRiskBudgetReport(
        **{
            **_report().__dict__,
            "total_suggested_notional": Decimal("0.000000"),
            "remaining_total_notional": None,
            "total_notional_utilization": None,
            "largest_single_recommendation_share": None,
            "selected_position_notional_values": (),
            "selected_count": 0,
            "blocked_count": 1,
            "status": "blocked",
            "reason_codes": ("empty_selection",),
            "nav_notional": None,
        },
    )
    row = codec.to_db_row(report)
    payload_json = {
        key: value
        for key, value in row.payload_json.items()
        if key != "remaining_total_notional"
    }

    with pytest.raises(ValueError, match="remaining_total_notional"):
        codec.PaperRecommendationRiskBudgetDbRow(
            **{
                **_row_values(row),
                "report_sha256": _payload_sha256(payload_json),
                "payload_json": payload_json,
            },
        )


def test_risk_budget_db_row_from_db_row_rejects_bypassed_materialized_mismatch():
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = _bypassed_row(codec, row, status="watch")

    with pytest.raises(ValueError, match="status"):
        codec.from_db_row(malformed)


def test_risk_budget_db_row_from_db_row_rejects_bypassed_nested_payload_hard_flag():
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload_json = {
        **row.payload_json,
        "nested_audit": {"paper_only": True, "report_only": True, "readonly": False},
    }
    malformed = _bypassed_row(
        codec,
        row,
        report_sha256=_payload_sha256(payload_json),
        payload_json=payload_json,
    )

    with pytest.raises(ValueError, match="readonly"):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"total_suggested_notional": 90.0}, "total_suggested_notional"),
        ({"total_notional_utilization": Decimal("0.0900001")}, "total_notional"),
        ({"selected_count": True}, "selected_count"),
        ({"paper_only": False}, "paper_only"),
    ),
)
def test_risk_budget_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
):
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperRecommendationRiskBudgetDbRow(
            **{**_row_values(row), **overrides},
        )


def test_risk_budget_db_row_module_is_pure_codec():
    _codec_module()
    source = Path(
        "src/polymarket_alpha_lab/paper_recommendation_risk_budget_db_row.py",
    ).read_text(encoding="utf-8")

    for banned in (
        "psycopg",
        "sql",
        "network",
        "client",
        "auth",
        "wallet",
        "account",
        "signing",
        "submission",
        "cancellation",
        "replacement",
        "exchange",
        "live_trading",
    ):
        assert banned not in source.lower()
