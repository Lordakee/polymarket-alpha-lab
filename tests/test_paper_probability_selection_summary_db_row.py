from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_probability_selection_summary import (
    PaperProbabilitySelectionSummaryReport,
    PaperProbabilitySelectionSummaryRow,
)


GENERATED_AT = datetime(2026, 6, 21, 15, 0, tzinfo=UTC)


class SelectionSummaryReportSubclass(PaperProbabilitySelectionSummaryReport):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _codec_module():
    from polymarket_alpha_lab import paper_probability_selection_summary_db_row

    return paper_probability_selection_summary_db_row


def _report() -> PaperProbabilitySelectionSummaryReport:
    rows = (
        PaperProbabilitySelectionSummaryRow(
            queue_rank=1,
            market_slug="event-alpha",
            question="Will event-alpha resolve yes?",
            side="yes",
            action="recommend",
            recommendation_score=d("0.120000"),
            net_probability_edge=d("0.120000"),
            executable_paper_shares=d("100.000000"),
            recommended_next_step="research_review",
            selection_status="ready",
            stress_scenario_count=2,
            stress_pass_count=2,
            stress_watch_count=0,
            stress_fail_count=0,
            worst_stressed_net_probability_edge=d("0.100000"),
            reason_codes=("source_edge", "cost_stress_passed"),
        ),
        PaperProbabilitySelectionSummaryRow(
            queue_rank=2,
            market_slug="event-beta",
            question="Will event-beta resolve no?",
            side="no",
            action="watch",
            recommendation_score=d("0.020000"),
            net_probability_edge=d("0.020000"),
            executable_paper_shares=d("25.000000"),
            recommended_next_step="await_fresh_context",
            selection_status="watch",
            stress_scenario_count=1,
            stress_pass_count=0,
            stress_watch_count=1,
            stress_fail_count=0,
            worst_stressed_net_probability_edge=d("0.015000"),
            reason_codes=("market_context_stale", "source_next_step_await_fresh_context"),
        ),
    )
    return PaperProbabilitySelectionSummaryReport(
        generated_at=GENERATED_AT,
        config_version="paper-probability-selection-summary-v0",
        source_queue_config_version="probability-recommendation-queue-v0",
        source_cost_stress_config_version="paper-cost-stress-v0",
        queue_count=2,
        ready_count=1,
        watch_count=1,
        blocked_count=0,
        missing_stress_count=0,
        rows=rows,
        reason_codes=("watch_selection_rows_present",),
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


def test_selection_summary_db_row_serializes_payload_and_round_trips() -> None:
    codec = _codec_module()
    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperProbabilitySelectionSummaryDbRow
    assert len(row.report_sha256) == 64
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "paper-probability-selection-summary-v0"
    assert row.source_queue_config_version == "probability-recommendation-queue-v0"
    assert row.source_cost_stress_config_version == "paper-cost-stress-v0"
    assert row.queue_count == 2
    assert row.ready_count == 1
    assert row.watch_count == 1
    assert row.blocked_count == 0
    assert row.missing_stress_count == 0
    assert row.rows_json[0] == {
        "queue_rank": 1,
        "market_slug": "event-alpha",
        "question": "Will event-alpha resolve yes?",
        "side": "yes",
        "action": "recommend",
        "recommendation_score": "0.120000",
        "net_probability_edge": "0.120000",
        "executable_paper_shares": "100.000000",
        "recommended_next_step": "research_review",
        "selection_status": "ready",
        "stress_scenario_count": 2,
        "stress_pass_count": 2,
        "stress_watch_count": 0,
        "stress_fail_count": 0,
        "worst_stressed_net_probability_edge": "0.100000",
        "reason_codes": ["source_edge", "cost_stress_passed"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert row.reason_codes_json == ["watch_selection_rows_present"]
    assert row.payload_json["generated_at"] == "2026-06-21T15:00:00+00:00"
    assert row.payload_json["rows"] == row.rows_json
    assert row.payload_json["reason_codes"] == row.reason_codes_json
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    _assert_no_floats(row.payload_json)
    _assert_no_floats(row.rows_json)
    _assert_no_floats(row.reason_codes_json)

    encoded = json.dumps(
        row.payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    assert row.report_sha256 == hashlib.sha256(encoded).hexdigest()
    assert codec.from_db_row(row) == report
    assert codec.paper_probability_selection_summary_report_to_db_row(report) == row
    assert codec.paper_probability_selection_summary_report_from_db_row(row) == report


def test_selection_summary_db_row_hash_is_deterministic() -> None:
    codec = _codec_module()
    report = _report()
    same_report = PaperProbabilitySelectionSummaryReport(**report.__dict__)
    different_report = PaperProbabilitySelectionSummaryReport(
        **{
            **report.__dict__,
            "config_version": "paper-probability-selection-summary-v1",
        },
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_selection_summary_db_row_is_frozen() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_selection_summary_db_row_rejects_wrong_report_types_and_subclasses() -> None:
    codec = _codec_module()

    with pytest.raises(ValueError, match="PaperProbabilitySelectionSummaryReport"):
        codec.to_db_row(object())

    report = _report()
    with pytest.raises(ValueError, match="PaperProbabilitySelectionSummaryReport"):
        codec.to_db_row(SelectionSummaryReportSubclass(**report.__dict__))


def test_selection_summary_db_row_rejects_wrong_row_types_and_subclasses() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    class SelectionSummaryDbRowSubclass(codec.PaperProbabilitySelectionSummaryDbRow):
        pass

    with pytest.raises(ValueError, match="PaperProbabilitySelectionSummaryDbRow"):
        codec.from_db_row(object())
    with pytest.raises(ValueError, match="PaperProbabilitySelectionSummaryDbRow"):
        codec.from_db_row(SelectionSummaryDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_selection_summary_db_row_rejects_false_report_flags_before_write(
    flag_name: str,
) -> None:
    codec = _codec_module()
    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_selection_summary_db_row_rejects_corrupted_nested_payload_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = codec.PaperProbabilitySelectionSummaryDbRow(
        **{
            **_row_values(row),
            "payload_json": {
                **row.payload_json,
                "rows": [
                    {
                        **row.payload_json["rows"][0],
                        "readonly": False,
                    },
                    *row.payload_json["rows"][1:],
                ],
            },
        },
    )

    with pytest.raises(ValueError, match="readonly"):
        codec.from_db_row(malformed)


def test_selection_summary_db_row_rejects_floats_in_json_payloads() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="payload_json"):
        codec.PaperProbabilitySelectionSummaryDbRow(
            **{**_row_values(row), "payload_json": {**row.payload_json, "bad_float": 0.1}},
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 21, 15, 1, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "paper-probability-selection-summary-v1"}, "config_version"),
        ({"source_queue_config_version": "probability-recommendation-queue-v1"}, "source_queue_config_version"),
        ({"source_cost_stress_config_version": "paper-cost-stress-v1"}, "source_cost_stress_config_version"),
        ({"queue_count": 1}, "queue_count"),
        ({"ready_count": 0}, "ready_count"),
        ({"watch_count": 0}, "watch_count"),
        ({"blocked_count": 1}, "blocked_count"),
        ({"missing_stress_count": 1}, "missing_stress_count"),
        ({"rows_json": []}, "rows_json"),
        ({"reason_codes_json": ["ready_selection_rows_present"]}, "reason_codes_json"),
    ),
)
def test_selection_summary_db_row_rejects_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = codec.PaperProbabilitySelectionSummaryDbRow(
        **{**_row_values(row), **overrides},
    )

    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"queue_count": True}, "queue_count"),
        ({"rows_json": "rows"}, "rows_json"),
        ({"rows_json": [{"queue_rank": 1}]}, "rows_json"),
        ({"reason_codes_json": "ready_selection_rows_present"}, "reason_codes_json"),
        ({"reason_codes_json": [1]}, "reason_codes_json"),
        ({"paper_only": False}, "paper_only"),
    ),
)
def test_selection_summary_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperProbabilitySelectionSummaryDbRow(
            **{**_row_values(row), **overrides},
        )


def test_selection_summary_db_row_module_is_pure_paper_only_codec() -> None:
    _codec_module()
    source = Path(
        "src/polymarket_alpha_lab/paper_probability_selection_summary_db_row.py",
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
