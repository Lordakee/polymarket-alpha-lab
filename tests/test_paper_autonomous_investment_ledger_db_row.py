from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_autonomous_investment_ledger import (
    PaperAutonomousInvestmentLedgerEntry,
    PaperAutonomousInvestmentLedgerReasonCodeCount,
    PaperAutonomousInvestmentLedgerReport,
)


GENERATED_AT = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)
LATEST_GENERATED_AT = datetime(2026, 6, 25, 11, 59, 30, tzinfo=UTC)
CONFIG_VERSION = "paper-autonomous-investment-ledger-test-v0"


def d(value: str) -> Decimal:
    return Decimal(value)


def _codec_module():
    from polymarket_alpha_lab import paper_autonomous_investment_ledger_db_row

    return paper_autonomous_investment_ledger_db_row


def _report() -> PaperAutonomousInvestmentLedgerReport:
    return PaperAutonomousInvestmentLedgerReport(
        generated_at=GENERATED_AT,
        config_version=CONFIG_VERSION,
        ledger_status="watch",
        recommended_next_step="review_paper_autonomous_investment_ledger",
        source_record_count=2,
        submitted_count=1,
        held_count=1,
        blocked_count=0,
        total_submitted_notional=d("12.500000"),
        held_zero_notional_count=1,
        blocked_zero_notional_count=0,
        latest_generated_at=LATEST_GENERATED_AT,
        latest_age_seconds=30,
        reason_code_counts=(
            PaperAutonomousInvestmentLedgerReasonCodeCount(
                reason_code="paper_autonomous_investment_ledger_held_records_present",
                source_record_count=1,
            ),
            PaperAutonomousInvestmentLedgerReasonCodeCount(
                reason_code="paper_broker_execution_submitted",
                source_record_count=1,
            ),
        ),
        entries=(
            PaperAutonomousInvestmentLedgerEntry(
                entry_rank=1,
                source_generated_at=datetime(2026, 6, 25, 11, 58, tzinfo=UTC),
                source_config_version="paper-broker-execution-v0",
                execution_status="paper_held",
                recommended_next_step="hold_for_operator_review",
                source_gate_status="paused",
                source_proposal_count=1,
                source_proposal_total_notional=d("25.000000"),
                execution_notional=d("0.000000"),
                reason_codes=(
                    "paper_autonomous_investment_ledger_held_records_present",
                ),
            ),
            PaperAutonomousInvestmentLedgerEntry(
                entry_rank=2,
                source_generated_at=LATEST_GENERATED_AT,
                source_config_version="paper-broker-execution-v0",
                execution_status="paper_submitted",
                recommended_next_step="archive_paper_execution",
                source_gate_status="ready",
                source_proposal_count=1,
                source_proposal_total_notional=d("12.500000"),
                execution_notional=d("12.500000"),
                reason_codes=("paper_broker_execution_submitted",),
            ),
        ),
        reason_codes=("paper_autonomous_investment_ledger_held_records_present",),
    )


