from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
import re
from collections.abc import Mapping

import pytest

from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate import (
    build_paper_autonomous_proposal_risk_gate_report,
)
from tests.test_paper_autonomous_proposal_risk_gate import _proposal_report


GENERATED_AT = datetime(2026, 6, 30, 12, 0, tzinfo=UTC)
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def _risk_gate_report(*, gate_status: str = "pass"):
    return build_paper_autonomous_proposal_risk_gate_report(
        proposal_report=_proposal_report(gate_status=gate_status),
        generated_at=GENERATED_AT,
    )


def _db_row():
    import polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_db_row as codec

    return codec.to_db_row(_risk_gate_report())


def _row_values(row: object) -> dict[str, object]:
    return dict(row.__dict__)


def _bypassed_row(row: object, overrides: dict[str, object]) -> object:
    bypassed = object.__new__(type(row))
    for field_name, value in {**_row_values(row), **overrides}.items():
        object.__setattr__(bypassed, field_name, value)
    return bypassed


def _mutable_json(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _mutable_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_mutable_json(item) for item in value]
    return value


def _canonical_payload_sha256(payload_json: Mapping[str, object]) -> str:
    _assert_json_safe(payload_json)
    encoded = json.dumps(
        _mutable_json(payload_json),
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _assert_json_safe(value: object) -> None:
    if isinstance(value, (float, Decimal, datetime)):
        pytest.fail(f"unexpected raw JSON value {value!r}")
    if isinstance(value, Mapping):
        for item in value.values():
            _assert_json_safe(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_json_safe(item)


def test_proposal_risk_gate_db_row_serializes_payload_and_round_trips() -> None:
    import polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_db_row as codec

    report = _risk_gate_report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperAutonomousProposalRiskGateDbRow
    assert SHA256_RE.fullmatch(row.report_sha256)
    assert row.generated_at == GENERATED_AT
    assert row.config_version == report.config_version
    assert row.gate_status == "pass"
    assert row.recommended_next_step == "allow_paper_proposal_to_paper_broker"
    assert row.source_proposal_status == "candidate"
    assert row.source_proposal_count == report.source_proposal_count
    assert row.source_proposal_total_notional == report.source_proposal_total_notional
    assert type(row.source_proposal_total_notional) is Decimal
    assert row.blocked_reason_codes_json == ()
    assert row.watch_reason_codes_json == ()
    assert row.reason_codes_json == report.reason_codes
    assert row.payload_json["generated_at"] == "2026-06-30T12:00:00+00:00"
    assert row.payload_json["source_proposal_total_notional"] == (
        f"{report.source_proposal_total_notional:.6f}"
    )
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    _assert_json_safe(row.blocked_reason_codes_json)
    _assert_json_safe(row.watch_reason_codes_json)
    _assert_json_safe(row.reason_codes_json)
    _assert_json_safe(row.payload_json)

    assert row.report_sha256 == _canonical_payload_sha256(row.payload_json)
    assert codec.from_db_row(row) == report
    assert codec.paper_autonomous_proposal_risk_gate_report_to_db_row(report) == row
    assert codec.paper_autonomous_proposal_risk_gate_report_from_db_row(row) == report


def test_proposal_risk_gate_db_row_writes_decimal_payloads_as_fixed_six_place_strings() -> None:
    import polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_db_row as codec

    report = replace(
        _risk_gate_report(),
        source_proposal_total_notional=Decimal("10.5"),
    )

    row = codec.to_db_row(report)

    assert row.source_proposal_total_notional == Decimal("10.500000")
    assert str(row.source_proposal_total_notional) == "10.500000"
    assert row.payload_json["source_proposal_total_notional"] == "10.500000"
    assert codec.from_db_row(row) == report


def test_proposal_risk_gate_db_row_is_frozen() -> None:
    row = _db_row()

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_proposal_risk_gate_db_row_nested_json_values_are_immutable() -> None:
    row = _db_row()

    with pytest.raises(TypeError, match="does not support item assignment"):
        row.payload_json["gate_status"] = "watch"
    with pytest.raises(AttributeError, match="append"):
        row.reason_codes_json.append("extra_reason")
    with pytest.raises(TypeError):
        dict.__setitem__(row.payload_json, "gate_status", "watch")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        list.append(row.reason_codes_json, "extra_reason")  # type: ignore[arg-type]

    assert row.report_sha256 == _canonical_payload_sha256(row.payload_json)
    assert row.payload_json["gate_status"] == row.gate_status
    assert row.reason_codes_json == tuple(row.reason_codes_json)


def test_proposal_risk_gate_db_row_normalizes_aware_datetimes_to_utc() -> None:
    row = _db_row()

    offset_row = replace(
        row,
        generated_at=datetime(2026, 6, 30, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert offset_row.generated_at == GENERATED_AT


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_proposal_risk_gate_db_row_rejects_false_report_flags_before_write(
    flag_name: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_db_row as codec

    report = _risk_gate_report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": GENERATED_AT + timedelta(seconds=1)}, "generated_at"),
        ({"config_version": "paper-autonomous-proposal-risk-gate-v1"}, "config_version"),
        ({"gate_status": "watch"}, "gate_status"),
        (
            {"recommended_next_step": "hold_paper_proposal_for_risk_review"},
            "recommended_next_step",
        ),
        ({"source_proposal_status": "blocked"}, "source_proposal_status"),
        ({"source_proposal_count": 2}, "source_proposal_count"),
        (
            {"source_proposal_total_notional": Decimal("9.000000")},
            "source_proposal_total_notional",
        ),
        ({"blocked_reason_codes_json": ["source_proposal_blocked"]}, "blocked_reason_codes_json"),
        ({"watch_reason_codes_json": ["source_proposal_watch"]}, "watch_reason_codes_json"),
        ({"reason_codes_json": ["source_proposal_watch"]}, "reason_codes_json"),
    ),
)
def test_proposal_risk_gate_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_db_row as codec

    row = _db_row()

    with pytest.raises(ValueError, match=message):
        codec.PaperAutonomousProposalRiskGateDbRow(
            **{**_row_values(row), **overrides},
        )
    with pytest.raises(ValueError, match=message):
        replace(row, **overrides)
    malformed = _bypassed_row(row, overrides)
    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("field_name", "payload_value", "message"),
    (
        ("source_proposal_total_notional", 10.5, "float"),
        ("source_proposal_total_notional", Decimal("10.500000"), "raw Decimal"),
        ("generated_at", GENERATED_AT, "raw datetime"),
    ),
)
def test_proposal_risk_gate_db_row_rejects_raw_json_payload_values(
    field_name: str,
    payload_value: object,
    message: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_db_row as codec

    row = _db_row()
    payload = {**row.payload_json, field_name: payload_value}
    sanitized_payload = {
        **row.payload_json,
        field_name: (
            str(payload_value)
            if isinstance(payload_value, Decimal)
            else payload_value.isoformat()
            if isinstance(payload_value, datetime)
            else str(payload_value)
        ),
    }
    malformed = _bypassed_row(
        row,
        {
            "report_sha256": _canonical_payload_sha256(sanitized_payload),
            "payload_json": payload,
        },
    )

    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 30, 12, 0)}, "generated_at"),
        ({"config_version": ""}, "config_version"),
        ({"gate_status": "paused"}, "gate_status"),
        ({"source_proposal_status": "paused"}, "source_proposal_status"),
        ({"source_proposal_count": True}, "source_proposal_count"),
        ({"source_proposal_count": -1}, "source_proposal_count"),
        (
            {"source_proposal_total_notional": Decimal("-1.000000")},
            "source_proposal_total_notional",
        ),
        ({"blocked_reason_codes_json": "source_proposal_blocked"}, "blocked_reason_codes_json"),
        ({"watch_reason_codes_json": "source_proposal_watch"}, "watch_reason_codes_json"),
        ({"reason_codes_json": "reason"}, "reason_codes_json"),
        ({"payload_json": []}, "payload_json"),
        ({"paper_only": False}, "paper_only"),
        ({"report_only": False}, "report_only"),
        ({"readonly": False}, "readonly"),
    ),
)
def test_proposal_risk_gate_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_db_row as codec

    with pytest.raises(ValueError, match=message):
        codec.PaperAutonomousProposalRiskGateDbRow(
            **{**_row_values(_db_row()), **overrides},
        )
