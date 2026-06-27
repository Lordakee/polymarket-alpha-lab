from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_execution_reconciliation import (
    PaperExecutionReconciliationPositionRow,
    PaperExecutionReconciliationReport,
)


GENERATED_AT = datetime(2026, 6, 25, 10, 30, tzinfo=UTC)
CONFIG_VERSION = "paper-execution-reconciliation-db-test-v0"


def d(value: str) -> Decimal:
    return Decimal(value)


def _codec():
    try:
        return importlib.import_module(
            "polymarket_alpha_lab.paper_execution_reconciliation_db_row",
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"codec module missing: {exc}")


def _report() -> PaperExecutionReconciliationReport:
    return PaperExecutionReconciliationReport(
        generated_at=GENERATED_AT,
        config_version=CONFIG_VERSION,
        reconciliation_status="has_pending",
        total_positions=2,
        filled_pending_count=1,
        settled_win_count=0,
        settled_loss_count=1,
        expired_count=0,
        cancelled_count=0,
        total_fill_notional=d("15.000000"),
        total_cost_basis=d("17.000000"),
        total_outcome_value=d("0.000000"),
        total_pnl=d("-2.000000"),
        realized_pnl=d("-2.000000"),
        unrealized_pnl=d("0.000000"),
        position_rows=(
            PaperExecutionReconciliationPositionRow(
                condition_id="condition-alpha",
                market_slug="alpha-market",
                question="Will alpha resolve yes?",
                scoring_side="yes",
                position_status="settled_loss",
                fill_notional=d("10.000000"),
                cost_basis=d("12.000000"),
                outcome_value=d("0.000000"),
                pnl=d("-2.000000"),
            ),
            PaperExecutionReconciliationPositionRow(
                condition_id="condition-beta",
                market_slug="beta-market",
                question="Will beta resolve yes?",
                scoring_side="no",
                position_status="filled_pending",
                fill_notional=d("5.000000"),
                cost_basis=d("5.000000"),
                outcome_value=None,
                pnl=None,
            ),
        ),
        reason_codes=(
            "paper_execution_reconciliation_has_pending",
            "paper_execution_reconciliation_settled_loss",
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _equivalent_exponent_report() -> PaperExecutionReconciliationReport:
    report = _report()
    return PaperExecutionReconciliationReport(
        **{
            **report.__dict__,
            "total_fill_notional": d("15"),
            "total_cost_basis": d("17.0"),
            "total_outcome_value": d("0"),
            "total_pnl": d("-2"),
            "realized_pnl": d("-2.0"),
            "unrealized_pnl": d("0"),
            "position_rows": (
                PaperExecutionReconciliationPositionRow(
                    **{
                        **report.position_rows[0].__dict__,
                        "fill_notional": d("10"),
                        "cost_basis": d("12.0"),
                        "outcome_value": d("0"),
                        "pnl": d("-2.0"),
                    },
                ),
                PaperExecutionReconciliationPositionRow(
                    **{
                        **report.position_rows[1].__dict__,
                        "fill_notional": d("5"),
                        "cost_basis": d("5.0"),
                    },
                ),
            ),
        },
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


def _row_values(row) -> dict[str, object]:
    return {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at,
        "config_version": row.config_version,
        "reconciliation_status": row.reconciliation_status,
        "total_positions": row.total_positions,
        "filled_pending_count": row.filled_pending_count,
        "settled_win_count": row.settled_win_count,
        "settled_loss_count": row.settled_loss_count,
        "expired_count": row.expired_count,
        "cancelled_count": row.cancelled_count,
        "total_fill_notional": row.total_fill_notional,
        "total_cost_basis": row.total_cost_basis,
        "total_outcome_value": row.total_outcome_value,
        "total_pnl": row.total_pnl,
        "realized_pnl": row.realized_pnl,
        "unrealized_pnl": row.unrealized_pnl,
        "position_rows_json": row.position_rows_json,
        "reason_codes_json": row.reason_codes_json,
        "payload_json": row.payload_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _unchecked_row(row: object, **overrides: object) -> object:
    values = _row_values(row)
    values.update(overrides)
    unchecked = object.__new__(type(row))
    for field_name, value in values.items():
        object.__setattr__(unchecked, field_name, value)
    return unchecked


def _canonical_payload_sha256(payload_json: dict[str, object]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def test_reconciliation_db_row_serializes_canonical_payload_and_round_trips():
    codec = _codec()
    report = _report()

    row = codec.paper_execution_reconciliation_report_to_db_row(report)

    assert type(row) is codec.PaperExecutionReconciliationDbRow
    assert len(row.report_sha256) == 64
    assert row.report_sha256 == row.report_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.config_version == CONFIG_VERSION
    assert row.reconciliation_status == "has_pending"
    assert row.total_positions == 2
    assert row.settled_loss_count == 1
    assert row.total_fill_notional == d("15.000000")
    assert row.total_pnl == d("-2.000000")
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.position_rows_json == [
        {
            "condition_id": "condition-alpha",
            "market_slug": "alpha-market",
            "question": "Will alpha resolve yes?",
            "scoring_side": "yes",
            "position_status": "settled_loss",
            "fill_notional": "10.000000",
            "cost_basis": "12.000000",
            "outcome_value": "0.000000",
            "pnl": "-2.000000",
        },
        {
            "condition_id": "condition-beta",
            "market_slug": "beta-market",
            "question": "Will beta resolve yes?",
            "scoring_side": "no",
            "position_status": "filled_pending",
            "fill_notional": "5.000000",
            "cost_basis": "5.000000",
            "outcome_value": None,
            "pnl": None,
        },
    ]
    assert row.payload_json["generated_at"] == "2026-06-25T10:30:00+00:00"
    assert row.payload_json["total_fill_notional"] == "15.000000"
    assert row.payload_json["total_pnl"] == "-2.000000"
    assert row.payload_json["position_rows"] == row.position_rows_json
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    _assert_no_floats(row.payload_json)

    encoded = json.dumps(
        row.payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    assert row.report_sha256 == hashlib.sha256(encoded).hexdigest()
    assert codec.paper_execution_reconciliation_report_from_db_row(row) == report
    assert codec.to_db_row(report) == row
    assert codec.from_db_row(row) == report


def test_reconciliation_db_row_writes_fixed_six_decimal_payload_paths():
    codec = _codec()

    canonical_row = codec.to_db_row(_report())
    equivalent_row = codec.to_db_row(_equivalent_exponent_report())

    assert equivalent_row.payload_json == canonical_row.payload_json
    assert equivalent_row.report_sha256 == canonical_row.report_sha256
    assert equivalent_row.payload_json["total_fill_notional"] == "15.000000"
    assert equivalent_row.payload_json["total_cost_basis"] == "17.000000"
    assert equivalent_row.payload_json["total_outcome_value"] == "0.000000"
    assert equivalent_row.payload_json["total_pnl"] == "-2.000000"
    assert equivalent_row.payload_json["realized_pnl"] == "-2.000000"
    assert equivalent_row.payload_json["unrealized_pnl"] == "0.000000"
    assert equivalent_row.payload_json["position_rows"][0]["fill_notional"] == "10.000000"
    assert equivalent_row.payload_json["position_rows"][0]["cost_basis"] == "12.000000"
    assert equivalent_row.payload_json["position_rows"][0]["outcome_value"] == "0.000000"
    assert equivalent_row.payload_json["position_rows"][0]["pnl"] == "-2.000000"
    assert equivalent_row.payload_json["position_rows"][1]["fill_notional"] == "5.000000"
    assert equivalent_row.payload_json["position_rows"][1]["cost_basis"] == "5.000000"


def test_reconciliation_db_row_hash_uses_full_payload_including_position_rows():
    codec = _codec()
    report = _report()
    same_report = PaperExecutionReconciliationReport(**report.__dict__)
    changed_report = PaperExecutionReconciliationReport(
        **{
            **report.__dict__,
            "position_rows": (
                PaperExecutionReconciliationPositionRow(
                    **{
                        **report.position_rows[0].__dict__,
                        "pnl": d("-1.000000"),
                    },
                ),
                report.position_rows[1],
            ),
            "total_pnl": d("-1.000000"),
            "realized_pnl": d("-1.000000"),
        },
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(changed_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_reconciliation_db_row_is_frozen():
    codec = _codec()
    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.paper_only = False  # type: ignore[misc]


def test_reconciliation_db_row_rejects_wrong_report_and_row_types():
    codec = _codec()

    with pytest.raises(ValueError, match="PaperExecutionReconciliationReport"):
        codec.to_db_row(object())

    with pytest.raises(ValueError, match="PaperExecutionReconciliationDbRow"):
        codec.from_db_row(object())


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_reconciliation_db_row_rejects_false_report_flags(flag_name: str):
    codec = _codec()
    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 25, 10, 31, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "different-v0"}, "config_version"),
        ({"reconciliation_status": "reconciled"}, "reconciliation_status"),
        ({"total_positions": 3}, "total_positions"),
        ({"settled_loss_count": 0}, "settled_loss_count"),
        ({"total_fill_notional": d("16.000000")}, "total_fill_notional"),
        (
            {"position_rows_json": [{"condition_id": "missing-fields"}]},
            "position_rows_json",
        ),
        ({"reason_codes_json": ["different_reason"]}, "reason_codes_json"),
    ),
)
def test_reconciliation_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperExecutionReconciliationDbRow(
            **{**_row_values(row), **overrides},
        )


def test_reconciliation_db_row_rejects_payload_mismatch_on_replace() -> None:
    codec = _codec()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="total_positions"):
        replace(row, total_positions=3)


def test_reconciliation_from_db_row_rejects_constructor_bypassed_mismatch() -> None:
    codec = _codec()
    row = codec.to_db_row(_report())
    malformed = _unchecked_row(row, total_positions=3)

    with pytest.raises(ValueError, match="total_positions"):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("total_fill_notional", d("15.0000000")),
        ("total_cost_basis", d("17.0000000")),
        ("total_outcome_value", d("0.0000000")),
        ("total_pnl", d("-2.0000000")),
        ("realized_pnl", d("-2.0000000")),
        ("unrealized_pnl", d("0.0000000")),
    ),
)
def test_reconciliation_from_db_row_rejects_bypassed_noncanonical_materialized_decimal(
    field_name: str,
    value: Decimal,
) -> None:
    codec = _codec()
    row = codec.to_db_row(_report())
    malformed = _unchecked_row(row, **{field_name: value})

    with pytest.raises(ValueError, match=field_name):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("payload_updates", "expected_message"),
    (
        ({"filled_pending_count": True}, "filled_pending_count"),
        ({"settled_loss_count": True}, "settled_loss_count"),
        ({"total_fill_notional": "15.0000000"}, "canonical|total_fill_notional"),
    ),
)
def test_reconciliation_db_row_rejects_type_loose_or_noncanonical_payload_values(
    payload_updates: dict[str, object],
    expected_message: str,
) -> None:
    codec = _codec()
    row = codec.to_db_row(_report())
    payload = {**row.payload_json, **payload_updates}

    with pytest.raises(ValueError, match=expected_message):
        codec.PaperExecutionReconciliationDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_reconciliation_db_row_rejects_noncanonical_nested_decimal_payload_string() -> None:
    codec = _codec()
    row = codec.to_db_row(_report())
    position_rows = [dict(item) for item in row.position_rows_json]
    position_rows[0]["fill_notional"] = "10.0000000"
    payload = {**row.payload_json, "position_rows": position_rows}

    with pytest.raises(ValueError, match="payload_json must be canonical|fill_notional"):
        codec.PaperExecutionReconciliationDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "position_rows_json": position_rows,
                "payload_json": payload,
            },
        )


