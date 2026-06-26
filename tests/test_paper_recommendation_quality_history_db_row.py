from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.paper_recommendation_quality_history import (
    PaperRecommendationQualityHistoryRecurringSubreportRow,
    PaperRecommendationQualityHistoryReport,
    PaperRecommendationQualityHistoryStatusRow,
)


GENERATED_AT = datetime(2026, 6, 22, 18, 0, tzinfo=UTC)
FIRST_SOURCE_AT = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
LATEST_SOURCE_AT = datetime(2026, 6, 22, 14, 0, tzinfo=UTC)


class QualityHistoryReportSubclass(PaperRecommendationQualityHistoryReport):
    pass


def _codec_module():
    from polymarket_alpha_lab import paper_recommendation_quality_history_db_row

    return paper_recommendation_quality_history_db_row


def _report() -> PaperRecommendationQualityHistoryReport:
    return PaperRecommendationQualityHistoryReport(
        generated_at=GENERATED_AT,
        config_version="paper-recommendation-quality-history-v0",
        history_status="watch",
        source_report_count=3,
        first_source_generated_at=FIRST_SOURCE_AT,
        latest_source_generated_at=LATEST_SOURCE_AT,
        summary_status_rows=(
            PaperRecommendationQualityHistoryStatusRow("pass", 2),
            PaperRecommendationQualityHistoryStatusRow("watch", 1),
            PaperRecommendationQualityHistoryStatusRow("blocked", 0),
            PaperRecommendationQualityHistoryStatusRow("incomplete", 0),
        ),
        duplicate_generated_at_count=1,
        recurring_blocked_reason_codes=("empty_selection",),
        recurring_incomplete_subreports=(
            PaperRecommendationQualityHistoryRecurringSubreportRow("health", 2),
        ),
        reason_codes=(
            "duplicate_generated_at_threshold_exceeded",
            "recurring_incomplete_subreports_present",
        ),
    )


