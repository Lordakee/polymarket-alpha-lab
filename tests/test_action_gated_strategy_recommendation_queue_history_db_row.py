from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab import (
    action_gated_strategy_recommendation_queue_history_db_row as db_row_module,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_history import (
    PaperActionGatedStrategyRecommendationQueueHistoryReport,
)
from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateReasonCodeCount,
)


HistoryDbRow = getattr(
    db_row_module,
    "PaperActionGatedStrategyRecommendationQueueHistoryDbRow",
)
from_db_row = getattr(
    db_row_module,
    "paper_action_gated_strategy_recommendation_queue_history_report_from_db_row",
)
to_db_row = getattr(
    db_row_module,
    "paper_action_gated_strategy_recommendation_queue_history_report_to_db_row",
)

GENERATED_AT = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
FIRST_SOURCE_GENERATED_AT = datetime(2026, 6, 20, 9, 0, tzinfo=UTC)
LAST_SOURCE_GENERATED_AT = datetime(2026, 6, 20, 11, 0, tzinfo=UTC)


class HistoryReportSubclass(PaperActionGatedStrategyRecommendationQueueHistoryReport):
    pass


class HistoryDbRowSubclass(HistoryDbRow):
    pass


def _reason_count(
    reason_code: str = "cycle_review_passed",
    count: int = 1,
) -> PaperRecommendationCycleActionGateReasonCodeCount:
    return PaperRecommendationCycleActionGateReasonCodeCount(
        reason_code=reason_code,
        count=count,
    )


def _history_report(
    **overrides: object,
) -> PaperActionGatedStrategyRecommendationQueueHistoryReport:
    values = {
        "generated_at": GENERATED_AT,
        "source_report_count": 3,
        "first_source_generated_at": FIRST_SOURCE_GENERATED_AT,
        "last_source_generated_at": LAST_SOURCE_GENERATED_AT,
        "research_ready_count": 1,
        "watch_count": 1,
        "blocked_count": 1,
        "total_ready_notional": Decimal("42.000000"),
        "latest_action_status": "research_ready",
        "latest_recommended_next_step": "review_candidate_research_queue",
        "status_transition_count": 2,
        "ready_notional_delta": Decimal("12.000000"),
        "latest_reason_code_counts": (_reason_count(),),
    }
    values.update(overrides)
    return PaperActionGatedStrategyRecommendationQueueHistoryReport(**values)


