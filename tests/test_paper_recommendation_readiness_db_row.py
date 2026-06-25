from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.paper_recommendation_readiness import (
    PaperRecommendationReadinessReport,
    PaperRecommendationReadinessRow,
)


GENERATED_AT = datetime(2026, 6, 25, 8, 30, tzinfo=UTC)


class ReadinessReportSubclass(PaperRecommendationReadinessReport):
    pass


def _codec_module():
    from polymarket_alpha_lab import paper_recommendation_readiness_db_row

    return paper_recommendation_readiness_db_row


def _report() -> PaperRecommendationReadinessReport:
    return PaperRecommendationReadinessReport(
        generated_at=GENERATED_AT,
        config_version="paper-recommendation-readiness-v0",
        input_count=5,
        row_count=3,
        ready_count=1,
        watch_count=1,
        blocked_count=1,
        top_adjusted_net_probability_edge=Decimal("0.070000"),
        total_cost_per_share=Decimal("0.045000"),
        rows=(
            PaperRecommendationReadinessRow(
                market_slug="alpha",
                side="yes",
                readiness_status="ready",
                gate_count=2,
                pass_gate_count=2,
                watch_gate_count=0,
                blocked_gate_count=0,
                adjusted_net_probability_edge=Decimal("0.070000"),
                total_cost_per_share=Decimal("0.015000"),
                reason_codes=("side_edge_passed", "thresholds_passed"),
            ),
            PaperRecommendationReadinessRow(
                market_slug="beta",
                side="no",
                readiness_status="watch",
                gate_count=2,
                pass_gate_count=1,
                watch_gate_count=1,
                blocked_gate_count=0,
                adjusted_net_probability_edge=Decimal("0.040000"),
                total_cost_per_share=Decimal("0.020000"),
                reason_codes=("readiness_watch_gate", "settlement_context_stale"),
            ),
            PaperRecommendationReadinessRow(
                market_slug="gamma",
                side="yes",
                readiness_status="blocked",
                gate_count=1,
                pass_gate_count=0,
                watch_gate_count=0,
                blocked_gate_count=1,
                adjusted_net_probability_edge=Decimal("0.010000"),
                total_cost_per_share=Decimal("0.010000"),
                reason_codes=("ambiguous_outcome_definition", "readiness_blocked_gate"),
            ),
        ),
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


def test_readiness_db_row_serializes_canonical_payload_and_round_trips():
    codec = _codec_module()
    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperRecommendationReadinessDbRow
    assert len(row.report_sha256) == 64
    assert row.report_sha256 == row.report_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "paper-recommendation-readiness-v0"
    assert row.input_count == 5
    assert row.row_count == 3
    assert row.ready_count == 1
    assert row.watch_count == 1
    assert row.blocked_count == 1
    assert row.top_adjusted_net_probability_edge == Decimal("0.070000")
    assert row.total_cost_per_share == Decimal("0.045000")
    assert row.readiness_status_counts_json == {
        "ready": 1,
        "watch": 1,
        "blocked": 1,
    }
    assert row.payload_json["generated_at"] == "2026-06-25T08:30:00+00:00"
    assert row.payload_json["top_adjusted_net_probability_edge"] == "0.070000"
    assert row.payload_json["total_cost_per_share"] == "0.045000"
    assert row.payload_json["rows"][0]["adjusted_net_probability_edge"] == "0.070000"
    assert row.payload_json["rows"][0]["total_cost_per_share"] == "0.015000"
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
    assert codec.paper_recommendation_readiness_to_db_row(report) == row
    assert codec.paper_recommendation_readiness_from_db_row(row) == report


def test_readiness_db_row_hash_is_deterministic_for_equivalent_reports():
    codec = _codec_module()
    report = _report()
    same_report = PaperRecommendationReadinessReport(**report.__dict__)
    different_report = PaperRecommendationReadinessReport(
        **{**report.__dict__, "config_version": "paper-recommendation-readiness-v1"},
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_readiness_db_row_is_frozen():
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_readiness_db_row_rejects_wrong_report_types_and_subclasses():
    codec = _codec_module()

    with pytest.raises(ValueError, match="PaperRecommendationReadinessReport"):
        codec.to_db_row(object())

    report = _report()
    with pytest.raises(ValueError, match="PaperRecommendationReadinessReport"):
        codec.to_db_row(ReadinessReportSubclass(**report.__dict__))


def test_readiness_db_row_rejects_wrong_row_types_and_subclasses():
    codec = _codec_module()
    row = codec.to_db_row(_report())

    class ReadinessDbRowSubclass(codec.PaperRecommendationReadinessDbRow):
        pass

    with pytest.raises(ValueError, match="PaperRecommendationReadinessDbRow"):
        codec.from_db_row(object())
    with pytest.raises(ValueError, match="PaperRecommendationReadinessDbRow"):
        codec.from_db_row(ReadinessDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_readiness_db_row_rejects_false_report_flags_before_write(flag_name: str):
    codec = _codec_module()
    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_readiness_db_row_rejects_corrupted_stored_payload_flags():
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = codec.PaperRecommendationReadinessDbRow(
        **{
            **_row_values(row),
            "payload_json": {
                **row.payload_json,
                "nested_audit": {"paper_only": True, "report_only": True, "readonly": False},
            },
        },
    )

    with pytest.raises(ValueError, match="readonly"):
        codec.from_db_row(malformed)


def test_readiness_db_row_rejects_floats_in_json_payloads():
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="payload_json"):
        codec.PaperRecommendationReadinessDbRow(
            **{**_row_values(row), "payload_json": {**row.payload_json, "bad_float": 0.1}},
        )


def test_readiness_db_row_rejects_malformed_stored_payload():
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = codec.PaperRecommendationReadinessDbRow(
        **{
            **_row_values(row),
            "payload_json": {
                key: value for key, value in row.payload_json.items() if key != "row_count"
            },
        },
    )

    with pytest.raises(ValueError, match="payload_json"):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 25, 8, 31, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "paper-recommendation-readiness-v1"}, "config_version"),
        ({"input_count": 6}, "input_count"),
        ({"row_count": 4}, "row_count"),
        ({"ready_count": 2}, "ready_count"),
        ({"watch_count": 2}, "watch_count"),
        ({"blocked_count": 2}, "blocked_count"),
        ({"top_adjusted_net_probability_edge": Decimal("0.060000")}, "top_adjusted"),
        ({"total_cost_per_share": Decimal("0.046000")}, "total_cost"),
        ({"readiness_status_counts_json": {"ready": 2, "watch": 1, "blocked": 0}}, "readiness_status_counts"),
    ),
)
def test_readiness_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
):
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = codec.PaperRecommendationReadinessDbRow(**{**_row_values(row), **overrides})

    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"input_count": True}, "input_count"),
        ({"top_adjusted_net_probability_edge": 0.07}, "top_adjusted_net_probability_edge"),
        ({"total_cost_per_share": Decimal("-0.000001")}, "total_cost_per_share"),
        ({"readiness_status_counts_json": {"ready": 1, "watch": 1}}, "readiness_status_counts"),
        ({"readiness_status_counts_json": {"ready": 1, "watch": 1, "blocked": True}}, "blocked"),
        ({"paper_only": False}, "paper_only"),
    ),
)
def test_readiness_db_row_validates_stored_row_fields(
    overrides: dict[str, object],
    message: str,
):
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperRecommendationReadinessDbRow(**{**_row_values(row), **overrides})


def test_readiness_db_row_rejects_non_canonical_json_objects():
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="JSON object keys"):
        codec.PaperRecommendationReadinessDbRow(
            **{
                **_row_values(row),
                "payload_json": {**row.payload_json, 1: "bad"},
            },
        )