def test_reconciliation_from_db_row_rejects_unchecked_raw_hash_bypass() -> None:
    codec = _codec()
    row = codec.to_db_row(_report())
    payload = {**row.payload_json, "total_fill_notional": "15.0000000"}
    malformed = _unchecked_row(
        row,
        report_sha256=_canonical_payload_sha256(payload),
        payload_json=payload,
    )

    with pytest.raises(
        ValueError,
        match="payload_json must be canonical|report_sha256|six decimal",
    ):
        codec.from_db_row(malformed)


def test_reconciliation_from_db_row_accepts_self_hashed_legacy_decimal_payload() -> None:
    codec = _codec()
    row = codec.to_db_row(_report())
    payload = deepcopy(row.payload_json)
    payload["total_fill_notional"] = "15"
    payload["total_cost_basis"] = "17.0"
    payload["total_outcome_value"] = "0"
    payload["total_pnl"] = "-2"
    payload["realized_pnl"] = "-2.0"
    payload["unrealized_pnl"] = "0"
    payload["position_rows"][0]["fill_notional"] = "10"
    payload["position_rows"][0]["cost_basis"] = "12.0"
    payload["position_rows"][0]["outcome_value"] = "0"
    payload["position_rows"][0]["pnl"] = "-2.0"
    payload["position_rows"][1]["fill_notional"] = "5"
    payload["position_rows"][1]["cost_basis"] = "5.0"

    legacy_row = codec.PaperExecutionReconciliationDbRow(
        **{
            **_row_values(row),
            "report_sha256": _canonical_payload_sha256(payload),
            "position_rows_json": payload["position_rows"],
            "payload_json": payload,
        },
    )

    assert codec.from_db_row(legacy_row) == _report()