def _empty_history_report() -> PaperActionGatedStrategyRecommendationQueueHistoryReport:
    return _history_report(
        source_report_count=0,
        first_source_generated_at=None,
        last_source_generated_at=None,
        research_ready_count=0,
        watch_count=0,
        blocked_count=0,
        total_ready_notional=Decimal("0.000000"),
        latest_action_status=None,
        latest_recommended_next_step=None,
        status_transition_count=0,
        ready_notional_delta=Decimal("0.000000"),
        latest_reason_code_counts=(),
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
        "research_ready_count": row.research_ready_count,
        "watch_count": row.watch_count,
        "blocked_count": row.blocked_count,
        "total_ready_notional": row.total_ready_notional,
        "latest_action_status": row.latest_action_status,
        "latest_recommended_next_step": row.latest_recommended_next_step,
        "status_transition_count": row.status_transition_count,
        "ready_notional_delta": row.ready_notional_delta,
        "latest_reason_code_counts_json": row.latest_reason_code_counts_json,
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


def _payload_sha256(payload_json: dict[str, object]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _bypassed_history_row(row: HistoryDbRow, **overrides: object) -> HistoryDbRow:
    values = _row_values(row)
    values.update(overrides)
    bypassed = object.__new__(HistoryDbRow)
    for field_name, value in values.items():
        object.__setattr__(bypassed, field_name, value)
    return bypassed


def test_action_gated_queue_history_db_row_serializes_payload_and_round_trips():
    report = _history_report()

    row = to_db_row(
        report,
    )

    assert type(row) is HistoryDbRow
    assert len(row.report_sha256) == 64
    assert row.report_sha256 == row.report_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.source_report_count == 3
    assert row.first_source_generated_at == FIRST_SOURCE_GENERATED_AT
    assert row.last_source_generated_at == LAST_SOURCE_GENERATED_AT
    assert row.research_ready_count == 1
    assert row.watch_count == 1
    assert row.blocked_count == 1
    assert row.total_ready_notional == Decimal("42.000000")
    assert row.latest_action_status == "research_ready"
    assert row.latest_recommended_next_step == "review_candidate_research_queue"
    assert row.status_transition_count == 2
    assert row.ready_notional_delta == Decimal("12.000000")
    assert row.latest_reason_code_counts_json == {"cycle_review_passed": 1}
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
    assert row.payload_json["ready_notional_delta"] == "12.000000"
    assert row.payload_json["latest_reason_code_counts"] == [
        {"reason_code": "cycle_review_passed", "count": 1},
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
    assert (
        from_db_row(
            row,
        )
        == report
    )
    assert (
        to_db_row(
            PaperActionGatedStrategyRecommendationQueueHistoryReport(**report.__dict__),
        ).report_sha256
        == row.report_sha256
    )


def test_action_gated_queue_history_db_row_serializes_empty_history():
    report = _empty_history_report()

    row = to_db_row(
        report,
    )

    assert row.source_report_count == 0
    assert row.first_source_generated_at is None
    assert row.last_source_generated_at is None
    assert row.latest_action_status is None
    assert row.latest_recommended_next_step is None
    assert row.status_transition_count == 0
    assert row.total_ready_notional == Decimal("0.000000")
    assert row.ready_notional_delta == Decimal("0.000000")
    assert row.latest_reason_code_counts_json == {}
    assert row.payload_json["first_source_generated_at"] is None
    assert row.payload_json["last_source_generated_at"] is None
    assert row.payload_json["latest_action_status"] is None
    assert row.payload_json["latest_recommended_next_step"] is None
    assert row.payload_json["latest_reason_code_counts"] == []
    _assert_no_floats(row.payload_json)

    assert (
        from_db_row(
            row,
        )
        == report
    )


def test_action_gated_queue_history_db_row_hash_uses_canonical_full_payload():
    report = _history_report()
    same_report = PaperActionGatedStrategyRecommendationQueueHistoryReport(
        **report.__dict__,
    )
    different_report = _history_report(
        generated_at=datetime(2026, 6, 20, 12, 1, tzinfo=UTC),
    )

    first = to_db_row(
        report,
    )
    second = to_db_row(
        same_report,
    )
    third = to_db_row(
        different_report,
    )

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_action_gated_queue_history_db_row_canonicalizes_equivalent_decimal_writes():
    integerish_report = _history_report()
    object.__setattr__(
        integerish_report,
        "total_ready_notional",
        Decimal("42"),
    )
    object.__setattr__(
        integerish_report,
        "ready_notional_delta",
        Decimal("12"),
    )
    six_place_report = _history_report()
    object.__setattr__(
        six_place_report,
        "total_ready_notional",
        Decimal("42.000000"),
    )
    object.__setattr__(
        six_place_report,
        "ready_notional_delta",
        Decimal("12.000000"),
    )

    integerish_row = to_db_row(
        integerish_report,
    )
    six_place_row = to_db_row(
        six_place_report,
    )

    assert integerish_row.payload_json["total_ready_notional"] == "42.000000"
    assert integerish_row.payload_json["ready_notional_delta"] == "12.000000"
    assert integerish_row.payload_json == six_place_row.payload_json
    assert integerish_row.report_sha256 == six_place_row.report_sha256


def test_action_gated_queue_history_db_row_rejects_overprecision_decimal_writes():
    report = _history_report()
    object.__setattr__(
        report,
        "total_ready_notional",
        Decimal("42.0000004"),
    )

    with pytest.raises(ValueError, match="total_ready_notional|Decimal"):
        to_db_row(
            report,
        )


def test_action_gated_queue_history_db_row_is_frozen():
    row = to_db_row(
        _history_report(),
    )

    with pytest.raises(FrozenInstanceError):
        row.paper_only = False  # type: ignore[misc]


def test_action_gated_queue_history_db_row_rejects_wrong_report_type_and_subclasses():
    with pytest.raises(
        ValueError,
        match="PaperActionGatedStrategyRecommendationQueueHistoryReport",
    ):
        to_db_row(
            object(),
        )

    report = _history_report()
    subclass = HistoryReportSubclass(**report.__dict__)
    with pytest.raises(
        ValueError,
        match="PaperActionGatedStrategyRecommendationQueueHistoryReport",
    ):
        to_db_row(
            subclass,
        )


def test_action_gated_queue_history_db_row_rejects_wrong_row_type_and_subclasses():
    with pytest.raises(
        ValueError,
        match="HistoryDbRow",
    ):
        from_db_row(
            object(),
        )

    row = to_db_row(
        _history_report(),
    )
    subclass = HistoryDbRowSubclass(**_row_values(row))
    with pytest.raises(
        ValueError,
        match="HistoryDbRow",
    ):
        from_db_row(
            subclass,
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_action_gated_queue_history_db_row_rejects_false_report_flags(flag_name: str):
    report = _history_report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        to_db_row(
            report,
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_action_gated_queue_history_db_row_constructor_rejects_unsafe_stored_payload_flags(
    flag_name: str,
):
    row = to_db_row(
        _history_report(),
    )
    payload_json = {**row.payload_json, flag_name: False}

    with pytest.raises(ValueError, match=flag_name):
        HistoryDbRow(
            **{
                **_row_values(row),
                "report_sha256": _payload_sha256(payload_json),
                "payload_json": payload_json,
            },
        )


def test_action_gated_queue_history_db_row_constructor_rejects_latest_nested_payload_flags():
    row = to_db_row(
        _history_report(),
    )
    latest_reason_code_counts = list(row.payload_json["latest_reason_code_counts"])
    latest_reason_code_counts[0] = {
        **latest_reason_code_counts[0],
        "paper_only": True,
        "report_only": True,
        "readonly": False,
    }
    payload_json = {
        **row.payload_json,
        "latest_reason_code_counts": latest_reason_code_counts,
    }

    with pytest.raises(ValueError, match="readonly"):
        HistoryDbRow(
            **{
                **_row_values(row),
                "report_sha256": _payload_sha256(payload_json),
                "payload_json": payload_json,
            },
        )


def test_action_gated_queue_history_db_row_constructor_rejects_payload_that_cannot_recover():
    row = to_db_row(
        _history_report(),
    )
    payload_json = {**row.payload_json, "unexpected_field": "not-a-report-field"}

    with pytest.raises(ValueError, match="payload_json"):
        HistoryDbRow(
            **{
                **_row_values(row),
                "report_sha256": _payload_sha256(payload_json),
                "payload_json": payload_json,
            },
        )


def test_action_gated_queue_history_db_row_constructor_rejects_bool_payload_int_count():
    row = to_db_row(
        _history_report(),
    )
    payload_json = {**row.payload_json, "research_ready_count": True}

    with pytest.raises(ValueError, match="payload_json|research_ready_count"):
        HistoryDbRow(
            **{
                **_row_values(row),
                "report_sha256": _payload_sha256(payload_json),
                "payload_json": payload_json,
            },
        )


def test_action_gated_queue_history_db_row_constructor_rejects_self_hashed_noncanonical_decimal():
    row = to_db_row(
        _history_report(),
    )
    payload_json = {**row.payload_json, "total_ready_notional": "42"}

    with pytest.raises(ValueError, match="payload_json|total_ready_notional"):
        HistoryDbRow(
            **{
                **_row_values(row),
                "report_sha256": _payload_sha256(payload_json),
                "total_ready_notional": Decimal("42"),
                "payload_json": payload_json,
            },
        )


def test_action_gated_queue_history_db_row_replace_revalidates_payload_consistency():
    row = to_db_row(
        _history_report(),
    )

    with pytest.raises(ValueError, match="source_report_count"):
        replace(row, source_report_count=row.source_report_count + 1)


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
        ({"research_ready_count": 2}, "research_ready_count"),
        ({"watch_count": 2}, "watch_count"),
        ({"blocked_count": 2}, "blocked_count"),
        ({"total_ready_notional": Decimal("43.000000")}, "total_ready_notional"),
        (
            {
                "latest_action_status": "watch",
                "latest_recommended_next_step": "await_fresh_cycle_evidence",
            },
            "latest_action_status",
        ),
        ({"status_transition_count": 1}, "status_transition_count"),
        ({"ready_notional_delta": Decimal("13.000000")}, "ready_notional_delta"),
        (
            {"latest_reason_code_counts_json": {"cycle_review_passed": 2}},
            "latest_reason_code_counts_json",
        ),
    ),
)
def test_action_gated_queue_history_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    row = to_db_row(
        _history_report(),
    )
    values = _row_values(row)
    values.update(overrides)

    with pytest.raises(ValueError, match=message):
        HistoryDbRow(**values)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"source_report_count": 4}, "action status counts"),
        (
            {"first_source_generated_at": None},
            "first_source_generated_at",
        ),
        (
            {"last_source_generated_at": datetime(2026, 6, 20, 8, 0, tzinfo=UTC)},
            "last_source_generated_at",
        ),
        ({"latest_action_status": None, "latest_recommended_next_step": None}, "latest_action_status"),
        ({"status_transition_count": 3}, "status_transition_count"),
    ),
)
def test_action_gated_queue_history_db_row_constructor_rejects_history_invariants(
    overrides: dict[str, object],
    message: str,
) -> None:
    row = to_db_row(
        _history_report(),
    )
    values = _row_values(row)
    values.update(overrides)
    payload_overrides = {
        field_name: values[field_name]
        for field_name in overrides
        if field_name in row.payload_json
    }
    payload_json = {
        **row.payload_json,
        **{
            field_name: (
                value.isoformat() if isinstance(value, datetime) else str(value)
                if isinstance(value, Decimal)
                else value
            )
            for field_name, value in payload_overrides.items()
        },
    }
    values.update(
        {
            "report_sha256": _payload_sha256(payload_json),
            "payload_json": payload_json,
        },
    )

    with pytest.raises(ValueError, match=message):
        HistoryDbRow(**values)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        (
            {"first_source_generated_at": FIRST_SOURCE_GENERATED_AT},
            "first_source_generated_at",
        ),
        (
            {"last_source_generated_at": LAST_SOURCE_GENERATED_AT},
            "last_source_generated_at",
        ),
        (
            {"latest_action_status": "watch", "latest_recommended_next_step": "await_fresh_cycle_evidence"},
            "latest_action_status",
        ),
        (
            {"total_ready_notional": Decimal("1.000000")},
            "total_ready_notional",
        ),
        (
            {"ready_notional_delta": Decimal("1.000000")},
            "ready_notional_delta",
        ),
        (
            {"latest_reason_code_counts_json": {"cycle_review_passed": 1}},
            "latest_reason_code_counts_json",
        ),
    ),
)
def test_action_gated_queue_history_empty_db_row_constructor_rejects_history_invariants(
    overrides: dict[str, object],
    message: str,
) -> None:
    row = to_db_row(
        _empty_history_report(),
    )
    values = _row_values(row)
    values.update(overrides)
    payload_json = {
        **row.payload_json,
        **{
            field_name: (
                value.isoformat() if isinstance(value, datetime) else str(value)
                if isinstance(value, Decimal)
                else value
            )
            for field_name, value in overrides.items()
            if field_name in row.payload_json
        },
    }
    if "latest_reason_code_counts_json" in overrides:
        payload_json["latest_reason_code_counts"] = [
            {"reason_code": reason_code, "count": count}
            for reason_code, count in values[
                "latest_reason_code_counts_json"
            ].items()
        ]
    values.update(
        {
            "report_sha256": _payload_sha256(payload_json),
            "payload_json": payload_json,
        },
    )

    with pytest.raises(ValueError, match=message):
        HistoryDbRow(**values)


