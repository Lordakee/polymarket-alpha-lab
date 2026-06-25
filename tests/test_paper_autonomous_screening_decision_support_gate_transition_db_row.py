from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re

import pytest

from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition import (
    PaperAutonomousScreeningDecisionSupportGateTransitionReport,
    build_paper_autonomous_screening_decision_support_gate_transition_report,
)
from tests.test_paper_autonomous_screening_decision_support_gate_transition import (
    _gate_report,
)


GENERATED_AT = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)
FIRST_GATE_AT = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
LATEST_GATE_AT = datetime(2026, 6, 24, 12, 0, tzinfo=UTC)
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


class TransitionReportSubclass(PaperAutonomousScreeningDecisionSupportGateTransitionReport):
    pass


def _report(
    *,
    config_version: str = "paper-autonomous-screening-decision-support-gate-transition-v0",
) -> PaperAutonomousScreeningDecisionSupportGateTransitionReport:
    return build_paper_autonomous_screening_decision_support_gate_transition_report(
        [
            _gate_report(generated_at=FIRST_GATE_AT, gate_status="pass"),
            _gate_report(generated_at=LATEST_GATE_AT, gate_status="watch"),
        ],
        config_version=config_version,
        generated_at=GENERATED_AT,
    )


def _empty_report() -> PaperAutonomousScreeningDecisionSupportGateTransitionReport:
    return build_paper_autonomous_screening_decision_support_gate_transition_report(
        [],
        generated_at=GENERATED_AT,
    )