def _row_values(row: object) -> dict[str, object]:
    return dict(row.__dict__)


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("DB payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


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


def _without_hard_flags(value: dict[str, object]) -> dict[str, object]:
    return {
        key: item
        for key, item in value.items()
        if key not in {"paper_only", "report_only", "readonly"}
    }


def _empty_report() -> PaperAutonomousInvestmentLedgerReport:
    return PaperAutonomousInvestmentLedgerReport(
        generated_at=GENERATED_AT,
        config_version=CONFIG_VERSION,
        ledger_status="blocked",
        recommended_next_step="block_paper_autonomous_investment_ledger",
        source_record_count=0,
        submitted_count=0,
        held_count=0,
        blocked_count=0,
        total_submitted_notional=d("0.000000"),
        held_zero_notional_count=0,
        blocked_zero_notional_count=0,
        latest_generated_at=None,
        latest_age_seconds=None,
        reason_code_counts=(),
        entries=(),
        reason_codes=("paper_autonomous_investment_ledger_no_source_records",),
    )


def test_ledger_db_row_serializes_payload_and_round_trips() -> None:
    codec = _codec_module()
    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperAutonomousInvestmentLedgerDbRow
    assert len(row.report_sha256) == 64
    assert row.report_sha256 == row.report_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.config_version == CONFIG_VERSION
    assert row.ledger_status == "watch"
    assert row.recommended_next_step == "review_paper_autonomous_investment_ledger"
    assert row.source_record_count == 2
    assert row.submitted_count == 1
    assert row.held_count == 1
    assert row.blocked_count == 0
    assert row.total_submitted_notional == d("12.500000")
    assert row.held_zero_notional_count == 1
    assert row.blocked_zero_notional_count == 0
    assert row.latest_generated_at == LATEST_GENERATED_AT
    assert row.latest_age_seconds == 30
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.reason_code_counts_json == [
        {
            "reason_code": "paper_autonomous_investment_ledger_held_records_present",
            "source_record_count": 1,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "reason_code": "paper_broker_execution_submitted",
            "source_record_count": 1,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    assert row.entries_json == [
        {
            "entry_rank": 1,
            "source_generated_at": "2026-06-25T11:58:00+00:00",
            "source_config_version": "paper-broker-execution-v0",
            "execution_status": "paper_held",
            "recommended_next_step": "hold_for_operator_review",
            "source_gate_status": "paused",
            "source_proposal_count": 1,
            "source_proposal_total_notional": "25.000000",
            "execution_notional": "0.000000",
            "reason_codes": [
                "paper_autonomous_investment_ledger_held_records_present",
            ],
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "entry_rank": 2,
            "source_generated_at": "2026-06-25T11:59:30+00:00",
            "source_config_version": "paper-broker-execution-v0",
            "execution_status": "paper_submitted",
            "recommended_next_step": "archive_paper_execution",
            "source_gate_status": "ready",
            "source_proposal_count": 1,
            "source_proposal_total_notional": "12.500000",
            "execution_notional": "12.500000",
            "reason_codes": ["paper_broker_execution_submitted"],
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    assert row.reason_codes_json == [
        "paper_autonomous_investment_ledger_held_records_present",
    ]
    assert row.payload_json["generated_at"] == "2026-06-25T12:00:00+00:00"
    assert row.payload_json["total_submitted_notional"] == "12.500000"
    assert row.payload_json["reason_code_counts"] == row.reason_code_counts_json
    assert row.payload_json["entries"] == row.entries_json
    assert row.payload_json["reason_codes"] == row.reason_codes_json
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    _assert_no_floats(row.payload_json)
    _assert_no_floats(row.reason_code_counts_json)
    _assert_no_floats(row.entries_json)
    _assert_no_floats(row.reason_codes_json)

    assert row.report_sha256 == _canonical_payload_sha256(row.payload_json)
    assert codec.from_db_row(row) == report
    assert codec.paper_autonomous_investment_ledger_report_to_db_row(report) == row
    assert codec.paper_autonomous_investment_ledger_report_from_db_row(row) == report


def test_ledger_db_row_hash_is_deterministic_and_uses_full_payload() -> None:
    codec = _codec_module()
    report = _report()
    same_report = PaperAutonomousInvestmentLedgerReport(**report.__dict__)
    changed_report = PaperAutonomousInvestmentLedgerReport(
        **{
            **report.__dict__,
            "entries": (
                report.entries[0],
                PaperAutonomousInvestmentLedgerEntry(
                    **{
                        **report.entries[1].__dict__,
                        "source_proposal_total_notional": d("13.500000"),
                        "execution_notional": d("13.500000"),
                    },
                ),
            ),
            "total_submitted_notional": d("13.500000"),
        },
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(changed_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_ledger_db_row_is_frozen() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_ledger_db_row_rejects_wrong_report_and_row_types() -> None:
    codec = _codec_module()

    with pytest.raises(ValueError, match="PaperAutonomousInvestmentLedgerReport"):
        codec.to_db_row(object())

    with pytest.raises(ValueError, match="PaperAutonomousInvestmentLedgerDbRow"):
        codec.from_db_row(object())


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_ledger_db_row_rejects_false_report_flags_before_write(flag_name: str) -> None:
    codec = _codec_module()
    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_ledger_db_row_rejects_corrupted_nested_payload_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload_json = {
        **row.payload_json,
        "entries": [
            {
                **row.payload_json["entries"][0],
                "readonly": False,
            },
            *row.payload_json["entries"][1:],
        ],
    }

    with pytest.raises(ValueError, match="readonly"):
        codec.PaperAutonomousInvestmentLedgerDbRow(
            **{**_row_values(row), "payload_json": payload_json},
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(row, payload_json=payload_json)
    malformed = _bypassed_row(row, {"payload_json": payload_json})
    with pytest.raises(ValueError, match="readonly"):
        codec.from_db_row(malformed)


def test_ledger_db_row_rejects_all_missing_nested_payload_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    entries = [_without_hard_flags(row.entries_json[0]), *row.entries_json[1:]]
    payload_json = {**row.payload_json, "entries": entries}
    report_sha256 = _canonical_payload_sha256(payload_json)

    with pytest.raises(ValueError, match="entries.*paper_only"):
        codec.PaperAutonomousInvestmentLedgerDbRow(
            **{
                **_row_values(row),
                "report_sha256": report_sha256,
                "entries_json": entries,
                "payload_json": payload_json,
            },
        )
    with pytest.raises(ValueError, match="entries.*paper_only"):
        replace(
            row,
            report_sha256=report_sha256,
            entries_json=entries,
            payload_json=payload_json,
        )
    malformed = _bypassed_row(
        row,
        {
            "report_sha256": report_sha256,
            "entries_json": entries,
            "payload_json": payload_json,
        },
    )
    with pytest.raises(ValueError, match="entries.*paper_only"):
        codec.from_db_row(malformed)


def test_ledger_db_row_rejects_all_missing_nested_materialized_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    reason_code_counts = [
        _without_hard_flags(row.reason_code_counts_json[0]),
        *row.reason_code_counts_json[1:],
    ]

    with pytest.raises(ValueError, match="reason_code_counts_json.*paper_only"):
        codec.PaperAutonomousInvestmentLedgerDbRow(
            **{**_row_values(row), "reason_code_counts_json": reason_code_counts},
        )
    with pytest.raises(ValueError, match="reason_code_counts_json.*paper_only"):
        replace(row, reason_code_counts_json=reason_code_counts)


def test_ledger_db_row_rejects_floats_in_json_payloads() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="payload_json"):
        codec.PaperAutonomousInvestmentLedgerDbRow(
            **{**_row_values(row), "payload_json": {**row.payload_json, "bad_float": 0.1}},
        )


def test_ledger_db_row_rejects_raw_payload_hash_mismatch() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload_json = {**row.payload_json, "unmaterialized_audit_field": "changed"}

    with pytest.raises(ValueError, match="report_sha256"):
        codec.PaperAutonomousInvestmentLedgerDbRow(
            **{**_row_values(row), "payload_json": payload_json},
        )
    malformed = _bypassed_row(row, {"payload_json": payload_json})
    with pytest.raises(ValueError, match="report_sha256"):
        codec.from_db_row(malformed)


def test_ledger_db_row_rejects_missing_nullable_payload_keys() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_empty_report())
    payload_json = {
        key: value
        for key, value in row.payload_json.items()
        if key != "latest_generated_at"
    }
    report_sha256 = _canonical_payload_sha256(payload_json)

    with pytest.raises(ValueError, match="latest_generated_at"):
        codec.PaperAutonomousInvestmentLedgerDbRow(
            **{
                **_row_values(row),
                "report_sha256": report_sha256,
                "payload_json": payload_json,
            },
        )
    malformed = _bypassed_row(
        row,
        {"report_sha256": report_sha256, "payload_json": payload_json},
    )
    with pytest.raises(ValueError, match="latest_generated_at"):
        codec.from_db_row(malformed)


def test_ledger_db_row_rejects_bool_for_int_payload_values_strictly() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload_json = {**row.payload_json, "submitted_count": True}
    report_sha256 = _canonical_payload_sha256(payload_json)

    with pytest.raises(ValueError, match="submitted_count"):
        codec.PaperAutonomousInvestmentLedgerDbRow(
            **{
                **_row_values(row),
                "report_sha256": report_sha256,
                "payload_json": payload_json,
            },
        )
    malformed = _bypassed_row(
        row,
        {"report_sha256": report_sha256, "payload_json": payload_json},
    )
    with pytest.raises(ValueError, match="submitted_count"):
        codec.from_db_row(malformed)


def test_ledger_db_row_rejects_noncanonical_decimal_payload_strings() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload_json = {
        **row.payload_json,
        "total_submitted_notional": "12.5000000",
    }
    report_sha256 = _canonical_payload_sha256(payload_json)

    with pytest.raises(ValueError, match="total_submitted_notional"):
        codec.PaperAutonomousInvestmentLedgerDbRow(
            **{
                **_row_values(row),
                "report_sha256": report_sha256,
                "total_submitted_notional": d("12.5000000"),
                "payload_json": payload_json,
            },
        )
    malformed = _bypassed_row(
        row,
        {
            "report_sha256": report_sha256,
            "total_submitted_notional": d("12.5000000"),
            "payload_json": payload_json,
        },
    )
    with pytest.raises(ValueError, match="payload_json|total_submitted_notional"):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 25, 12, 1, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "paper-autonomous-investment-ledger-test-v1"}, "config_version"),
        ({"ledger_status": "pass"}, "ledger_status"),
        ({"recommended_next_step": "archive_paper_autonomous_investment_ledger"}, "recommended_next_step"),
        ({"source_record_count": 1}, "source_record_count"),
        ({"submitted_count": 0}, "submitted_count"),
        ({"held_count": 0}, "held_count"),
        ({"blocked_count": 1}, "blocked_count"),
        ({"total_submitted_notional": d("13.500000")}, "total_submitted_notional"),
        ({"held_zero_notional_count": 0}, "held_zero_notional_count"),
        ({"latest_age_seconds": 31}, "latest_age_seconds"),
        ({"reason_code_counts_json": []}, "reason_code_counts_json"),
        ({"entries_json": []}, "entries_json"),
        ({"reason_codes_json": ["paper_autonomous_investment_ledger_passed"]}, "reason_codes_json"),
    ),
)
def test_ledger_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperAutonomousInvestmentLedgerDbRow(
            **{**_row_values(row), **overrides},
        )
    with pytest.raises(ValueError, match=message):
        replace(row, **overrides)
    malformed = _bypassed_row(row, overrides)
    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"source_record_count": True}, "source_record_count"),
        ({"ledger_status": "live"}, "ledger_status"),
        ({"reason_code_counts_json": "reasons"}, "reason_code_counts_json"),
        ({"entries_json": "entries"}, "entries_json"),
        ({"reason_codes_json": [1]}, "reason_codes_json"),
        ({"paper_only": False}, "paper_only"),
        ({"report_only": False}, "report_only"),
        ({"readonly": False}, "readonly"),
    ),
)
def test_ledger_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperAutonomousInvestmentLedgerDbRow(
            **{**_row_values(row), **overrides},
        )


def test_ledger_db_row_module_is_pure_paper_report_only_codec() -> None:
    _codec_module()
    source = Path(
        "src/polymarket_alpha_lab/paper_autonomous_investment_ledger_db_row.py",
    ).read_text(encoding="utf-8")

    for banned in (
        "psycopg",
        "supabase",
        "os.environ",
        "requests",
        "httpx",
        "urllib",
        "subprocess",
        "socket",
        "private_key",
        "wallet",
        "account",
        "submit_order",
        "cancel_order",
        "replace_order",
        "open(",
        "print(",
    ):
        assert banned not in source.lower()
