from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.paper_recommendation_quality_summary import (
    PaperRecommendationQualityReasonCodeCount,
    PaperRecommendationQualitySubreportSummary,
    PaperRecommendationQualitySummaryReport,
)


GENERATED_AT = datetime(2026, 6, 22, 21, 0, tzinfo=UTC)
SOURCE_AT = datetime(2026, 6, 22, 20, 0, tzinfo=UTC)


class QualitySummaryReportSubclass(PaperRecommendationQualitySummaryReport):
    pass


def _codec_module():
    from polymarket_alpha_lab import paper_recommendation_quality_summary_db_row

    return paper_recommendation_quality_summary_db_row


def _report() -> PaperRecommendationQualitySummaryReport:
    subreports = (
        PaperRecommendationQualitySubreportSummary(
            report_name="health",
            status="pass",
            generated_at=SOURCE_AT,
            config_version="paper-recommendation-health-v0",
            row_count=3,
            reason_codes=("positive_net_edge", "wide_spread"),
        ),
        PaperRecommendationQualitySubreportSummary(
            report_name="consistency",
            status="watch",
            generated_at=SOURCE_AT,
            config_version="paper-recommendation-consistency-v0",
            row_count=2,
            reason_codes=("wide_spread",),
        ),
        PaperRecommendationQualitySubreportSummary(
            report_name="risk_budget",
            status="pass",
            generated_at=SOURCE_AT,
            config_version="paper-recommendation-risk-budget-v0",
            row_count=2,
            reason_codes=("risk_budget_passed",),
        ),
        PaperRecommendationQualitySubreportSummary(
            report_name="reason_trend",
            status="watch",
            generated_at=SOURCE_AT,
            config_version="paper-recommendation-reason-trend-v0",
            row_count=2,
            reason_codes=("new_reason_code",),
        ),
        PaperRecommendationQualitySubreportSummary(
            report_name="rank_stability",
            status="pass",
            generated_at=SOURCE_AT,
            config_version="paper-strategy-recommendation-rank-stability-v0",
            row_count=1,
            reason_codes=("stable_ready_candidates_present",),
        ),
    )
    reason_code_counts = (
        PaperRecommendationQualityReasonCodeCount(
            reason_code="wide_spread",
            subreport_count=2,
        ),
        PaperRecommendationQualityReasonCodeCount(
            reason_code="new_reason_code",
            subreport_count=1,
        ),
        PaperRecommendationQualityReasonCodeCount(
            reason_code="positive_net_edge",
            subreport_count=1,
        ),
        PaperRecommendationQualityReasonCodeCount(
            reason_code="risk_budget_passed",
            subreport_count=1,
        ),
        PaperRecommendationQualityReasonCodeCount(
            reason_code="stable_ready_candidates_present",
            subreport_count=1,
        ),
    )
    return PaperRecommendationQualitySummaryReport(
        generated_at=GENERATED_AT,
        config_version="paper-recommendation-quality-summary-v0",
        summary_status="watch",
        subreport_count=5,
        pass_count=3,
        watch_count=2,
        blocked_count=0,
        incomplete_count=0,
        reason_code_counts=reason_code_counts,
        reason_codes=tuple(row.reason_code for row in reason_code_counts),
        subreports=subreports,
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


def test_quality_summary_db_row_serializes_payload_and_round_trips() -> None:
    codec = _codec_module()
    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperRecommendationQualitySummaryDbRow
    assert len(row.report_sha256) == 64
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "paper-recommendation-quality-summary-v0"
    assert row.summary_status == "watch"
    assert row.subreport_count == 5
    assert row.pass_count == 3
    assert row.watch_count == 2
    assert row.blocked_count == 0
    assert row.incomplete_count == 0
    assert row.reason_code_counts_json == [
        {"reason_code": "wide_spread", "subreport_count": 2},
        {"reason_code": "new_reason_code", "subreport_count": 1},
        {"reason_code": "positive_net_edge", "subreport_count": 1},
        {"reason_code": "risk_budget_passed", "subreport_count": 1},
        {"reason_code": "stable_ready_candidates_present", "subreport_count": 1},
    ]
    assert row.reason_codes_json == [
        "wide_spread",
        "new_reason_code",
        "positive_net_edge",
        "risk_budget_passed",
        "stable_ready_candidates_present",
    ]
    assert row.subreports_json[0] == {
        "report_name": "health",
        "status": "pass",
        "generated_at": "2026-06-22T20:00:00+00:00",
        "config_version": "paper-recommendation-health-v0",
        "row_count": 3,
        "reason_codes": ["positive_net_edge", "wide_spread"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json["generated_at"] == "2026-06-22T21:00:00+00:00"
    assert row.payload_json["reason_code_counts"] == row.reason_code_counts_json
    assert row.payload_json["reason_codes"] == row.reason_codes_json
    assert row.payload_json["subreports"] == row.subreports_json
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    _assert_no_floats(row.payload_json)
    _assert_no_floats(row.reason_code_counts_json)
    _assert_no_floats(row.reason_codes_json)
    _assert_no_floats(row.subreports_json)

    encoded = json.dumps(
        row.payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    assert row.report_sha256 == hashlib.sha256(encoded).hexdigest()
    assert codec.from_db_row(row) == report
    assert codec.paper_recommendation_quality_summary_report_to_db_row(report) == row
    assert codec.paper_recommendation_quality_summary_report_from_db_row(row) == report


def test_quality_summary_db_row_hash_is_deterministic() -> None:
    codec = _codec_module()
    report = _report()
    same_report = PaperRecommendationQualitySummaryReport(**report.__dict__)
    different_report = PaperRecommendationQualitySummaryReport(
        **{
            **report.__dict__,
            "config_version": "paper-recommendation-quality-summary-v1",
        },
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_quality_summary_db_row_is_frozen() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_quality_summary_db_row_rejects_wrong_report_types_and_subclasses() -> None:
    codec = _codec_module()

    with pytest.raises(ValueError, match="PaperRecommendationQualitySummaryReport"):
        codec.to_db_row(object())

    report = _report()
    with pytest.raises(ValueError, match="PaperRecommendationQualitySummaryReport"):
        codec.to_db_row(QualitySummaryReportSubclass(**report.__dict__))


def test_quality_summary_db_row_rejects_wrong_row_types_and_subclasses() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    class QualitySummaryDbRowSubclass(codec.PaperRecommendationQualitySummaryDbRow):
        pass

    with pytest.raises(ValueError, match="PaperRecommendationQualitySummaryDbRow"):
        codec.from_db_row(object())
    with pytest.raises(ValueError, match="PaperRecommendationQualitySummaryDbRow"):
        codec.from_db_row(QualitySummaryDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_quality_summary_db_row_rejects_false_report_flags_before_write(
    flag_name: str,
) -> None:
    codec = _codec_module()
    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_quality_summary_db_row_rejects_corrupted_nested_payload_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="readonly"):
        codec.PaperRecommendationQualitySummaryDbRow(
            **{
                **_row_values(row),
                "payload_json": {
                    **row.payload_json,
                    "subreports": [
                        *row.payload_json["subreports"][:-1],
                        {
                            **row.payload_json["subreports"][-1],
                            "readonly": False,
                        },
                    ],
                },
            },
        )


def test_quality_summary_db_row_rejects_floats_in_json_payloads() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="payload_json"):
        codec.PaperRecommendationQualitySummaryDbRow(
            **{**_row_values(row), "payload_json": {**row.payload_json, "bad_float": 0.1}},
        )


def test_quality_summary_db_row_serializes_future_decimal_payload_values_as_strings() -> None:
    codec = _codec_module()
    report = _report()

    payload = codec._json_ready({"future_decimal": Decimal("0.125000")})

    assert payload == {"future_decimal": "0.125000"}


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 22, 21, 1, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "paper-recommendation-quality-summary-v1"}, "config_version"),
        ({"summary_status": "blocked"}, "summary_status"),
        ({"subreport_count": 4}, "subreport_count"),
        ({"pass_count": 2}, "pass_count"),
        ({"watch_count": 1}, "watch_count"),
        ({"blocked_count": 1}, "blocked_count"),
        ({"incomplete_count": 1}, "incomplete_count"),
        (
            {"reason_code_counts_json": [{"reason_code": "wide_spread", "subreport_count": 1}]},
            "reason_code_counts",
        ),
        ({"reason_codes_json": ["wide_spread"]}, "reason_codes"),
        ({"subreports_json": []}, "subreports"),
    ),
)
def test_quality_summary_db_row_rejects_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperRecommendationQualitySummaryDbRow(
            **{**_row_values(row), **overrides},
        )


