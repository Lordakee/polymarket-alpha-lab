from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab import (
    strategy_candidate_research_queue_history_db_row as db_row_module,
)
from polymarket_alpha_lab.strategy_candidate_research_queue_history import (
    PaperStrategyCandidateResearchQueueHistoryReport,
)


HistoryDbRow = getattr(
    db_row_module,
    "PaperStrategyCandidateResearchQueueHistoryDbRow",
)
from_db_row = getattr(
    db_row_module,
    "paper_strategy_candidate_research_queue_history_report_from_db_row",
)
to_db_row = getattr(
    db_row_module,
    "paper_strategy_candidate_research_queue_history_report_to_db_row",
)

GENERATED_AT = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
FIRST_SOURCE_GENERATED_AT = datetime(2026, 6, 20, 9, 0, tzinfo=UTC)
LAST_SOURCE_GENERATED_AT = datetime(2026, 6, 20, 11, 0, tzinfo=UTC)


class HistoryReportSubclass(PaperStrategyCandidateResearchQueueHistoryReport):
    pass


class HistoryDbRowSubclass(HistoryDbRow):
    pass


def _history_report(
    **overrides: object,
) -> PaperStrategyCandidateResearchQueueHistoryReport:
    values = {
        "generated_at": GENERATED_AT,
        "source_report_count": 3,
        "first_source_generated_at": FIRST_SOURCE_GENERATED_AT,
        "last_source_generated_at": LAST_SOURCE_GENERATED_AT,
        "action_status_research_ready_count": 1,
        "action_status_watch_count": 1,
        "action_status_blocked_count": 1,
        "research_status_ready_count": 1,
        "research_status_watch_count": 1,
        "research_status_blocked_count": 1,
        "total_ready_notional": Decimal("42.000000"),
        "total_selected_notional": Decimal("18.000000"),
        "total_suggested_notional": Decimal("54.000000"),
        "latest_action_status": "research_ready",
        "latest_recommended_next_step": "review_candidate_research_queue",
        "latest_research_status": "ready",
        "latest_top_research_priority_score": Decimal("0.750000"),
        "latest_average_research_ready_score": Decimal("0.650000"),
        "status_transition_count": 2,
        "ready_notional_delta": Decimal("12.000000"),
        "selected_notional_delta": Decimal("6.000000"),
        "latest_selected_count": 2,
        "latest_skipped_count": 1,
        "latest_not_selected_count": 0,
        "latest_primary_reason_code_counts": (
            ("recommendation_ready", 2),
            ("low_net_edge", 1),
        ),
        "latest_reason_codes": (
            "candidate_research_queue_ready",
            "sufficient_depth",
        ),
    }
    values.update(overrides)
    return PaperStrategyCandidateResearchQueueHistoryReport(**values)


def _empty_history_report() -> PaperStrategyCandidateResearchQueueHistoryReport:
    return _history_report(
        source_report_count=0,
        first_source_generated_at=None,
        last_source_generated_at=None,
        action_status_research_ready_count=0,
        action_status_watch_count=0,
        action_status_blocked_count=0,
        research_status_ready_count=0,
        research_status_watch_count=0,
        research_status_blocked_count=0,
        total_ready_notional=Decimal("0.000000"),
        total_selected_notional=Decimal("0.000000"),
        total_suggested_notional=Decimal("0.000000"),
        latest_action_status=None,
        latest_recommended_next_step=None,
        latest_research_status=None,
        latest_top_research_priority_score=None,
        latest_average_research_ready_score=None,
        status_transition_count=0,
        ready_notional_delta=Decimal("0.000000"),
        selected_notional_delta=Decimal("0.000000"),
        latest_selected_count=0,
        latest_skipped_count=0,
        latest_not_selected_count=0,
        latest_primary_reason_code_counts=(),
        latest_reason_codes=(),
    )


