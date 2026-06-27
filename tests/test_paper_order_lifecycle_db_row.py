"""Tests for paper order lifecycle DB row codec."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.paper_order_lifecycle import PaperOrderLifecycleRecord
from polymarket_alpha_lab.paper_order_lifecycle_db_row import (
    PaperOrderLifecycleDbRow,
    paper_order_lifecycle_record_from_db_row,
    paper_order_lifecycle_record_to_db_row,
)


GENERATED_AT = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)


def _record() -> PaperOrderLifecycleRecord:
    return PaperOrderLifecycleRecord(
        generated_at=GENERATED_AT,
        config_version="paper-order-lifecycle-v0",
        lifecycle_status="paper_filled",
        recommended_next_step="record_paper_outcome",
        source_execution_status="paper_submitted",
        source_execution_notional=Decimal("1.230000"),
        fill_notional=Decimal("1.230000"),
        is_terminal=True,
        reason_codes=("paper_order_lifecycle_filled",),
    )


def _payload_sha256(payload_json: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _row_kwargs(row: PaperOrderLifecycleDbRow) -> dict[str, Any]:
    return {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at,
        "config_version": row.config_version,
        "lifecycle_status": row.lifecycle_status,
        "recommended_next_step": row.recommended_next_step,
        "source_execution_status": row.source_execution_status,
        "source_execution_notional": row.source_execution_notional,
        "fill_notional": row.fill_notional,
        "is_terminal": row.is_terminal,
        "reason_codes_json": list(row.reason_codes_json),
        "payload_json": dict(row.payload_json),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _valid_row() -> PaperOrderLifecycleDbRow:
    return paper_order_lifecycle_record_to_db_row(_record())


def _bypassed_row(
    row: PaperOrderLifecycleDbRow,
    *,
    payload_json: dict[str, Any] | None = None,
    report_sha256: str | None = None,
    **overrides: Any,
) -> PaperOrderLifecycleDbRow:
    bypassed = object.__new__(PaperOrderLifecycleDbRow)
    kwargs = _row_kwargs(row)
    if payload_json is not None:
        kwargs["payload_json"] = payload_json
    if report_sha256 is not None:
        kwargs["report_sha256"] = report_sha256
    kwargs.update(overrides)
    for field_name, value in kwargs.items():
        object.__setattr__(bypassed, field_name, value)
    return bypassed


def test_order_lifecycle_db_row_module_is_pure_paper_only_codec() -> None:
    source = Path(
        "src/polymarket_alpha_lab/paper_order_lifecycle_db_row.py",
    ).read_text(encoding="utf-8")

    for banned in (
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "private_key",
        "wallet",
        "api_key",
        "submit_order",
        "cancel_order",
        "replace_order",
        "live_trading",
        "exchange",
    ):
        assert banned not in source.lower()


def _kwargs_with_payload(
    row: PaperOrderLifecycleDbRow,
    payload_json: dict[str, Any],
    **overrides: Any,
) -> dict[str, Any]:
    kwargs = _row_kwargs(row)
    kwargs.update(
        report_sha256=_payload_sha256(payload_json),
        payload_json=payload_json,
    )
    kwargs.update(overrides)
    return kwargs


def test_record_to_db_row_uses_canonical_payload_hash_and_round_trips() -> None:
    record = _record()
    row = paper_order_lifecycle_record_to_db_row(record)

    assert row.payload_json == {
        "generated_at": "2026-06-25T12:00:00+00:00",
        "config_version": "paper-order-lifecycle-v0",
        "lifecycle_status": "paper_filled",
        "recommended_next_step": "record_paper_outcome",
        "source_execution_status": "paper_submitted",
        "source_execution_notional": "1.230000",
        "fill_notional": "1.230000",
        "is_terminal": True,
        "reason_codes": ["paper_order_lifecycle_filled"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert row.report_sha256 == _payload_sha256(row.payload_json)
    assert paper_order_lifecycle_record_from_db_row(row) == record


def test_record_to_db_row_writes_decimal_payload_fields_at_fixed_six_places() -> None:
    record = PaperOrderLifecycleRecord(
        generated_at=GENERATED_AT,
        config_version="paper-order-lifecycle-v0",
        lifecycle_status="paper_filled",
        recommended_next_step="record_paper_outcome",
        source_execution_status="paper_submitted",
        source_execution_notional=Decimal("1.2"),
        fill_notional=Decimal("3"),
        is_terminal=True,
        reason_codes=("paper_order_lifecycle_filled",),
    )

    row = paper_order_lifecycle_record_to_db_row(record)

    assert row.payload_json["source_execution_notional"] == "1.200000"
    assert row.payload_json["fill_notional"] == "3.000000"
    assert row.report_sha256 == _payload_sha256(row.payload_json)
    assert paper_order_lifecycle_record_from_db_row(row) == record


def test_from_db_row_recovers_equivalent_legacy_decimal_payload_after_raw_hash() -> None:
    row = _valid_row()
    payload_json = dict(row.payload_json)
    payload_json["source_execution_notional"] = "1.23"
    payload_json["fill_notional"] = "1.230"
    legacy_row = _bypassed_row(
        row,
        payload_json=payload_json,
        report_sha256=_payload_sha256(payload_json),
    )

    recovered = paper_order_lifecycle_record_from_db_row(legacy_row)

    assert recovered == _record()


def test_from_db_row_rejects_legacy_payload_when_raw_hash_is_stale() -> None:
    row = _valid_row()
    payload_json = dict(row.payload_json)
    payload_json["source_execution_notional"] = "1.23"
    payload_json["fill_notional"] = "1.230"
    stale_hash_row = _bypassed_row(row, payload_json=payload_json)

    with pytest.raises(ValueError, match="report_sha256 must match payload_json"):
        paper_order_lifecycle_record_from_db_row(stale_hash_row)


def test_from_db_row_rejects_legacy_decimal_payload_that_changes_value() -> None:
    row = _valid_row()
    payload_json = dict(row.payload_json)
    payload_json["source_execution_notional"] = "1.24"
    payload_json["fill_notional"] = "1.230"
    changed_value_row = _bypassed_row(
        row,
        payload_json=payload_json,
        report_sha256=_payload_sha256(payload_json),
    )

    with pytest.raises(ValueError, match="source_execution_notional must match payload_json"):
        paper_order_lifecycle_record_from_db_row(changed_value_row)


@pytest.mark.parametrize(
    ("payload_key", "payload_value"),
    (
        ("source_execution_notional", "1.2300001"),
        ("fill_notional", "1.2300001"),
    ),
)
def test_from_db_row_rejects_overprecision_legacy_decimal_payload(
    payload_key: str,
    payload_value: str,
) -> None:
    row = _valid_row()
    payload_json = dict(row.payload_json)
    payload_json[payload_key] = payload_value
    overprecision_row = _bypassed_row(
        row,
        payload_json=payload_json,
        report_sha256=_payload_sha256(payload_json),
    )

    with pytest.raises(ValueError, match="at most six decimal places"):
        paper_order_lifecycle_record_from_db_row(overprecision_row)


def test_from_db_row_rejects_non_allowlisted_decimal_like_payload() -> None:
    row = _valid_row()
    payload_json = dict(row.payload_json)
    payload_json["recommended_next_step"] = "1.230000"
    decimal_like_row = _bypassed_row(
        row,
        payload_json=payload_json,
        report_sha256=_payload_sha256(payload_json),
    )

    with pytest.raises(ValueError, match="Decimal-like|allowlisted"):
        paper_order_lifecycle_record_from_db_row(decimal_like_row)


@pytest.mark.parametrize(
    ("payload_key", "payload_value", "match"),
    (
        ("source_execution_notional", 1.23, "float"),
        ("source_execution_notional", Decimal("1.23"), "raw Decimal"),
        ("generated_at", GENERATED_AT, "raw datetime"),
    ),
)
def test_from_db_row_rejects_raw_unsafe_json_payload_values(
    payload_key: str,
    payload_value: Any,
    match: str,
) -> None:
    row = _valid_row()
    payload_json = dict(row.payload_json)
    payload_json[payload_key] = payload_value
    unsafe_row = _bypassed_row(
        row,
        payload_json=payload_json,
        report_sha256=row.report_sha256,
    )

    with pytest.raises(ValueError, match=match):
        paper_order_lifecycle_record_from_db_row(unsafe_row)


def test_constructor_rejects_report_sha256_mismatch() -> None:
    row = _valid_row()
    kwargs = _row_kwargs(row)
    kwargs["report_sha256"] = "0" * 64

    with pytest.raises(ValueError, match="report_sha256 must match payload_json"):
        PaperOrderLifecycleDbRow(**kwargs)


@pytest.mark.parametrize(
    ("field_name", "payload_key", "payload_value"),
    (
        (
            "generated_at",
            "generated_at",
            "2026-06-25T12:00:01+00:00",
        ),
        ("config_version", "config_version", "paper-order-lifecycle-v1"),
        ("lifecycle_status", "lifecycle_status", "risk_blocked"),
        (
            "recommended_next_step",
            "recommended_next_step",
            "archive_proposal",
        ),
        ("source_execution_status", "source_execution_status", "paper_blocked"),
        ("source_execution_notional", "source_execution_notional", "2.000000"),
        ("fill_notional", "fill_notional", "2.000000"),
        ("is_terminal", "is_terminal", False),
    ),
)
def test_constructor_rejects_materialized_payload_mismatch(
    field_name: str,
    payload_key: str,
    payload_value: Any,
) -> None:
    row = _valid_row()
    payload_json = dict(row.payload_json)
    payload_json[payload_key] = payload_value

    with pytest.raises(ValueError, match=f"{field_name} must match payload_json"):
        PaperOrderLifecycleDbRow(**_kwargs_with_payload(row, payload_json))


def test_constructor_rejects_reason_codes_json_payload_mismatch() -> None:
    row = _valid_row()
    payload_json = dict(row.payload_json)
    payload_json["reason_codes"] = ["paper_order_lifecycle_other"]

    with pytest.raises(ValueError, match="reason_codes_json must match payload_json"):
        PaperOrderLifecycleDbRow(**_kwargs_with_payload(row, payload_json))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_constructor_rejects_hard_flag_payload_mismatch(flag_name: str) -> None:
    row = _valid_row()
    payload_json = dict(row.payload_json)
    payload_json[flag_name] = False

    with pytest.raises(ValueError, match=f"{flag_name} must match payload_json"):
        PaperOrderLifecycleDbRow(**_kwargs_with_payload(row, payload_json))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_constructor_rejects_unsafe_hard_flags(flag_name: str) -> None:
    row = _valid_row()
    payload_json = dict(row.payload_json)
    payload_json[flag_name] = False

    with pytest.raises(ValueError, match=f"{flag_name} must be True"):
        PaperOrderLifecycleDbRow(
            **_kwargs_with_payload(row, payload_json, **{flag_name: False}),
        )


def test_constructor_rejects_payload_floats() -> None:
    row = _valid_row()
    payload_json = dict(row.payload_json)
    payload_json["source_execution_notional"] = 1.23

    kwargs = _row_kwargs(row)
    kwargs.update(report_sha256="0" * 64, payload_json=payload_json)

    with pytest.raises(ValueError, match="float"):
        PaperOrderLifecycleDbRow(**kwargs)


def test_constructor_rejects_payload_noncanonical_json_values() -> None:
    row = _valid_row()
    payload_json = dict(row.payload_json)
    payload_json["reason_codes"] = tuple(row.reason_codes_json)

    kwargs = _row_kwargs(row)
    kwargs.update(report_sha256="0" * 64, payload_json=payload_json)

    with pytest.raises(ValueError, match="canonical JSON"):
        PaperOrderLifecycleDbRow(**kwargs)


def test_from_db_row_revalidates_object_new_bypassed_rows() -> None:
    row = _valid_row()
    payload_json = dict(row.payload_json)
    payload_json["fill_notional"] = "2.000000"
    bypassed = _bypassed_row(
        row,
        payload_json=payload_json,
        report_sha256=_payload_sha256(payload_json),
    )

    with pytest.raises(ValueError, match="fill_notional must match payload_json"):
        paper_order_lifecycle_record_from_db_row(bypassed)
