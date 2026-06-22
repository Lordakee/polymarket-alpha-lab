from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.paper_recommendation_reason_trend import (
    PaperRecommendationReasonTrendReport,
    PaperRecommendationReasonTrendRow,
    PaperRecommendationTransitionTrendRow,
)


GENERATED_AT = datetime(2026, 6, 22, 13, 45, tzinfo=UTC)
FIRST_SEEN_AT = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
LATEST_SEEN_AT = datetime(2026, 6, 22, 13, 0, tzinfo=UTC)


class ReasonTrendReportSubclass(PaperRecommendationReasonTrendReport):
    pass


def _codec_module():
    from polymarket_alpha_lab import paper_recommendation_reason_trend_db_row

    return paper_recommendation_reason_trend_db_row


def _report() -> PaperRecommendationReasonTrendReport:
    return PaperRecommendationReasonTrendReport(
        generated_at=GENERATED_AT,
        config_version="paper-recommendation-reason-trend-v0",
        source_report_count=3,
        reason_trend_rows=(
            PaperRecommendationReasonTrendRow(
                reason_code="insufficient_edge",
                source_status="watch",
                count=4,
                first_seen_at=FIRST_SEEN_AT,
                latest_seen_at=LATEST_SEEN_AT,
            ),
            PaperRecommendationReasonTrendRow(
                reason_code="low_liquidity",
                source_status="blocked",
                count=2,
                first_seen_at=FIRST_SEEN_AT,
                latest_seen_at=LATEST_SEEN_AT,
            ),
        ),
        transition_trend_rows=(
            PaperRecommendationTransitionTrendRow(
                market_slug="market-a",
                side="yes",
                from_status="watch",
                to_status="blocked",
                transition_count=2,
                latest_transition_at=LATEST_SEEN_AT,
                reason_codes=("low_liquidity",),
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


def test_reason_trend_db_row_serializes_canonical_payload_and_round_trips() -> None:
    codec = _codec_module()
    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperRecommendationReasonTrendDbRow
    assert len(row.report_sha256) == 64
    assert row.report_sha256 == row.report_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "paper-recommendation-reason-trend-v0"
    assert row.source_report_count == 3
    assert row.reason_trend_rows_json == [
        {
            "count": 4,
            "first_seen_at": "2026-06-22T12:00:00+00:00",
            "latest_seen_at": "2026-06-22T13:00:00+00:00",
            "paper_only": True,
            "readonly": True,
            "reason_code": "insufficient_edge",
            "report_only": True,
            "source_status": "watch",
        },
        {
            "count": 2,
            "first_seen_at": "2026-06-22T12:00:00+00:00",
            "latest_seen_at": "2026-06-22T13:00:00+00:00",
            "paper_only": True,
            "readonly": True,
            "reason_code": "low_liquidity",
            "report_only": True,
            "source_status": "blocked",
        },
    ]
    assert row.transition_trend_rows_json == [
        {
            "from_status": "watch",
            "latest_transition_at": "2026-06-22T13:00:00+00:00",
            "market_slug": "market-a",
            "paper_only": True,
            "readonly": True,
            "reason_codes": ["low_liquidity"],
            "report_only": True,
            "side": "yes",
            "to_status": "blocked",
            "transition_count": 2,
        },
    ]
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json["generated_at"] == "2026-06-22T13:45:00+00:00"
    assert row.payload_json["reason_trend_rows"][0]["count"] == 4
    assert row.payload_json["transition_trend_rows"][0]["reason_codes"] == [
        "low_liquidity",
    ]
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    _assert_no_floats(row.payload_json)
    _assert_no_floats(row.reason_trend_rows_json)
    _assert_no_floats(row.transition_trend_rows_json)

    encoded = json.dumps(
        row.payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    assert row.report_sha256 == hashlib.sha256(encoded).hexdigest()
    assert codec.from_db_row(row) == report
    assert codec.paper_recommendation_reason_trend_report_to_db_row(report) == row
    assert codec.paper_recommendation_reason_trend_report_from_db_row(row) == report


def test_reason_trend_db_row_hash_is_deterministic_for_equivalent_reports() -> None:
    codec = _codec_module()
    report = _report()
    same_report = PaperRecommendationReasonTrendReport(**report.__dict__)
    different_report = PaperRecommendationReasonTrendReport(
        **{**report.__dict__, "config_version": "paper-recommendation-reason-trend-v1"},
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_reason_trend_db_row_is_frozen() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_reason_trend_db_row_rejects_wrong_report_types_and_subclasses() -> None:
    codec = _codec_module()

    with pytest.raises(ValueError, match="PaperRecommendationReasonTrendReport"):
        codec.to_db_row(object())

    report = _report()
    with pytest.raises(ValueError, match="PaperRecommendationReasonTrendReport"):
        codec.to_db_row(ReasonTrendReportSubclass(**report.__dict__))


def test_reason_trend_db_row_rejects_wrong_row_types_and_subclasses() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    class ReasonTrendDbRowSubclass(codec.PaperRecommendationReasonTrendDbRow):
        pass

    with pytest.raises(ValueError, match="PaperRecommendationReasonTrendDbRow"):
        codec.from_db_row(object())
    with pytest.raises(ValueError, match="PaperRecommendationReasonTrendDbRow"):
        codec.from_db_row(ReasonTrendDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_reason_trend_db_row_rejects_false_report_flags_before_write(
    flag_name: str,
) -> None:
    codec = _codec_module()
    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_reason_trend_db_row_rejects_corrupted_stored_payload_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = codec.PaperRecommendationReasonTrendDbRow(
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


def test_reason_trend_db_row_rejects_floats_in_json_payloads() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="payload_json"):
        codec.PaperRecommendationReasonTrendDbRow(
            **{**_row_values(row), "payload_json": {**row.payload_json, "bad_float": 0.1}},
        )
    with pytest.raises(ValueError, match="reason_trend_rows_json"):
        codec.PaperRecommendationReasonTrendDbRow(
            **{
                **_row_values(row),
                "reason_trend_rows_json": [
                    {**row.reason_trend_rows_json[0], "bad_float": 0.1},
                ],
            },
        )


def test_reason_trend_db_row_rejects_stored_transition_reason_codes_string() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="transition_trend_rows_json"):
        codec.PaperRecommendationReasonTrendDbRow(
            **{
                **_row_values(row),
                "transition_trend_rows_json": [
                    {**row.transition_trend_rows_json[0], "reason_codes": "abc"},
                ],
            },
        )


def test_reason_trend_db_row_rejects_malformed_stored_payload() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = codec.PaperRecommendationReasonTrendDbRow(
        **{
            **_row_values(row),
            "payload_json": {
                key: value
                for key, value in row.payload_json.items()
                if key != "reason_trend_rows"
            },
        },
    )

    with pytest.raises(ValueError, match="payload_json"):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 22, 13, 46, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "paper-recommendation-reason-trend-v1"}, "config_version"),
        ({"source_report_count": 4}, "source_report_count"),
        ({"reason_trend_rows_json": []}, "reason_trend_rows_json"),
        ({"transition_trend_rows_json": []}, "transition_trend_rows_json"),
    ),
)
def test_reason_trend_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = codec.PaperRecommendationReasonTrendDbRow(
        **{**_row_values(row), **overrides},
    )

    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"source_report_count": True}, "source_report_count"),
        ({"reason_trend_rows_json": {}}, "reason_trend_rows_json"),
        ({"transition_trend_rows_json": {}}, "transition_trend_rows_json"),
        ({"paper_only": False}, "paper_only"),
    ),
)
def test_reason_trend_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperRecommendationReasonTrendDbRow(
            **{**_row_values(row), **overrides},
        )


def test_reason_trend_db_row_module_is_pure_codec() -> None:
    _codec_module()
    source = Path(
        "src/polymarket_alpha_lab/paper_recommendation_reason_trend_db_row.py",
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