def test_reconciliation_from_db_row_rejects_stale_legacy_decimal_payload_hash() -> None:
    codec = _codec()
    row = codec.to_db_row(_report())
    payload = deepcopy(row.payload_json)
    payload["total_fill_notional"] = "15"

    with pytest.raises(ValueError, match="report_sha256"):
        codec.PaperExecutionReconciliationDbRow(
            **{
                **_row_values(row),
                "payload_json": payload,
            },
        )

    with pytest.raises(ValueError, match="report_sha256"):
        codec.from_db_row(
            _unchecked_row(
                row,
                payload_json=payload,
            ),
        )


def test_reconciliation_from_db_row_rejects_value_changing_legacy_payload() -> None:
    codec = _codec()
    row = codec.to_db_row(_report())
    payload = deepcopy(row.payload_json)
    payload["total_fill_notional"] = "15.000001"

    with pytest.raises(ValueError, match="total_fill_notional"):
        codec.PaperExecutionReconciliationDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_reconciliation_from_db_row_rejects_overprecision_legacy_decimal_payload() -> None:
    codec = _codec()
    row = codec.to_db_row(_report())
    payload = deepcopy(row.payload_json)
    payload["total_fill_notional"] = "15.0000001"

    with pytest.raises(ValueError, match="six decimal|overprecision|payload_json"):
        codec.from_db_row(
            _unchecked_row(
                row,
                report_sha256=_canonical_payload_sha256(payload),
                total_fill_notional=d("15.0000001"),
                payload_json=payload,
            ),
        )