def _empty_report() -> PaperRecommendationQualityHistoryReport:
    return PaperRecommendationQualityHistoryReport(
        generated_at=GENERATED_AT,
        config_version="paper-recommendation-quality-history-v0",
        history_status="blocked",
        source_report_count=0,
        first_source_generated_at=None,
        latest_source_generated_at=None,
        summary_status_rows=(
            PaperRecommendationQualityHistoryStatusRow("pass", 0),
            PaperRecommendationQualityHistoryStatusRow("watch", 0),
            PaperRecommendationQualityHistoryStatusRow("blocked", 0),
            PaperRecommendationQualityHistoryStatusRow("incomplete", 0),
        ),
        duplicate_generated_at_count=0,
        recurring_blocked_reason_codes=(),
        recurring_incomplete_subreports=(),
        reason_codes=("insufficient_quality_summary_history",),
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


def test_quality_history_db_row_serializes_payload_and_round_trips() -> None:
    codec = _codec_module()
    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperRecommendationQualityHistoryDbRow
    assert len(row.report_sha256) == 64
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "paper-recommendation-quality-history-v0"
    assert row.history_status == "watch"
    assert row.source_report_count == 3
    assert row.first_source_generated_at == FIRST_SOURCE_AT
    assert row.latest_source_generated_at == LATEST_SOURCE_AT
    assert row.summary_status_rows_json == [
        {
            "summary_status": "pass",
            "status_count": 2,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "summary_status": "watch",
            "status_count": 1,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "summary_status": "blocked",
            "status_count": 0,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "summary_status": "incomplete",
            "status_count": 0,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    assert row.pass_summary_count == 2
    assert row.watch_summary_count == 1
    assert row.blocked_summary_count == 0
    assert row.incomplete_summary_count == 0
    assert row.duplicate_generated_at_count == 1
    assert row.recurring_blocked_reason_codes_json == ["empty_selection"]
    assert row.recurring_incomplete_subreports_json == [
        {
            "report_name": "health",
            "incomplete_count": 2,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    assert row.recurring_incomplete_subreport_count == 1
    assert row.reason_codes_json == [
        "duplicate_generated_at_threshold_exceeded",
        "recurring_incomplete_subreports_present",
    ]
    assert row.reason_code_count == 2
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json["summary_status_rows"] == row.summary_status_rows_json
    assert row.payload_json["recurring_blocked_reason_codes"] == ["empty_selection"]
    assert row.payload_json["recurring_incomplete_subreports"] == (
        row.recurring_incomplete_subreports_json
    )
    assert row.payload_json["reason_codes"] == row.reason_codes_json
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    _assert_no_floats(row.payload_json)
    _assert_no_floats(row.summary_status_rows_json)
    _assert_no_floats(row.recurring_incomplete_subreports_json)

    encoded = json.dumps(
        row.payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    assert row.report_sha256 == hashlib.sha256(encoded).hexdigest()
    assert codec.from_db_row(row) == report
    assert codec.paper_recommendation_quality_history_report_to_db_row(report) == row
    assert codec.paper_recommendation_quality_history_report_from_db_row(row) == report


def test_quality_history_db_row_handles_empty_source_history() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_empty_report())

    assert row.source_report_count == 0
    assert row.first_source_generated_at is None
    assert row.latest_source_generated_at is None
    assert row.pass_summary_count == 0
    assert row.watch_summary_count == 0
    assert row.blocked_summary_count == 0
    assert row.incomplete_summary_count == 0
    assert row.recurring_blocked_reason_codes_json == []
    assert row.recurring_incomplete_subreports_json == []
    assert row.reason_codes_json == ["insufficient_quality_summary_history"]
    assert codec.from_db_row(row) == _empty_report()


def test_quality_history_db_row_hash_is_deterministic() -> None:
    codec = _codec_module()
    report = _report()
    same_report = PaperRecommendationQualityHistoryReport(**report.__dict__)
    different_report = PaperRecommendationQualityHistoryReport(
        **{**report.__dict__, "config_version": "paper-recommendation-quality-history-v1"},
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_quality_history_db_row_is_frozen() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_quality_history_db_row_rejects_wrong_report_types_and_subclasses() -> None:
    codec = _codec_module()

    with pytest.raises(ValueError, match="PaperRecommendationQualityHistoryReport"):
        codec.to_db_row(object())

    report = _report()
    with pytest.raises(ValueError, match="PaperRecommendationQualityHistoryReport"):
        codec.to_db_row(QualityHistoryReportSubclass(**report.__dict__))


def test_quality_history_db_row_rejects_wrong_row_types_and_subclasses() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    class QualityHistoryDbRowSubclass(codec.PaperRecommendationQualityHistoryDbRow):
        pass

    with pytest.raises(ValueError, match="PaperRecommendationQualityHistoryDbRow"):
        codec.from_db_row(object())
    with pytest.raises(ValueError, match="PaperRecommendationQualityHistoryDbRow"):
        codec.from_db_row(QualityHistoryDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_quality_history_db_row_rejects_false_report_flags_before_write(
    flag_name: str,
) -> None:
    codec = _codec_module()
    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_quality_history_db_row_rejects_false_nested_report_flags_before_write() -> None:
    codec = _codec_module()
    report = _report()
    object.__setattr__(report.summary_status_rows[0], "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        codec.to_db_row(report)


def test_quality_history_db_row_rejects_corrupted_payload_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="readonly"):
        codec.PaperRecommendationQualityHistoryDbRow(
            **{
                **_row_values(row),
                "payload_json": {
                    **row.payload_json,
                    "nested_audit": {
                        "paper_only": True,
                        "report_only": True,
                        "readonly": False,
                    },
                },
            },
        )


def test_quality_history_db_row_rejects_floats_in_json_payloads() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="payload_json"):
        codec.PaperRecommendationQualityHistoryDbRow(
            **{**_row_values(row), "payload_json": {**row.payload_json, "bad_float": 0.1}},
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 22, 18, 1, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "paper-recommendation-quality-history-v1"}, "config_version"),
        ({"history_status": "pass"}, "history_status"),
        ({"source_report_count": 4}, "source_report_count"),
        ({"first_source_generated_at": datetime(2026, 6, 22, 11, 0, tzinfo=UTC)}, "first_source_generated_at"),
        ({"latest_source_generated_at": datetime(2026, 6, 22, 15, 0, tzinfo=UTC)}, "latest_source_generated_at"),
        ({"pass_summary_count": 3}, "pass_summary_count"),
        ({"watch_summary_count": 0}, "watch_summary_count"),
        ({"duplicate_generated_at_count": 0}, "duplicate_generated_at_count"),
        ({"recurring_blocked_reason_codes_json": []}, "recurring_blocked_reason_codes"),
        ({"recurring_incomplete_subreport_count": 0}, "recurring_incomplete_subreport_count"),
        ({"reason_codes_json": ["quality_summary_history_passed"]}, "reason_codes"),
        ({"reason_code_count": 1}, "reason_code_count"),
    ),
)
def test_quality_history_db_row_rejects_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperRecommendationQualityHistoryDbRow(
            **{**_row_values(row), **overrides},
        )


def test_quality_history_db_row_rejects_replaced_payload_mismatches() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="pass_summary_count"):
        replace(row, pass_summary_count=3)


def test_quality_history_from_db_row_rejects_bypassed_payload_mismatches() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = object.__new__(codec.PaperRecommendationQualityHistoryDbRow)
    for field_name, value in {
        **_row_values(row),
        "pass_summary_count": 3,
    }.items():
        object.__setattr__(malformed, field_name, value)

    with pytest.raises(ValueError, match="pass_summary_count"):
        codec.from_db_row(malformed)


def test_quality_history_from_db_row_rejects_bypassed_nested_payload_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = object.__new__(codec.PaperRecommendationQualityHistoryDbRow)
    for field_name, value in {
        **_row_values(row),
        "payload_json": {
            **row.payload_json,
            "nested_audit": {
                "paper_only": True,
                "report_only": True,
                "readonly": False,
            },
        },
    }.items():
        object.__setattr__(malformed, field_name, value)

    with pytest.raises(ValueError, match="readonly"):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"history_status": "stable"}, "history_status"),
        ({"source_report_count": True}, "source_report_count"),
        ({"first_source_generated_at": "2026-06-22T12:00:00+00:00"}, "first_source_generated_at"),
        ({"summary_status_rows_json": "pass"}, "summary_status_rows_json"),
        ({"summary_status_rows_json": [{"summary_status": "pass", "status_count": 2, "bad_float": 0.1}]}, "summary_status_rows_json"),
        ({"summary_status_rows_json": [{"summary_status": "stable", "status_count": 2, "paper_only": True, "report_only": True, "readonly": True}]}, "summary_status_rows_json"),
        ({"pass_summary_count": -1}, "pass_summary_count"),
        ({"recurring_blocked_reason_codes_json": [1]}, "recurring_blocked_reason_codes_json"),
        ({"recurring_incomplete_subreports_json": ["health"]}, "recurring_incomplete_subreports_json"),
        ({"recurring_incomplete_subreports_json": [{"report_name": "unknown", "incomplete_count": 2, "paper_only": True, "report_only": True, "readonly": True}]}, "recurring_incomplete_subreports_json"),
        ({"reason_codes_json": []}, "reason_codes_json"),
        ({"reason_codes_json": [1]}, "reason_codes_json"),
        ({"paper_only": False}, "paper_only"),
    ),
)
def test_quality_history_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperRecommendationQualityHistoryDbRow(
            **{**_row_values(row), **overrides},
        )


def test_quality_history_db_row_module_is_pure_codec() -> None:
    _codec_module()
    source = Path(
        "src/polymarket_alpha_lab/paper_recommendation_quality_history_db_row.py",
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