def test_action_gated_queue_history_db_row_from_db_row_rejects_bypassed_payload_mismatch():
    row = to_db_row(
        _history_report(),
    )
    malformed = _bypassed_history_row(
        row,
        source_report_count=row.source_report_count + 1,
    )

    with pytest.raises(ValueError, match="source_report_count"):
        from_db_row(
            malformed,
        )


def test_action_gated_queue_history_db_row_from_db_row_rejects_bypassed_payload_recovery_error():
    row = to_db_row(
        _history_report(),
    )
    payload_json = {**row.payload_json, "unexpected_field": "not-a-report-field"}
    malformed = _bypassed_history_row(
        row,
        report_sha256=_payload_sha256(payload_json),
        payload_json=payload_json,
    )

    with pytest.raises(ValueError, match="payload_json"):
        from_db_row(
            malformed,
        )


def test_action_gated_queue_history_db_row_from_db_row_rejects_bypassed_bool_materialized_int():
    row = to_db_row(
        _history_report(),
    )
    malformed = _bypassed_history_row(row, research_ready_count=True)

    with pytest.raises(ValueError, match="research_ready_count"):
        from_db_row(
            malformed,
        )


def test_action_gated_queue_history_db_row_from_db_row_rejects_bypassed_bool_materialized_reason_count():
    row = to_db_row(
        _history_report(),
    )
    malformed = _bypassed_history_row(
        row,
        latest_reason_code_counts_json={"cycle_review_passed": True},
    )

    with pytest.raises(ValueError, match="latest_reason_code_counts_json"):
        from_db_row(
            malformed,
        )