def test_reconciliation_db_row_rejects_non_allowlisted_decimal_like_strings() -> None:
    codec = _codec()
    row = codec.to_db_row(_report())
    payload = deepcopy(row.payload_json)
    payload["position_rows"][0]["market_slug"] = "1.0"

    with pytest.raises(ValueError, match="market_slug|Decimal-like|allowlisted|payload_json"):
        codec.PaperExecutionReconciliationDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "position_rows_json": payload["position_rows"],
                "payload_json": payload,
            },
        )


@pytest.mark.parametrize(
    ("field_name", "value", "message"),
    (
        ("total_fill_notional", 15.0, "float|payload_json"),
        ("total_fill_notional", d("15.000000"), "Decimal|JSON"),
        ("generated_at", GENERATED_AT, "datetime|JSON"),
    ),
)
def test_reconciliation_db_row_rejects_raw_non_json_payload_values(
    field_name: str,
    value: object,
    message: str,
) -> None:
    codec = _codec()
    row = codec.to_db_row(_report())
    payload = deepcopy(row.payload_json)
    payload[field_name] = value

    with pytest.raises(ValueError, match=message):
        codec.PaperExecutionReconciliationDbRow(
            **{
                **_row_values(row),
                "payload_json": payload,
            },
        )

    with pytest.raises(ValueError, match=message):
        codec.from_db_row(_unchecked_row(row, payload_json=payload))


def test_reconciliation_db_row_rejects_nested_all_missing_hard_flags() -> None:
    codec = _codec()
    row = codec.to_db_row(_report())
    payload = {
        **row.payload_json,
        "source_report": {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "nested_report": {
                "generated_at": "2026-06-25T10:30:00+00:00",
                "config_version": "nested-v0",
                "reason_codes": [],
            },
        },
    }

    with pytest.raises(ValueError, match="nested_report paper_only"):
        codec.PaperExecutionReconciliationDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_reconciliation_db_row_wraps_payload_recovery_errors_as_value_error():
    codec = _codec()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="position_rows_json|payload_json"):
        codec.PaperExecutionReconciliationDbRow(
            **{
                **_row_values(row),
                "payload_json": {
                    key: value
                    for key, value in row.payload_json.items()
                    if key != "position_rows"
                },
            },
        )


def test_reconciliation_from_db_row_wraps_bypassed_payload_recovery_errors() -> None:
    codec = _codec()
    row = codec.to_db_row(_report())
    malformed = _unchecked_row(
        row,
        payload_json={
            key: value
            for key, value in row.payload_json.items()
            if key != "position_rows"
        },
    )

    with pytest.raises(ValueError, match="payload_json|position_rows_json"):
        codec.from_db_row(malformed)


def test_reconciliation_db_row_validates_row_shape_and_rejects_floats():
    codec = _codec()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="report_sha256"):
        codec.PaperExecutionReconciliationDbRow(
            **{**_row_values(row), "report_sha256": "bad"},
        )

    with pytest.raises(ValueError, match="payload_json"):
        codec.PaperExecutionReconciliationDbRow(
            **{
                **_row_values(row),
                "payload_json": {**row.payload_json, "bad_float": 0.1},
            },
        )


def test_reconciliation_db_row_module_is_pure_codec():
    _codec()
    source = Path(
        "src/polymarket_alpha_lab/paper_execution_reconciliation_db_row.py",
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
        "execute(",
        "open(",
        "print(",
    ):
        assert banned not in source.lower()
