from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.paper_recommendation_health import (
    PaperRecommendationHealthReasonCodeCount,
    PaperRecommendationHealthReport,
)


GENERATED_AT = datetime(2026, 6, 21, 14, 15, tzinfo=UTC)


class HealthReportSubclass(PaperRecommendationHealthReport):
    pass


def _codec_module():
    from polymarket_alpha_lab import paper_recommendation_health_db_row

    return paper_recommendation_health_db_row


def _report() -> PaperRecommendationHealthReport:
    return PaperRecommendationHealthReport(
        generated_at=GENERATED_AT,
        config_version="paper-recommendation-health-v0",
        row_count=4,
        recommend_count=2,
        watch_count=1,
        reject_count=1,
        average_net_probability_edge=Decimal("0.030000"),
        average_total_cost_per_share=Decimal("0.020000"),
        top_recommendation_score=Decimal("0.080000"),
        reason_code_counts=(
            PaperRecommendationHealthReasonCodeCount(
                reason_code="positive_net_edge",
                count=2,
            ),
            PaperRecommendationHealthReasonCodeCount(
                reason_code="wide_spread",
                count=2,
            ),
            PaperRecommendationHealthReasonCodeCount(
                reason_code="below_min_edge",
                count=1,
            ),
        ),
        health_status="pass",
        max_average_cost_per_share=Decimal("0.030000"),
        min_recommend_share=Decimal("0.500000"),
    )


def _row_values(row: object) -> dict[str, object]:
    return dict(row.__dict__)