def test_quality_summary_db_row_rejects_replaced_payload_mismatches() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="pass_count"):
        replace(row, pass_count=2)


def test_quality_summary_from_db_row_rejects_bypassed_payload_mismatches() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = object.__new__(codec.PaperRecommendationQualitySummaryDbRow)
    for field_name, value in {
        **_row_values(row),
        "reason_codes_json": ["wide_spread"],
    }.items():
        object.__setattr__(malformed, field_name, value)

    with pytest.raises(ValueError, match="reason_codes"):
        codec.from_db_row(malformed)


def test_quality_summary_from_db_row_rejects_bypassed_nested_payload_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = object.__new__(codec.PaperRecommendationQualitySummaryDbRow)
    for field_name, value in {
        **_row_values(row),
        "payload_json": {
            **row.payload_json,
            "subreports": [
                *row.payload_json["subreports"][:-1],
                {
                    **row.payload_json["subreports"][-1],
                    "readonly": False,
                },
            ],
        },
    }.items():
        object.__setattr__(malformed, field_name, value)

    with pytest.raises(ValueError, match="readonly"):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"summary_status": "stable"}, "summary_status"),
        ({"subreport_count": True}, "subreport_count"),
        (
            {"reason_code_counts_json": [{"reason_code": "wide_spread", "subreport_count": 0}]},
            "subreport_count",
        ),
        ({"reason_codes_json": "wide_spread"}, "reason_codes_json"),
        ({"reason_codes_json": [1]}, "reason_codes_json"),
        ({"subreports_json": "health"}, "subreports_json"),
        ({"subreports_json": [{"report_name": "health"}]}, "subreports_json"),
        ({"paper_only": False}, "paper_only"),
    ),
)
def test_quality_summary_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperRecommendationQualitySummaryDbRow(
            **{**_row_values(row), **overrides},
        )


def test_quality_summary_db_row_module_is_pure_paper_only_codec() -> None:
    _codec_module()
    source = Path(
        "src/polymarket_alpha_lab/paper_recommendation_quality_summary_db_row.py",
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