def _row_values(row: object) -> dict[str, object]:
    return dict(row.__dict__)


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
        pytest.fail("transition DB JSON contains floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_transition_db_row_serializes_payload_and_round_trips() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_db_row as codec

    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperAutonomousScreeningDecisionSupportGateTransitionDbRow
    assert SHA256_RE.fullmatch(row.report_sha256)
    assert row.generated_at == GENERATED_AT
    assert (
        row.config_version
        == "paper-autonomous-screening-decision-support-gate-transition-v0"
    )
    assert row.gate_report_count == 2
    assert row.transition_count == 1
    assert row.first_report_generated_at == FIRST_GATE_AT
    assert row.latest_report_generated_at == LATEST_GATE_AT
    assert row.latest_from_gate_status == "pass"
    assert row.latest_to_gate_status == "watch"
    assert row.latest_introduced_reason_codes_json == list(
        report.latest_introduced_reason_codes,
    )
    assert row.latest_cleared_reason_codes_json == list(
        report.latest_cleared_reason_codes,
    )
    assert row.latest_persistent_reason_codes_json == list(
        report.latest_persistent_reason_codes,
    )
    assert isinstance(row.status_transition_rows_json, list)
    assert len(row.status_transition_rows_json) == 9
    assert any(
        item["from_gate_status"] == "pass"
        and item["to_gate_status"] == "watch"
        and item["transition_count"] == 1
        for item in row.status_transition_rows_json
    )
    assert isinstance(row.reason_change_rows_json, list)
    assert row.payload_json["generated_at"] == "2026-06-25T12:00:00+00:00"
    assert row.payload_json["status_transition_rows"] == row.status_transition_rows_json
    assert row.payload_json["reason_change_rows"] == row.reason_change_rows_json
    assert row.payload_json["paper_only"] is True
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    _assert_no_floats(row.payload_json)
    _assert_no_floats(row.status_transition_rows_json)
    _assert_no_floats(row.reason_change_rows_json)

    assert row.report_sha256 == _canonical_payload_sha256(row.payload_json)
    assert codec.from_db_row(row) == report
    assert (
        codec.paper_autonomous_screening_decision_support_gate_transition_report_to_db_row(
            report,
        )
        == row
    )
    assert (
        codec.paper_autonomous_screening_decision_support_gate_transition_report_from_db_row(
            row,
        )
        == report
    )


def test_transition_db_row_hash_is_deterministic() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_db_row as codec

    report = _report()
    same_report = PaperAutonomousScreeningDecisionSupportGateTransitionReport(
        **report.__dict__,
    )
    different_report = _report(
        config_version="paper-autonomous-screening-decision-support-gate-transition-v1",
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_transition_db_row_preserves_empty_transition_report() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_db_row as codec

    report = _empty_report()

    row = codec.to_db_row(report)

    assert row.gate_report_count == 0
    assert row.transition_count == 0
    assert row.first_report_generated_at is None
    assert row.latest_report_generated_at is None
    assert row.latest_from_gate_status is None
    assert row.latest_to_gate_status is None
    assert row.latest_introduced_reason_codes_json == []
    assert row.latest_cleared_reason_codes_json == []
    assert row.latest_persistent_reason_codes_json == []
    assert row.status_transition_rows_json is None
    assert row.reason_change_rows_json is None
    assert codec.from_db_row(row) == report


def test_transition_db_row_is_frozen() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_transition_db_row_rejects_wrong_report_types_and_subclasses() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_db_row as codec

    with pytest.raises(
        ValueError,
        match="PaperAutonomousScreeningDecisionSupportGateTransitionReport",
    ):
        codec.to_db_row(object())

    report = _report()
    subclass = TransitionReportSubclass(**report.__dict__)
    with pytest.raises(
        ValueError,
        match="PaperAutonomousScreeningDecisionSupportGateTransitionReport",
    ):
        codec.to_db_row(subclass)


def test_transition_db_row_rejects_wrong_row_types_and_subclasses() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_db_row as codec

    row = codec.to_db_row(_report())

    class TransitionDbRowSubclass(
        codec.PaperAutonomousScreeningDecisionSupportGateTransitionDbRow,
    ):
        pass

    with pytest.raises(
        ValueError,
        match="PaperAutonomousScreeningDecisionSupportGateTransitionDbRow",
    ):
        codec.from_db_row(object())
    with pytest.raises(
        ValueError,
        match="PaperAutonomousScreeningDecisionSupportGateTransitionDbRow",
    ):
        codec.from_db_row(TransitionDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_transition_db_row_rejects_false_report_flags_before_write(
    flag_name: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_db_row as codec

    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_transition_db_row_rejects_false_nested_row_flags_before_write() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_db_row as codec

    report = _report()
    assert report.status_transition_rows is not None
    object.__setattr__(report.status_transition_rows[0], "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        codec.to_db_row(report)


def test_transition_db_row_rejects_corrupted_stored_payload_flags() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_db_row as codec

    row = codec.to_db_row(_report())
    assert row.status_transition_rows_json is not None
    payload = {
        **row.payload_json,
        "status_transition_rows": [
            {
                **row.status_transition_rows_json[0],
                "paper_only": False,
            },
            *row.status_transition_rows_json[1:],
        ],
    }
    malformed = codec.PaperAutonomousScreeningDecisionSupportGateTransitionDbRow(
        **{
            **_row_values(row),
            "report_sha256": _canonical_payload_sha256(payload),
            "payload_json": payload,
            "status_transition_rows_json": payload["status_transition_rows"],
        },
    )

    with pytest.raises(ValueError, match="paper_only"):
        codec.from_db_row(malformed)


def test_transition_db_row_rejects_recursive_floats_in_json_payloads() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_db_row as codec

    row = codec.to_db_row(_report())
    assert row.status_transition_rows_json is not None

    with pytest.raises(ValueError, match="status_transition_rows_json"):
        replace(
            row,
            status_transition_rows_json=[
                {**row.status_transition_rows_json[0], "transition_count": 1.0},
                *row.status_transition_rows_json[1:],
            ],
        )
    with pytest.raises(ValueError, match="payload_json"):
        replace(row, payload_json={**row.payload_json, "bad_float": 0.1})


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 25, 12, 1, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "transition-v1"}, "config_version"),
        ({"gate_report_count": 3}, "gate_report_count"),
        ({"transition_count": 2}, "transition_count"),
        ({"first_report_generated_at": datetime(2026, 6, 22, tzinfo=UTC)}, "first_report_generated_at"),
        ({"latest_report_generated_at": datetime(2026, 6, 25, tzinfo=UTC)}, "latest_report_generated_at"),
        ({"latest_from_gate_status": "blocked"}, "latest_from_gate_status"),
        ({"latest_to_gate_status": "blocked"}, "latest_to_gate_status"),
        ({"latest_introduced_reason_codes_json": ["extra_reason"]}, "latest_introduced_reason_codes_json"),
    ),
)
def test_transition_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_db_row as codec

    row = codec.to_db_row(_report())
    malformed = codec.PaperAutonomousScreeningDecisionSupportGateTransitionDbRow(
        **{**_row_values(row), **overrides},
    )

    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"config_version": ""}, "config_version"),
        ({"gate_report_count": True}, "gate_report_count"),
        ({"transition_count": -1}, "transition_count"),
        ({"latest_from_gate_status": "paused"}, "latest_from_gate_status"),
        ({"latest_introduced_reason_codes_json": "reason"}, "latest_introduced_reason_codes_json"),
        ({"latest_cleared_reason_codes_json": ["b", "a"]}, "latest_cleared_reason_codes_json"),
        ({"status_transition_rows_json": {"from_gate_status": "pass"}}, "status_transition_rows_json"),
        ({"payload_json": []}, "payload_json"),
        ({"paper_only": False}, "paper_only"),
    ),
)
def test_transition_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperAutonomousScreeningDecisionSupportGateTransitionDbRow(
            **{**_row_values(row), **overrides},
        )


def test_transition_db_row_module_is_pure_codec() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_db_row as codec

    assert codec.__name__.endswith("_db_row")
    source = Path(
        "src/polymarket_alpha_lab/"
        "paper_autonomous_screening_decision_support_gate_transition_db_row.py",
    ).read_text(encoding="utf-8")

    for banned in (
        "psycopg",
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