def _bypassed_row(codec: object, row: object, **overrides: object) -> object:
    row_type = codec.PaperRecommendationHealthDbRow
    bypassed = object.__new__(row_type)
    for field_name, value in {**_row_values(row), **overrides}.items():
        object.__setattr__(bypassed, field_name, value)
    return bypassed


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("DB payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_health_db_row_serializes_canonical_payload_and_round_trips():
    codec = _codec_module()
    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperRecommendationHealthDbRow
    assert len(row.report_sha256) == 64
    assert row.report_sha256 == row.report_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "paper-recommendation-health-v0"
    assert row.health_status == "pass"
    assert row.row_count == 4
    assert row.recommend_count == 2
    assert row.watch_count == 1
    assert row.reject_count == 1
    assert row.average_net_probability_edge == Decimal("0.030000")
    assert row.average_total_cost_per_share == Decimal("0.020000")
    assert row.top_recommendation_score == Decimal("0.080000")
    assert row.reason_code_counts_json == [
        {"reason_code": "positive_net_edge", "count": 2},
        {"reason_code": "wide_spread", "count": 2},
        {"reason_code": "below_min_edge", "count": 1},
    ]
    assert row.max_average_cost_per_share == Decimal("0.030000")
    assert row.min_recommend_share == Decimal("0.500000")
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json["generated_at"] == "2026-06-21T14:15:00+00:00"
    assert row.payload_json["average_net_probability_edge"] == "0.030000"
    assert row.payload_json["average_total_cost_per_share"] == "0.020000"
    assert row.payload_json["top_recommendation_score"] == "0.080000"
    assert row.payload_json["reason_code_counts"] == [
        {"reason_code": "positive_net_edge", "count": 2},
        {"reason_code": "wide_spread", "count": 2},
        {"reason_code": "below_min_edge", "count": 1},
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
    assert codec.from_db_row(row) == report
    assert codec.paper_recommendation_health_to_db_row(report) == row
    assert codec.paper_recommendation_health_from_db_row(row) == report


def test_health_db_row_hash_is_deterministic_for_equivalent_reports():
    codec = _codec_module()
    report = _report()
    same_report = PaperRecommendationHealthReport(**report.__dict__)
    different_report = PaperRecommendationHealthReport(
        **{**report.__dict__, "config_version": "paper-recommendation-health-v1"},
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_health_db_row_is_frozen():
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_health_db_row_rejects_wrong_report_types_and_subclasses():
    codec = _codec_module()

    with pytest.raises(ValueError, match="PaperRecommendationHealthReport"):
        codec.to_db_row(object())

    report = _report()
    with pytest.raises(ValueError, match="PaperRecommendationHealthReport"):
        codec.to_db_row(HealthReportSubclass(**report.__dict__))


def test_health_db_row_rejects_wrong_row_types_and_subclasses():
    codec = _codec_module()
    row = codec.to_db_row(_report())

    class HealthDbRowSubclass(codec.PaperRecommendationHealthDbRow):
        pass

    with pytest.raises(ValueError, match="PaperRecommendationHealthDbRow"):
        codec.from_db_row(object())
    with pytest.raises(ValueError, match="PaperRecommendationHealthDbRow"):
        codec.from_db_row(HealthDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_health_db_row_rejects_false_report_flags_before_write(flag_name: str):
    codec = _codec_module()
    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_health_db_row_constructor_rejects_corrupted_payload_flags():
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="readonly"):
        codec.PaperRecommendationHealthDbRow(
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


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_health_db_row_constructor_rejects_top_level_payload_flag_mismatches(
    flag_name: str,
):
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=flag_name):
        codec.PaperRecommendationHealthDbRow(
            **{
                **_row_values(row),
                "payload_json": {
                    key: value for key, value in row.payload_json.items() if key != flag_name
                },
            },
        )


def test_health_db_row_rejects_floats_in_json_payloads():
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="payload_json"):
        codec.PaperRecommendationHealthDbRow(
            **{**_row_values(row), "payload_json": {**row.payload_json, "bad_float": 0.1}},
        )


def test_health_db_row_constructor_rejects_malformed_payload():
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="health_status"):
        codec.PaperRecommendationHealthDbRow(
            **{
                **_row_values(row),
                "payload_json": {
                    key: value
                    for key, value in row.payload_json.items()
                    if key != "health_status"
                },
            },
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 21, 14, 16, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "paper-recommendation-health-v1"}, "config_version"),
        ({"health_status": "watch"}, "health_status"),
        ({"row_count": 5}, "row_count"),
        ({"recommend_count": 3}, "recommend_count"),
        ({"watch_count": 2}, "watch_count"),
        ({"reject_count": 2}, "reject_count"),
        ({"average_net_probability_edge": Decimal("0.031000")}, "average_net"),
        ({"average_total_cost_per_share": Decimal("0.021000")}, "average_total"),
        ({"top_recommendation_score": Decimal("0.090000")}, "top_recommendation"),
        (
            {"reason_code_counts_json": [{"reason_code": "positive_net_edge", "count": 1}]},
            "reason_code_counts",
        ),
        ({"max_average_cost_per_share": Decimal("0.040000")}, "max_average"),
        ({"min_recommend_share": Decimal("0.600000")}, "min_recommend"),
    ),
)
def test_health_db_row_constructor_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
):
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperRecommendationHealthDbRow(**{**_row_values(row), **overrides})


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"row_count": 5}, "row_count"),
        (
            {
                "payload_json": {
                    "nested_audit": {
                        "paper_only": True,
                        "report_only": True,
                        "readonly": False,
                    },
                },
            },
            "readonly",
        ),
    ),
)
def test_health_from_db_row_rejects_bypassed_constructor_payload_corruption(
    overrides: dict[str, object],
    message: str,
):
    codec = _codec_module()
    row = codec.to_db_row(_report())
    if "payload_json" in overrides:
        overrides = {
            **overrides,
            "payload_json": {**row.payload_json, **overrides["payload_json"]},
        }
    malformed = _bypassed_row(codec, row, **overrides)

    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)


@pytest.mark.parametrize("missing_field", ("payload_json", "row_count"))
def test_health_from_db_row_rejects_bypassed_constructor_missing_fields(
    missing_field: str,
):
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = _bypassed_row(codec, row)
    object.__delattr__(malformed, missing_field)

    with pytest.raises(ValueError, match=missing_field):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"average_net_probability_edge": 0.03}, "average_net_probability_edge"),
        ({"average_total_cost_per_share": Decimal("-0.000001")}, "average_total"),
        ({"top_recommendation_score": Decimal("0.0800001")}, "top_recommendation"),
        ({"reason_code_counts_json": [{"reason_code": "positive_net_edge", "count": 0}]}, "count"),
        ({"min_recommend_share": Decimal("1.000001")}, "min_recommend_share"),
        ({"row_count": True}, "row_count"),
        ({"paper_only": False}, "paper_only"),
    ),
)
def test_health_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
):
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperRecommendationHealthDbRow(**{**_row_values(row), **overrides})


def test_health_db_row_module_is_pure_codec():
    _codec_module()
    source = Path(
        "src/polymarket_alpha_lab/paper_recommendation_health_db_row.py",
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
