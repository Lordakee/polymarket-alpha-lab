from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
import re

import pytest

from tests.test_paper_autonomous_allocation_proposal_db_history_health import (
    GENERATED_AT,
    _health_report,
    _history_report,
    d,
)


SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def _db_row():
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_db_row as codec

    return codec.to_db_row(_report())


def _report():
    return _health_report(
        (
            _history_report(
                latest_report_generated_at=GENERATED_AT - timedelta(seconds=1_800),
            ),
            _history_report(
                latest_report_generated_at=GENERATED_AT - timedelta(seconds=1_200),
            ),
            _history_report(
                latest_report_generated_at=GENERATED_AT - timedelta(seconds=600),
                latest_allocated_count=5,
                latest_total_allocated_paper_notional=d("42.000000"),
            ),
        ),
    )


def _empty_report():
    return _health_report(())


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
        pytest.fail("health DB JSON contains floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_health_db_row_serializes_payload_and_round_trips() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_db_row as codec

    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperAutonomousAllocationProposalDbHistoryHealthDbRow
    assert SHA256_RE.fullmatch(row.report_sha256)
    assert row.generated_at == GENERATED_AT
    assert row.config_version == (
        "paper-autonomous-allocation-proposal-db-history-health-v0"
    )
    assert row.health_status == "pass"
    assert row.recommended_next_step == (
        "allow_paper_autonomous_allocation_proposal_history_review"
    )
    assert row.history_report_count == 3
    assert row.pass_report_count == 3
    assert row.watch_report_count == 0
    assert row.blocked_report_count == 0
    assert row.latest_history_status == "pass"
    assert row.latest_proposal_status == "pass"
    assert row.latest_allocated_count == 5
    assert row.latest_total_allocated_paper_notional == d("42.000000")
    assert type(row.latest_total_allocated_paper_notional) is Decimal
    assert row.max_source_age_seconds == 1_800
    assert row.latest_source_age_seconds == 600
    assert row.duplicate_latest_report_generated_at_count == 0
    assert row.reason_codes_json == [
        "paper_autonomous_allocation_proposal_db_history_health_passed",
    ]
    assert row.reason_code_counts_json == [
        {
            "reason_code": "paper_autonomous_allocation_proposal_db_history_passed",
            "report_count": 3,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json["generated_at"] == "2026-06-24T18:00:00+00:00"
    assert row.payload_json["latest_total_allocated_paper_notional"] == "42.000000"
    assert row.payload_json["reason_code_counts"][0]["readonly"] is True
    _assert_no_floats(row.reason_code_counts_json)
    _assert_no_floats(row.reason_codes_json)
    _assert_no_floats(row.payload_json)

    assert row.report_sha256 == _canonical_payload_sha256(row.payload_json)
    assert codec.from_db_row(row) == report
    assert (
        codec.paper_autonomous_allocation_proposal_db_history_health_report_to_db_row(
            report,
        )
        == row
    )
    assert (
        codec.paper_autonomous_allocation_proposal_db_history_health_report_from_db_row(
            row,
        )
        == report
    )


def test_health_db_row_hash_is_deterministic_for_equivalent_reports() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_db_row as codec
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health import (
        PaperAutonomousAllocationProposalDbHistoryHealthReport,
    )

    report = _report()
    same_report = PaperAutonomousAllocationProposalDbHistoryHealthReport(
        **report.__dict__,
    )
    different_report = _health_report(
        (
            _history_report(
                latest_report_generated_at=GENERATED_AT - timedelta(seconds=2_400),
            ),
            _history_report(
                latest_report_generated_at=GENERATED_AT - timedelta(seconds=1_200),
            ),
            _history_report(
                latest_report_generated_at=GENERATED_AT - timedelta(seconds=600),
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
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_db_row as codec
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health import (
        PaperAutonomousAllocationProposalDbHistoryHealthReport,
    )

    with pytest.raises(ValueError, match="PaperAutonomousAllocationProposalDbHistoryHealthReport"):
        codec.to_db_row(object())

    with pytest.raises(TypeError, match="HealthReport .*subclassing"):
        class ReportSubclass(PaperAutonomousAllocationProposalDbHistoryHealthReport):
            pass


def test_health_db_row_rejects_wrong_row_types_and_subclasses() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_db_row as codec

    row = _db_row()

    class HealthDbRowSubclass(codec.PaperAutonomousAllocationProposalDbHistoryHealthDbRow):
        pass

    with pytest.raises(ValueError, match="PaperAutonomousAllocationProposalDbHistoryHealthDbRow"):
        codec.from_db_row(object())
    with pytest.raises(ValueError, match="PaperAutonomousAllocationProposalDbHistoryHealthDbRow"):
        codec.from_db_row(HealthDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_health_db_row_rejects_false_report_flags_before_write(
    flag_name: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_db_row as codec

    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_health_db_row_rejects_false_nested_reason_count_flags() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_db_row as codec

    report = _report()
    object.__setattr__(report.reason_code_counts[0], "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        codec.to_db_row(report)


def test_health_db_row_rejects_corrupted_stored_payload_flags() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_db_row as codec

    row = _db_row()
    reason_code_counts = [
        {
            **row.payload_json["reason_code_counts"][0],
            "paper_only": False,
        },
    ]
    payload = {**row.payload_json, "reason_code_counts": reason_code_counts}
    malformed = codec.PaperAutonomousAllocationProposalDbHistoryHealthDbRow(
        **{
            **_row_values(row),
            "report_sha256": _canonical_payload_sha256(payload),
            "payload_json": payload,
            "reason_code_counts_json": reason_code_counts,
        },
    )

    with pytest.raises(ValueError, match="paper_only"):
        codec.from_db_row(malformed)


def test_health_db_row_rejects_non_materialized_payload_hash_mismatch() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_db_row as codec

    row = _db_row()
    payload = {**row.payload_json, "paper_only": False}
    malformed = codec.PaperAutonomousAllocationProposalDbHistoryHealthDbRow(
        **{
            **_row_values(row),
            "payload_json": payload,
        },
    )

    with pytest.raises(ValueError, match="report_sha256"):
        codec.from_db_row(malformed)


def test_health_db_row_rejects_recursive_floats_in_json_payloads() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_db_row as codec

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
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_db_row as codec

    report = _empty_report()

    row = codec.to_db_row(report)

    assert row.history_report_count == 0
    assert row.health_status == "blocked"
    assert row.latest_history_status is None
    assert row.latest_proposal_status is None
    assert row.latest_allocated_count is None
    assert row.latest_total_allocated_paper_notional is None
    assert row.max_source_age_seconds is None
    assert row.latest_source_age_seconds is None
    assert row.reason_code_counts_json == []
    assert codec.from_db_row(row) == report


def test_health_db_row_normalizes_aware_datetimes_to_utc() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_db_row as codec

    row = codec.to_db_row(_report())
    offset_row = replace(
        row,
        generated_at=datetime(2026, 6, 24, 14, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert offset_row.generated_at == GENERATED_AT


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": GENERATED_AT + timedelta(seconds=1)}, "generated_at"),
        (
            {"config_version": "paper-autonomous-allocation-proposal-db-history-health-v1"},
            "config_version",
        ),
        (
            {
                "health_status": "watch",
                "recommended_next_step": (
                    "throttle_paper_autonomous_allocation_proposal_history_review"
                ),
            },
            "health_status",
        ),
        (
            {"history_report_count": 4, "pass_report_count": 4},
            "history_report_count",
        ),
        ({"pass_report_count": 2, "watch_report_count": 1}, "pass_report_count"),
        ({"latest_history_status": "watch"}, "latest_history_status"),
        ({"latest_proposal_status": "watch"}, "latest_proposal_status"),
        ({"latest_allocated_count": 4}, "latest_allocated_count"),
        (
            {"latest_total_allocated_paper_notional": d("41.000000")},
            "latest_total_allocated_paper_notional",
        ),
        ({"max_source_age_seconds": 1_799}, "max_source_age_seconds"),
        ({"latest_source_age_seconds": 599}, "latest_source_age_seconds"),
        (
            {"duplicate_latest_report_generated_at_count": 1},
            "duplicate_latest_report_generated_at_count",
        ),
        ({"reason_codes_json": ["stale_allocation_proposal_db_history"]}, "reason_codes_json"),
        ({"reason_code_counts_json": []}, "reason_code_counts_json"),
    ),
)
def test_health_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_db_row as codec

    row = _db_row()
    malformed = codec.PaperAutonomousAllocationProposalDbHistoryHealthDbRow(
        **{**_row_values(row), **overrides},
    )

    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("status", "next_step"),
    (
        ("pass", "throttle_paper_autonomous_allocation_proposal_history_review"),
        ("watch", "allow_paper_autonomous_allocation_proposal_history_review"),
        ("blocked", "throttle_paper_autonomous_allocation_proposal_history_review"),
    ),
)
def test_health_db_row_rejects_health_status_next_step_mismatches(
    status: str,
    next_step: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_db_row as codec

    with pytest.raises(ValueError, match="recommended_next_step"):
        codec.PaperAutonomousAllocationProposalDbHistoryHealthDbRow(
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
        ({"generated_at": datetime(2026, 6, 24, 18, 0)}, "generated_at"),
        ({"config_version": ""}, "config_version"),
        ({"health_status": "paused"}, "health_status"),
        ({"history_report_count": True}, "history_report_count"),
        ({"history_report_count": -1}, "history_report_count"),
        ({"pass_report_count": 2}, "history_report_count"),
        ({"latest_history_status": "paused"}, "latest_history_status"),
        ({"latest_allocated_count": -1}, "latest_allocated_count"),
        (
            {"latest_total_allocated_paper_notional": d("-1.000000")},
            "latest_total_allocated_paper_notional",
        ),
        ({"max_source_age_seconds": -1}, "max_source_age_seconds"),
        ({"latest_source_age_seconds": True}, "latest_source_age_seconds"),
        ({"duplicate_latest_report_generated_at_count": -1}, "duplicate_latest_report_generated_at_count"),
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
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_db_row as codec

    with pytest.raises(ValueError, match=message):
        codec.PaperAutonomousAllocationProposalDbHistoryHealthDbRow(
            **{**_row_values(_db_row()), **overrides},
        )