def _row_values(
    row: HistoryDbRow,
) -> dict[str, object]:
    return {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at,
        "source_report_count": row.source_report_count,
        "first_source_generated_at": row.first_source_generated_at,
        "last_source_generated_at": row.last_source_generated_at,
        "action_status_research_ready_count": row.action_status_research_ready_count,
        "action_status_watch_count": row.action_status_watch_count,
        "action_status_blocked_count": row.action_status_blocked_count,
        "research_status_ready_count": row.research_status_ready_count,
        "research_status_watch_count": row.research_status_watch_count,
        "research_status_blocked_count": row.research_status_blocked_count,
        "total_ready_notional": row.total_ready_notional,
        "total_selected_notional": row.total_selected_notional,
        "total_suggested_notional": row.total_suggested_notional,
        "latest_action_status": row.latest_action_status,
        "latest_recommended_next_step": row.latest_recommended_next_step,
        "latest_research_status": row.latest_research_status,
        "latest_top_research_priority_score": row.latest_top_research_priority_score,
        "latest_average_research_ready_score": (
            row.latest_average_research_ready_score
        ),
        "status_transition_count": row.status_transition_count,
        "ready_notional_delta": row.ready_notional_delta,
        "selected_notional_delta": row.selected_notional_delta,
        "latest_selected_count": row.latest_selected_count,
        "latest_skipped_count": row.latest_skipped_count,
        "latest_not_selected_count": row.latest_not_selected_count,
        "latest_primary_reason_code_counts_json": (
            row.latest_primary_reason_code_counts_json
        ),
        "latest_reason_codes_json": row.latest_reason_codes_json,
        "payload_json": row.payload_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("DB payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_research_queue_history_db_row_serializes_payload_and_round_trips():
    report = _history_report()

    row = to_db_row(report)

    assert type(row) is HistoryDbRow
    assert len(row.report_sha256) == 64
    assert row.report_sha256 == row.report_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.source_report_count == 3
    assert row.first_source_generated_at == FIRST_SOURCE_GENERATED_AT
    assert row.last_source_generated_at == LAST_SOURCE_GENERATED_AT
    assert row.action_status_research_ready_count == 1
    assert row.action_status_watch_count == 1
    assert row.action_status_blocked_count == 1
    assert row.research_status_ready_count == 1
    assert row.research_status_watch_count == 1
    assert row.research_status_blocked_count == 1
    assert row.total_ready_notional == Decimal("42.000000")
    assert row.total_selected_notional == Decimal("18.000000")
    assert row.total_suggested_notional == Decimal("54.000000")
    assert row.latest_action_status == "research_ready"
    assert row.latest_recommended_next_step == "review_candidate_research_queue"
    assert row.latest_research_status == "ready"
    assert row.latest_top_research_priority_score == Decimal("0.750000")
    assert row.latest_average_research_ready_score == Decimal("0.650000")
    assert row.status_transition_count == 2
    assert row.ready_notional_delta == Decimal("12.000000")
    assert row.selected_notional_delta == Decimal("6.000000")
    assert row.latest_selected_count == 2
    assert row.latest_skipped_count == 1
    assert row.latest_not_selected_count == 0
    assert row.latest_primary_reason_code_counts_json == {
        "recommendation_ready": 2,
        "low_net_edge": 1,
    }
    assert row.latest_reason_codes_json == [
        "candidate_research_queue_ready",
        "sufficient_depth",
    ]
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json["generated_at"] == "2026-06-20T12:00:00+00:00"
    assert (
        row.payload_json["first_source_generated_at"]
        == "2026-06-20T09:00:00+00:00"
    )
    assert (
        row.payload_json["last_source_generated_at"]
        == "2026-06-20T11:00:00+00:00"
    )
    assert row.payload_json["total_ready_notional"] == "42.000000"
    assert row.payload_json["total_selected_notional"] == "18.000000"
    assert row.payload_json["total_suggested_notional"] == "54.000000"
    assert row.payload_json["latest_top_research_priority_score"] == "0.750000"
    assert row.payload_json["latest_average_research_ready_score"] == "0.650000"
    assert row.payload_json["ready_notional_delta"] == "12.000000"
    assert row.payload_json["selected_notional_delta"] == "6.000000"
    assert row.payload_json["latest_primary_reason_code_counts"] == [
        ["recommendation_ready", 2],
        ["low_net_edge", 1],
    ]
    assert row.payload_json["latest_reason_codes"] == [
        "candidate_research_queue_ready",
        "sufficient_depth",
    ]
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
    assert from_db_row(row) == report
    assert (
        to_db_row(PaperStrategyCandidateResearchQueueHistoryReport(**report.__dict__))
        .report_sha256
        == row.report_sha256
    )


def test_research_queue_history_db_row_serializes_empty_history():
    report = _empty_history_report()

    row = to_db_row(report)

    assert row.source_report_count == 0
    assert row.first_source_generated_at is None
    assert row.last_source_generated_at is None
    assert row.latest_action_status is None
    assert row.latest_recommended_next_step is None
    assert row.latest_research_status is None
    assert row.latest_top_research_priority_score is None
    assert row.latest_average_research_ready_score is None
    assert row.status_transition_count == 0
    assert row.total_ready_notional == Decimal("0.000000")
    assert row.total_selected_notional == Decimal("0.000000")
    assert row.total_suggested_notional == Decimal("0.000000")
    assert row.ready_notional_delta == Decimal("0.000000")
    assert row.selected_notional_delta == Decimal("0.000000")
    assert row.latest_selected_count == 0
    assert row.latest_skipped_count == 0
    assert row.latest_not_selected_count == 0
    assert row.latest_primary_reason_code_counts_json == {}
    assert row.latest_reason_codes_json == []
    assert row.payload_json["first_source_generated_at"] is None
    assert row.payload_json["last_source_generated_at"] is None
    assert row.payload_json["latest_action_status"] is None
    assert row.payload_json["latest_recommended_next_step"] is None
    assert row.payload_json["latest_research_status"] is None
    assert row.payload_json["latest_top_research_priority_score"] is None
    assert row.payload_json["latest_average_research_ready_score"] is None
    assert row.payload_json["latest_primary_reason_code_counts"] == []
    assert row.payload_json["latest_reason_codes"] == []
    _assert_no_floats(row.payload_json)

    assert from_db_row(row) == report


def test_research_queue_history_db_row_hash_uses_canonical_full_payload():
    report = _history_report()
    same_report = PaperStrategyCandidateResearchQueueHistoryReport(**report.__dict__)
    different_report = _history_report(
        generated_at=datetime(2026, 6, 20, 12, 1, tzinfo=UTC),
    )

    first = to_db_row(report)
    second = to_db_row(same_report)
    third = to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_research_queue_history_db_row_is_frozen():
    row = to_db_row(_history_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_research_queue_history_db_row_rejects_wrong_report_type_and_subclasses():
    with pytest.raises(
        ValueError,
        match="PaperStrategyCandidateResearchQueueHistoryReport",
    ):
        to_db_row(object())

    report = _history_report()
    subclass = HistoryReportSubclass(**report.__dict__)
    with pytest.raises(
        ValueError,
        match="PaperStrategyCandidateResearchQueueHistoryReport",
    ):
        to_db_row(subclass)


def test_research_queue_history_db_row_rejects_wrong_row_type_and_subclasses():
    with pytest.raises(ValueError, match="HistoryDbRow"):
        from_db_row(object())

    row = to_db_row(_history_report())
    subclass = HistoryDbRowSubclass(**_row_values(row))
    with pytest.raises(ValueError, match="HistoryDbRow"):
        from_db_row(subclass)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_research_queue_history_db_row_rejects_false_report_flags(flag_name: str):
    report = _history_report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        to_db_row(report)


def test_research_queue_history_db_row_rejects_duplicate_reason_shapes_before_write():
    report = _history_report()
    object.__setattr__(
        report,
        "latest_primary_reason_code_counts",
        (("recommendation_ready", 2), ("recommendation_ready", 1)),
    )
    with pytest.raises(ValueError, match="latest_primary_reason_code_counts"):
        to_db_row(report)

    report = _history_report()
    object.__setattr__(
        report,
        "latest_reason_codes",
        ("candidate_research_queue_ready", "candidate_research_queue_ready"),
    )
    with pytest.raises(ValueError, match="latest_reason_codes"):
        to_db_row(report)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_research_queue_history_db_row_rejects_unsafe_stored_payload_flags(
    flag_name: str,
):
    row = to_db_row(_history_report())
    malformed = HistoryDbRow(
        **{
            **_row_values(row),
            "report_sha256": "a" * 64,
            "payload_json": {**row.payload_json, flag_name: False},
        },
    )

    with pytest.raises(ValueError, match=flag_name):
        from_db_row(malformed)


def test_research_queue_history_db_row_rejects_missing_stored_payload_hard_flags():
    row = to_db_row(_history_report())
    payload_without_hard_flags = {
        key: value
        for key, value in row.payload_json.items()
        if key not in ("paper_only", "report_only", "readonly")
    }
    malformed = HistoryDbRow(
        **{
            **_row_values(row),
            "payload_json": payload_without_hard_flags,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )

    with pytest.raises(ValueError, match="paper_only|hard flags"):
        from_db_row(malformed)


def test_research_queue_history_db_row_rejects_deep_unsafe_stored_payload_flags():
    row = to_db_row(_history_report())
    malformed = HistoryDbRow(
        **{
            **_row_values(row),
            "report_sha256": "a" * 64,
            "payload_json": {
                **row.payload_json,
                "audit": {
                    "paper_only": True,
                    "report_only": True,
                    "readonly": False,
                },
            },
        },
    )

    with pytest.raises(ValueError, match="readonly"):
        from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        (
            {"generated_at": datetime(2026, 6, 20, 12, 1, tzinfo=UTC)},
            "generated_at",
        ),
        ({"source_report_count": 4}, "source_report_count"),
        (
            {"first_source_generated_at": datetime(2026, 6, 20, 8, 0, tzinfo=UTC)},
            "first_source_generated_at",
        ),
        (
            {"last_source_generated_at": datetime(2026, 6, 20, 10, 0, tzinfo=UTC)},
            "last_source_generated_at",
        ),
        ({"action_status_research_ready_count": 2}, "action_status_research_ready_count"),
        ({"action_status_watch_count": 2}, "action_status_watch_count"),
        ({"action_status_blocked_count": 2}, "action_status_blocked_count"),
        ({"research_status_ready_count": 2}, "research_status_ready_count"),
        ({"research_status_watch_count": 2}, "research_status_watch_count"),
        ({"research_status_blocked_count": 2}, "research_status_blocked_count"),
        ({"total_ready_notional": Decimal("43.000000")}, "total_ready_notional"),
        ({"total_selected_notional": Decimal("19.000000")}, "total_selected_notional"),
        (
            {"total_suggested_notional": Decimal("55.000000")},
            "total_suggested_notional",
        ),
        (
            {
                "latest_action_status": "watch",
                "latest_recommended_next_step": "await_fresh_cycle_evidence",
            },
            "latest_action_status",
        ),
        ({"latest_research_status": "watch"}, "latest_research_status"),
        (
            {"latest_top_research_priority_score": Decimal("0.700000")},
            "latest_top_research_priority_score",
        ),
        (
            {"latest_average_research_ready_score": Decimal("0.600000")},
            "latest_average_research_ready_score",
        ),
        ({"status_transition_count": 1}, "status_transition_count"),
        ({"ready_notional_delta": Decimal("13.000000")}, "ready_notional_delta"),
        (
            {"selected_notional_delta": Decimal("7.000000")},
            "selected_notional_delta",
        ),
        ({"latest_selected_count": 1}, "latest_selected_count"),
        ({"latest_skipped_count": 2}, "latest_skipped_count"),
        ({"latest_not_selected_count": 1}, "latest_not_selected_count"),
        (
            {"latest_primary_reason_code_counts_json": {"recommendation_ready": 1}},
            "latest_primary_reason_code_counts_json",
        ),
        (
            {"latest_reason_codes_json": ["different_reason"]},
            "latest_reason_codes_json",
        ),
    ),
)
def test_research_queue_history_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    row = to_db_row(_history_report())
    values = _row_values(row)
    values.update(overrides)
    malformed = HistoryDbRow(**values)

    with pytest.raises(ValueError, match=message):
        from_db_row(malformed)


def test_research_queue_history_db_row_wraps_payload_recovery_errors():
    row = to_db_row(_history_report())
    malformed = HistoryDbRow(
        **{
            **_row_values(row),
            "report_sha256": "a" * 64,
            "payload_json": {
                key: value
                for key, value in row.payload_json.items()
                if key != "latest_reason_codes"
            },
        },
    )

    with pytest.raises(ValueError, match="payload_json"):
        from_db_row(malformed)


def test_research_queue_history_db_row_validates_row_shape_and_rejects_floats():
    row = to_db_row(_history_report())

    with pytest.raises(ValueError, match="report_sha256"):
        HistoryDbRow(**{**_row_values(row), "report_sha256": "bad"})

    with pytest.raises(ValueError, match="latest_primary_reason_code_counts_json"):
        HistoryDbRow(
            **{
                **_row_values(row),
                "latest_primary_reason_code_counts_json": {
                    "recommendation_ready": 0,
                },
            },
        )

    with pytest.raises(ValueError, match="latest_reason_codes_json"):
        HistoryDbRow(
            **{
                **_row_values(row),
                "latest_reason_codes_json": ["same_reason", "same_reason"],
            },
        )

    with pytest.raises(ValueError, match="payload_json"):
        HistoryDbRow(
            **{
                **_row_values(row),
                "payload_json": {**row.payload_json, "bad_float": 0.1},
            },
        )

    for flag_name in ("paper_only", "report_only", "readonly"):
        with pytest.raises(ValueError, match=flag_name):
            HistoryDbRow(**{**_row_values(row), flag_name: False})


def test_research_queue_history_db_row_module_remains_pure_codec():
    source_path = Path(db_row_module.__file__)
    tree = ast.parse(source_path.read_text())

    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_parts = {
        "auth",
        "client",
        "exchange",
        "live_trading",
        "network",
        "order",
        "psycopg",
        "sql",
        "wallet",
    }
    for module_name in imported_modules:
        module_parts = set(module_name.split("."))
        assert module_parts.isdisjoint(forbidden_import_parts)
