from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
import re

import pytest

from tests.test_paper_autonomous_investment_ledger_db_history_health import (
    GENERATED_AT,
    _health_report,
    _ledger_report,
    d,
)


SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def _db_row():
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    return codec.to_db_row(_report())


def _report():
    return _health_report(
        (
            _ledger_report(
                latest_generated_at=GENERATED_AT - timedelta(seconds=1_800),
                total_submitted_notional=d("10.000000"),
            ),
            _ledger_report(
                latest_generated_at=GENERATED_AT - timedelta(seconds=1_200),
                total_submitted_notional=d("15.500000"),
            ),
            _ledger_report(
                latest_generated_at=GENERATED_AT - timedelta(seconds=600),
                total_submitted_notional=d("42.250000"),
            ),
        ),
    )


def _empty_report():
    return _health_report(())


def _row_values(row: object) -> dict[str, object]:
    return dict(row.__dict__)


def _bypassed_row(row: object, overrides: dict[str, object]) -> object:
    bypassed = object.__new__(type(row))
    for field_name, value in {**_row_values(row), **overrides}.items():
        object.__setattr__(bypassed, field_name, value)
    return bypassed


def _canonical_payload_sha256(payload_json: dict[str, object]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("health DB JSON contains floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def _without_hard_flags(value: dict[str, object]) -> dict[str, object]:
    return {
        key: item
        for key, item in value.items()
        if key not in {"paper_only", "report_only", "readonly"}
    }


def test_health_db_row_serializes_payload_and_round_trips() -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow
    assert SHA256_RE.fullmatch(row.report_sha256)
    assert row.generated_at == GENERATED_AT
    assert row.config_version == (
        "paper-autonomous-investment-ledger-db-history-health-v0"
    )
    assert row.health_status == "pass"
    assert row.recommended_next_step == (
        "allow_paper_autonomous_investment_ledger_review"
    )
    assert row.ledger_report_count == 3
    assert row.pass_ledger_report_count == 3
    assert row.watch_ledger_report_count == 0
    assert row.blocked_ledger_report_count == 0
    assert row.latest_ledger_status == "pass"
    assert row.latest_source_record_count == 1
    assert row.latest_submitted_count == 1
    assert row.latest_held_count == 0
    assert row.latest_blocked_count == 0
    assert row.latest_total_submitted_notional == d("42.250000")
    assert type(row.latest_total_submitted_notional) is Decimal
    assert row.latest_source_generated_at == GENERATED_AT - timedelta(seconds=600)
    assert row.latest_source_age_seconds == 600
    assert row.max_source_age_seconds == 1_800
    assert row.duplicate_latest_generated_at_count == 0
    assert row.reason_codes_json == [
        "paper_autonomous_investment_ledger_db_history_health_passed",
    ]
    assert row.reason_code_counts_json == [
        {
            "reason_code": "paper_autonomous_investment_ledger_passed",
            "report_count": 3,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json["generated_at"] == "2026-06-25T18:00:00+00:00"
    assert row.payload_json["latest_total_submitted_notional"] == "42.250000"
    assert row.payload_json["latest_source_generated_at"] == "2026-06-25T17:50:00+00:00"
    assert row.payload_json["reason_code_counts"][0]["readonly"] is True
    _assert_no_floats(row.reason_code_counts_json)
    _assert_no_floats(row.reason_codes_json)
    _assert_no_floats(row.payload_json)

    assert row.report_sha256 == _canonical_payload_sha256(row.payload_json)
    assert codec.from_db_row(row) == report
    assert (
        codec.paper_autonomous_investment_ledger_db_history_health_report_to_db_row(
            report,
        )
        == row
    )
    assert (
        codec.paper_autonomous_investment_ledger_db_history_health_report_from_db_row(
            row,
        )
        == report
    )


def test_health_db_row_writes_decimal_payloads_as_fixed_six_place_strings() -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    report = replace(_report(), latest_total_submitted_notional=Decimal("42.25"))

    row = codec.to_db_row(report)

    assert row.latest_total_submitted_notional == Decimal("42.250000")
    assert str(row.latest_total_submitted_notional) == "42.250000"
    assert row.payload_json["latest_total_submitted_notional"] == "42.250000"
    assert row.report_sha256 == _canonical_payload_sha256(row.payload_json)

    explicit_row = replace(row, latest_total_submitted_notional=Decimal("42.25"))
    assert explicit_row.latest_total_submitted_notional == Decimal("42.250000")
    assert str(explicit_row.latest_total_submitted_notional) == "42.250000"


def test_health_db_row_recovers_legacy_self_hashed_decimal_payloads() -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    row = _db_row()
    payload = {
        **row.payload_json,
        "latest_total_submitted_notional": "42.25",
    }

    legacy_row = codec.PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow(
        **{
            **_row_values(row),
            "report_sha256": _canonical_payload_sha256(payload),
            "latest_total_submitted_notional": Decimal("42.25"),
            "payload_json": payload,
        },
    )

    assert legacy_row.payload_json["latest_total_submitted_notional"] == "42.25"
    report = codec.from_db_row(legacy_row)
    assert report == _report()
    assert str(report.latest_total_submitted_notional) == "42.250000"


def test_health_db_row_rejects_stale_legacy_decimal_payload_hashes() -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    row = _db_row()
    payload = {
        **row.payload_json,
        "latest_total_submitted_notional": "42.25",
    }

    malformed = _bypassed_row(
        row,
        {
            "latest_total_submitted_notional": Decimal("42.25"),
            "payload_json": payload,
        },
    )

    with pytest.raises(ValueError, match="report_sha256"):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    "payload_value",
    (
        "42.250001",
        "42.2500001",
    ),
)
def test_health_db_row_rejects_value_changing_or_overprecision_decimal_payloads(
    payload_value: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    row = _db_row()
    payload = {
        **row.payload_json,
        "latest_total_submitted_notional": payload_value,
    }
    malformed = _bypassed_row(
        row,
        {
            "report_sha256": _canonical_payload_sha256(payload),
            "payload_json": payload,
        },
    )

    with pytest.raises(ValueError, match="latest_total_submitted_notional|payload_json"):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("field_name", "payload_value"),
    (
        ("config_version", "42.25"),
        ("generated_at", "2026.000000"),
        ("reason_codes", ["paper_autonomous_investment_ledger_db_history_health_passed", "1.000000"]),
        (
            "reason_code_counts",
            [
                {
                    "reason_code": "paper_autonomous_investment_ledger_passed",
                    "report_count": "3.000000",
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            ],
        ),
    ),
)
def test_health_db_row_rejects_non_allowlisted_decimal_like_payloads(
    field_name: str,
    payload_value: object,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    row = _db_row()
    payload = {**row.payload_json, field_name: payload_value}
    malformed = _bypassed_row(
        row,
        {
            "report_sha256": _canonical_payload_sha256(payload),
            "payload_json": payload,
        },
    )

    with pytest.raises(ValueError, match=field_name):
        codec.from_db_row(malformed)


def test_health_db_row_rejects_matching_non_allowlisted_decimal_like_payloads() -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    row = _db_row()
    payload = {**row.payload_json, "config_version": "42.25"}
    malformed = _bypassed_row(
        row,
        {
            "report_sha256": _canonical_payload_sha256(payload),
            "config_version": "42.25",
            "payload_json": payload,
        },
    )

    with pytest.raises(ValueError, match="config_version"):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("field_name", "payload_value", "message"),
    (
        ("latest_total_submitted_notional", 42.25, "float"),
        ("latest_total_submitted_notional", Decimal("42.250000"), "raw Decimal"),
        ("generated_at", GENERATED_AT, "raw datetime"),
    ),
)
def test_health_db_row_rejects_raw_json_payload_values(
    field_name: str,
    payload_value: object,
    message: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    row = _db_row()
    payload = {**row.payload_json, field_name: payload_value}
    malformed = _bypassed_row(
        row,
        {
            "report_sha256": row.report_sha256,
            "payload_json": payload,
        },
    )

    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)


def test_health_db_row_hash_is_deterministic_for_equivalent_reports() -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec
    from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health import (
        PaperAutonomousInvestmentLedgerDbHistoryHealthReport,
    )

    report = _report()
    same_report = PaperAutonomousInvestmentLedgerDbHistoryHealthReport(
        **report.__dict__,
    )
    different_report = _health_report(
        (
            _ledger_report(
                latest_generated_at=GENERATED_AT - timedelta(seconds=2_400),
            ),
            _ledger_report(
                latest_generated_at=GENERATED_AT - timedelta(seconds=1_200),
            ),
            _ledger_report(
                latest_generated_at=GENERATED_AT - timedelta(seconds=600),
            ),
        ),
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_health_db_row_is_frozen() -> None:
    row = _db_row()

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_health_db_row_rejects_wrong_report_types_and_blocks_subclasses() -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec
    from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health import (
        PaperAutonomousInvestmentLedgerDbHistoryHealthReport,
    )

    with pytest.raises(ValueError, match="PaperAutonomousInvestmentLedgerDbHistoryHealthReport"):
        codec.to_db_row(object())

    with pytest.raises(TypeError, match="HealthReport .*subclassing"):
        class ReportSubclass(PaperAutonomousInvestmentLedgerDbHistoryHealthReport):
            pass


def test_health_db_row_rejects_wrong_row_types_and_subclasses() -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    row = _db_row()

    class HealthDbRowSubclass(codec.PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow):
        pass

    with pytest.raises(ValueError, match="PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow"):
        codec.from_db_row(object())
    with pytest.raises(ValueError, match="PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow"):
        codec.from_db_row(HealthDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_health_db_row_rejects_false_report_flags_before_write(
    flag_name: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_health_db_row_rejects_false_nested_reason_count_flags() -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    report = _report()
    object.__setattr__(report.reason_code_counts[0], "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        codec.to_db_row(report)


def test_health_db_row_rejects_corrupted_stored_payload_flags() -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    row = _db_row()
    reason_code_counts = [
        {
            **row.payload_json["reason_code_counts"][0],
            "paper_only": False,
        },
    ]
    payload = {**row.payload_json, "reason_code_counts": reason_code_counts}

    with pytest.raises(ValueError, match="paper_only"):
        codec.PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
                "reason_code_counts_json": reason_code_counts,
            },
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(
            row,
            report_sha256=_canonical_payload_sha256(payload),
            payload_json=payload,
            reason_code_counts_json=reason_code_counts,
        )
    malformed = _bypassed_row(
        row,
        {
            "report_sha256": _canonical_payload_sha256(payload),
            "payload_json": payload,
            "reason_code_counts_json": reason_code_counts,
        },
    )
    with pytest.raises(ValueError, match="paper_only"):
        codec.from_db_row(malformed)


def test_health_db_row_rejects_missing_nested_reason_count_flags() -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    row = _db_row()
    reason_code_counts = [
        {
            key: value
            for key, value in reason_count.items()
            if key not in {"paper_only", "report_only", "readonly"}
        }
        for reason_count in row.reason_code_counts_json
    ]
    payload = {**row.payload_json, "reason_code_counts": reason_code_counts}
    report_sha256 = _canonical_payload_sha256(payload)

    with pytest.raises(ValueError, match="reason_code_counts.*paper_only"):
        codec.PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow(
            **{
                **_row_values(row),
                "report_sha256": report_sha256,
                "payload_json": payload,
                "reason_code_counts_json": reason_code_counts,
            },
        )
    with pytest.raises(ValueError, match="reason_code_counts.*paper_only"):
        replace(
            row,
            report_sha256=report_sha256,
            payload_json=payload,
            reason_code_counts_json=reason_code_counts,
        )
    malformed = _bypassed_row(
        row,
        {
            "report_sha256": report_sha256,
            "payload_json": payload,
            "reason_code_counts_json": reason_code_counts,
        },
    )
    with pytest.raises(ValueError, match="reason_code_counts.*paper_only"):
        codec.from_db_row(malformed)


def test_health_db_row_rejects_all_missing_nested_materialized_flags() -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    row = _db_row()
    reason_code_counts = [
        _without_hard_flags(row.reason_code_counts_json[0]),
        *row.reason_code_counts_json[1:],
    ]

    with pytest.raises(ValueError, match="reason_code_counts_json.*paper_only"):
        codec.PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow(
            **{**_row_values(row), "reason_code_counts_json": reason_code_counts},
        )
    with pytest.raises(ValueError, match="reason_code_counts_json.*paper_only"):
        replace(row, reason_code_counts_json=reason_code_counts)


def test_health_db_row_rejects_non_materialized_payload_hash_mismatch() -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    row = _db_row()
    payload = {**row.payload_json, "paper_only": False}

    with pytest.raises(ValueError, match="report_sha256"):
        codec.PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow(
            **{**_row_values(row), "payload_json": payload},
        )
    with pytest.raises(ValueError, match="report_sha256"):
        replace(row, payload_json=payload)
    malformed = _bypassed_row(row, {"payload_json": payload})
    with pytest.raises(ValueError, match="report_sha256"):
        codec.from_db_row(malformed)


def test_health_db_row_rejects_missing_nullable_payload_keys() -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    row = codec.to_db_row(_empty_report())
    payload = {
        key: value
        for key, value in row.payload_json.items()
        if key != "latest_total_submitted_notional"
    }
    report_sha256 = _canonical_payload_sha256(payload)

    with pytest.raises(ValueError, match="latest_total_submitted_notional"):
        codec.PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow(
            **{
                **_row_values(row),
                "report_sha256": report_sha256,
                "payload_json": payload,
            },
        )
    malformed = _bypassed_row(
        row,
        {"report_sha256": report_sha256, "payload_json": payload},
    )
    with pytest.raises(ValueError, match="latest_total_submitted_notional"):
        codec.from_db_row(malformed)


def test_health_db_row_rejects_bool_for_int_payload_values_strictly() -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    row = _db_row()
    payload = {**row.payload_json, "latest_source_record_count": True}
    report_sha256 = _canonical_payload_sha256(payload)

    with pytest.raises(ValueError, match="latest_source_record_count"):
        codec.PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow(
            **{
                **_row_values(row),
                "report_sha256": report_sha256,
                "payload_json": payload,
            },
        )
    malformed = _bypassed_row(
        row,
        {"report_sha256": report_sha256, "payload_json": payload},
    )
    with pytest.raises(ValueError, match="latest_source_record_count"):
        codec.from_db_row(malformed)


def test_health_db_row_rejects_noncanonical_decimal_payload_strings() -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    row = _db_row()
    payload = {
        **row.payload_json,
        "latest_total_submitted_notional": "42.2500000",
    }
    report_sha256 = _canonical_payload_sha256(payload)

    with pytest.raises(ValueError, match="latest_total_submitted_notional"):
        codec.PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow(
            **{
                **_row_values(row),
                "report_sha256": report_sha256,
                "latest_total_submitted_notional": Decimal("42.2500000"),
                "payload_json": payload,
            },
        )
    malformed = _bypassed_row(
        row,
        {
            "report_sha256": report_sha256,
            "latest_total_submitted_notional": Decimal("42.2500000"),
            "payload_json": payload,
        },
    )
    with pytest.raises(ValueError, match="payload_json|latest_total_submitted_notional"):
        codec.from_db_row(malformed)


def test_health_db_row_rejects_recursive_floats_in_json_payloads() -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    row = _db_row()

    with pytest.raises(ValueError, match="reason_code_counts_json"):
        replace(
            row,
            reason_code_counts_json=[
                {**row.reason_code_counts_json[0], "report_count": 1.0},
            ],
        )
    with pytest.raises(ValueError, match="reason_codes_json"):
        replace(row, reason_codes_json=["reason", 1.0])
    with pytest.raises(ValueError, match="payload_json"):
        replace(row, payload_json={**row.payload_json, "bad_float": 0.1})


def test_health_db_row_round_trips_empty_health_reports_with_nullable_latest_fields() -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    report = _empty_report()

    row = codec.to_db_row(report)

    assert row.ledger_report_count == 0
    assert row.health_status == "blocked"
    assert row.latest_ledger_status is None
    assert row.latest_source_record_count is None
    assert row.latest_submitted_count is None
    assert row.latest_held_count is None
    assert row.latest_blocked_count is None
    assert row.latest_total_submitted_notional is None
    assert row.latest_source_generated_at is None
    assert row.latest_source_age_seconds is None
    assert row.max_source_age_seconds is None
    assert row.reason_code_counts_json == []
    assert codec.from_db_row(row) == report


def test_health_db_row_normalizes_aware_datetimes_to_utc() -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    row = codec.to_db_row(_report())
    offset_row = replace(
        row,
        generated_at=datetime(2026, 6, 25, 14, 0, tzinfo=timezone(timedelta(hours=-4))),
        latest_source_generated_at=datetime(
            2026,
            6,
            25,
            13,
            50,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert offset_row.generated_at == GENERATED_AT
    assert offset_row.latest_source_generated_at == GENERATED_AT - timedelta(seconds=600)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": GENERATED_AT + timedelta(seconds=1)}, "generated_at"),
        (
            {"config_version": "paper-autonomous-investment-ledger-db-history-health-v1"},
            "config_version",
        ),
        (
            {
                "health_status": "watch",
                "recommended_next_step": (
                    "throttle_paper_autonomous_investment_ledger_review"
                ),
            },
            "health_status",
        ),
        (
            {"ledger_report_count": 4, "pass_ledger_report_count": 4},
            "ledger_report_count",
        ),
        ({"pass_ledger_report_count": 2, "watch_ledger_report_count": 1}, "pass_ledger_report_count"),
        ({"latest_ledger_status": "watch"}, "latest_ledger_status"),
        ({"latest_source_record_count": 2}, "latest_source_record_count"),
        ({"latest_submitted_count": 2}, "latest_submitted_count"),
        ({"latest_held_count": 1}, "latest_held_count"),
        ({"latest_blocked_count": 1}, "latest_blocked_count"),
        (
            {"latest_total_submitted_notional": d("41.000000")},
            "latest_total_submitted_notional",
        ),
        (
            {"latest_source_generated_at": GENERATED_AT - timedelta(seconds=601)},
            "latest_source_generated_at",
        ),
        ({"latest_source_age_seconds": 599}, "latest_source_age_seconds"),
        ({"max_source_age_seconds": 1_799}, "max_source_age_seconds"),
        (
            {"duplicate_latest_generated_at_count": 1},
            "duplicate_latest_generated_at_count",
        ),
        ({"reason_codes_json": ["stale_investment_ledger_db_history"]}, "reason_codes_json"),
        ({"reason_code_counts_json": []}, "reason_code_counts_json"),
    ),
)
def test_health_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    row = _db_row()

    with pytest.raises(ValueError, match=message):
        codec.PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow(
            **{**_row_values(row), **overrides},
        )
    with pytest.raises(ValueError, match=message):
        replace(row, **overrides)
    malformed = _bypassed_row(row, overrides)
    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("status", "next_step"),
    (
        ("pass", "throttle_paper_autonomous_investment_ledger_review"),
        ("watch", "allow_paper_autonomous_investment_ledger_review"),
        ("blocked", "throttle_paper_autonomous_investment_ledger_review"),
    ),
)
def test_health_db_row_rejects_health_status_next_step_mismatches(
    status: str,
    next_step: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    with pytest.raises(ValueError, match="recommended_next_step"):
        codec.PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow(
            **{
                **_row_values(_db_row()),
                "health_status": status,
                "recommended_next_step": next_step,
            },
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 25, 18, 0)}, "generated_at"),
        ({"config_version": ""}, "config_version"),
        ({"health_status": "paused"}, "health_status"),
        ({"ledger_report_count": True}, "ledger_report_count"),
        ({"ledger_report_count": -1}, "ledger_report_count"),
        ({"pass_ledger_report_count": 2}, "ledger_report_count"),
        ({"latest_ledger_status": "paused"}, "latest_ledger_status"),
        ({"latest_source_record_count": -1}, "latest_source_record_count"),
        ({"latest_submitted_count": True}, "latest_submitted_count"),
        ({"latest_held_count": -1}, "latest_held_count"),
        ({"latest_blocked_count": -1}, "latest_blocked_count"),
        (
            {"latest_total_submitted_notional": d("-1.000000")},
            "latest_total_submitted_notional",
        ),
        (
            {"latest_source_generated_at": datetime(2026, 6, 25, 17, 50)},
            "latest_source_generated_at",
        ),
        ({"latest_source_age_seconds": True}, "latest_source_age_seconds"),
        ({"max_source_age_seconds": -1}, "max_source_age_seconds"),
        ({"duplicate_latest_generated_at_count": -1}, "duplicate_latest_generated_at_count"),
        ({"reason_code_counts_json": {"reason_code": "reason"}}, "reason_code_counts_json"),
        ({"reason_code_counts_json": ["reason"]}, "reason_code_counts_json"),
        ({"reason_codes_json": "reason"}, "reason_codes_json"),
        ({"payload_json": []}, "payload_json"),
        ({"paper_only": False}, "paper_only"),
        ({"report_only": False}, "report_only"),
        ({"readonly": False}, "readonly"),
    ),
)
def test_health_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_db_row as codec

    with pytest.raises(ValueError, match=message):
        codec.PaperAutonomousInvestmentLedgerDbHistoryHealthDbRow(
            **{**_row_values(_db_row()), **overrides},
        )