def test_action_gated_queue_history_db_row_from_db_row_accepts_equivalent_materialized_decimal_scale():
    report = _history_report()
    row = to_db_row(
        report,
    )
    equivalent = _bypassed_history_row(
        row,
        total_ready_notional=Decimal("42"),
        ready_notional_delta=Decimal("12"),
    )

    assert (
        from_db_row(
            equivalent,
        )
        == report
    )


def test_action_gated_queue_history_db_row_from_db_row_rejects_bypassed_self_hashed_legacy_decimal_payload():
    row = to_db_row(
        _history_report(),
    )
    payload_json = {
        **row.payload_json,
        "total_ready_notional": "42",
        "ready_notional_delta": "12",
    }
    malformed = _bypassed_history_row(
        row,
        report_sha256=_payload_sha256(payload_json),
        total_ready_notional=Decimal("42"),
        ready_notional_delta=Decimal("12"),
        payload_json=payload_json,
    )

    with pytest.raises(ValueError, match="total_ready_notional"):
        from_db_row(
            malformed,
        )


def test_action_gated_queue_history_db_row_from_db_row_rejects_bypassed_missing_nested_payload_hard_flag():
    row = to_db_row(
        _history_report(),
    )
    latest_reason_code_counts = list(row.payload_json["latest_reason_code_counts"])
    latest_reason_code_counts[0] = {
        **latest_reason_code_counts[0],
        "paper_only": True,
        "report_only": True,
    }
    payload_json = {
        **row.payload_json,
        "latest_reason_code_counts": latest_reason_code_counts,
    }
    malformed = _bypassed_history_row(
        row,
        report_sha256=_payload_sha256(payload_json),
        payload_json=payload_json,
    )

    with pytest.raises(ValueError, match="readonly"):
        from_db_row(
            malformed,
        )


def test_action_gated_queue_history_db_row_from_db_row_rejects_bypassed_missing_all_payload_hard_flags():
    row = to_db_row(
        _history_report(),
    )
    payload_json = {
        key: value
        for key, value in row.payload_json.items()
        if key not in ("paper_only", "report_only", "readonly")
    }
    malformed = _bypassed_history_row(
        row,
        report_sha256=row.report_sha256,
        payload_json=payload_json,
    )

    with pytest.raises(ValueError, match="report_sha256|payload_json"):
        from_db_row(
            malformed,
        )


def test_action_gated_queue_history_db_row_wraps_payload_recovery_errors():
    row = to_db_row(
        _history_report(),
    )
    payload_json = {
        key: value
        for key, value in row.payload_json.items()
        if key != "latest_reason_code_counts"
    }

    with pytest.raises(ValueError, match="payload_json"):
        HistoryDbRow(
            **{
                **_row_values(row),
                "report_sha256": _payload_sha256(payload_json),
                "payload_json": payload_json,
            },
        )


def test_action_gated_queue_history_db_row_validates_row_shape_and_rejects_floats():
    row = to_db_row(
        _history_report(),
    )

    with pytest.raises(ValueError, match="report_sha256"):
        HistoryDbRow(
            **{**_row_values(row), "report_sha256": "bad"},
        )

    with pytest.raises(ValueError, match="latest_reason_code_counts_json"):
        HistoryDbRow(
            **{
                **_row_values(row),
                "latest_reason_code_counts_json": {"cycle_review_passed": 0},
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
            HistoryDbRow(
                **{**_row_values(row), flag_name: False},
            )


def test_action_gated_queue_db_row_module_remains_pure_codec():
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
