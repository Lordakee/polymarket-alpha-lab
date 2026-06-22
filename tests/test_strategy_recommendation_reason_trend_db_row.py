from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_recommendation_reason_trend import (
    NO_REASON_CODE,
    PaperStrategyRecommendationReasonTrendReport,
    PaperStrategyRecommendationReasonTrendSourceSummary,
)


GENERATED_AT = datetime(2026, 6, 20, 15, 30, tzinfo=UTC)


class ReasonTrendReportSubclass(PaperStrategyRecommendationReasonTrendReport):
    pass


def _codec_module():
    from polymarket_alpha_lab import strategy_recommendation_reason_trend_db_row

    return strategy_recommendation_reason_trend_db_row


def _report() -> PaperStrategyRecommendationReasonTrendReport:
    source_summaries = (
        PaperStrategyRecommendationReasonTrendSourceSummary(
            generated_at=datetime(2026, 6, 20, 14, 0, tzinfo=UTC),
            config_version="strategy-recommendation-bundle-v1",
            primary_reason_code_counts=(
                ("alpha_reason", 2),
                ("blocked_forecast_quality", 1),
            ),
            reason_code_count=3,
            no_reason_code_count=0,
        ),
        PaperStrategyRecommendationReasonTrendSourceSummary(
            generated_at=datetime(2026, 6, 20, 15, 0, tzinfo=UTC),
            config_version="strategy-recommendation-explain-v1",
            primary_reason_code_counts=(
                ("new_reason", 2),
                ("alpha_reason", 1),
                (NO_REASON_CODE, 1),
            ),
            reason_code_count=4,
            no_reason_code_count=1,
        ),
    )
    return PaperStrategyRecommendationReasonTrendReport(
        generated_at=GENERATED_AT,
        config_version="strategy-recommendation-reason-trend-v0",
        source_report_count=2,
        first_generated_at=source_summaries[0].generated_at,
        latest_generated_at=source_summaries[1].generated_at,
        latest_primary_reason_code_counts=source_summaries[1].primary_reason_code_counts,
        total_primary_reason_code_counts=(
            ("alpha_reason", 3),
            ("new_reason", 2),
            ("blocked_forecast_quality", 1),
            (NO_REASON_CODE, 1),
        ),
        top_new_reason_codes=(("new_reason", 2), (NO_REASON_CODE, 1)),
        persistent_reason_codes=("alpha_reason",),
        latest_reason_code_count=4,
        latest_no_reason_code_count=1,
        latest_blocked_reason_count=0,
        latest_no_reason_code_share=Decimal("0.250000"),
        latest_blocked_reason_share=Decimal("0.000000"),
        max_blocked_reason_share=Decimal("0.500000"),
        max_no_reason_code_share=Decimal("0.500000"),
        top_reason_code_limit=5,
        blocked_reason_codes=(
            "blocked_forecast_quality",
            "blocked_risk_drawdown",
        ),
        status="watch",
        source_summaries=source_summaries,
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


def test_reason_trend_db_row_serializes_canonical_payload_and_round_trips():
    codec = _codec_module()
    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperStrategyRecommendationReasonTrendDbRow
    assert len(row.report_sha256) == 64
    assert row.report_sha256 == row.report_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "strategy-recommendation-reason-trend-v0"
    assert row.status == "watch"
    assert row.source_report_count == 2
    assert row.first_generated_at == datetime(2026, 6, 20, 14, 0, tzinfo=UTC)
    assert row.latest_generated_at == datetime(2026, 6, 20, 15, 0, tzinfo=UTC)
    assert row.latest_primary_reason_code_counts_json == {
        "new_reason": 2,
        "alpha_reason": 1,
        NO_REASON_CODE: 1,
    }
    assert row.total_primary_reason_code_counts_json == {
        "alpha_reason": 3,
        "new_reason": 2,
        "blocked_forecast_quality": 1,
        NO_REASON_CODE: 1,
    }
    assert row.top_new_reason_codes_json == {"new_reason": 2, NO_REASON_CODE: 1}
    assert row.persistent_reason_codes_json == ["alpha_reason"]
    assert row.latest_reason_code_count == 4
    assert row.latest_no_reason_code_count == 1
    assert row.latest_blocked_reason_count == 0
    assert row.latest_no_reason_code_share == Decimal("0.250000")
    assert row.latest_blocked_reason_share == Decimal("0.000000")
    assert row.max_blocked_reason_share == Decimal("0.500000")
    assert row.max_no_reason_code_share == Decimal("0.500000")
    assert row.top_reason_code_limit == 5
    assert row.blocked_reason_codes_json == [
        "blocked_forecast_quality",
        "blocked_risk_drawdown",
    ]
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json["generated_at"] == "2026-06-20T15:30:00+00:00"
    assert row.payload_json["latest_no_reason_code_share"] == "0.250000"
    assert row.payload_json["latest_blocked_reason_share"] == "0.000000"
    assert row.payload_json["source_summaries"][0]["generated_at"] == (
        "2026-06-20T14:00:00+00:00"
    )
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
    assert codec.strategy_recommendation_reason_trend_to_db_row(report) == row
    assert codec.strategy_recommendation_reason_trend_from_db_row(row) == report


def test_reason_trend_db_row_hash_is_deterministic_for_equivalent_reports():
    codec = _codec_module()
    report = _report()
    same_report = PaperStrategyRecommendationReasonTrendReport(**report.__dict__)
    different_report = PaperStrategyRecommendationReasonTrendReport(
        **{**report.__dict__, "config_version": "reason-trend-v1"},
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_reason_trend_db_row_is_frozen():
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_reason_trend_db_row_rejects_wrong_report_types_and_subclasses():
    codec = _codec_module()

    with pytest.raises(ValueError, match="PaperStrategyRecommendationReasonTrendReport"):
        codec.to_db_row(object())

    report = _report()
    with pytest.raises(ValueError, match="PaperStrategyRecommendationReasonTrendReport"):
        codec.to_db_row(ReasonTrendReportSubclass(**report.__dict__))


def test_reason_trend_db_row_rejects_wrong_row_types_and_subclasses():
    codec = _codec_module()
    row = codec.to_db_row(_report())

    class ReasonTrendDbRowSubclass(codec.PaperStrategyRecommendationReasonTrendDbRow):
        pass

    with pytest.raises(ValueError, match="PaperStrategyRecommendationReasonTrendDbRow"):
        codec.from_db_row(object())
    with pytest.raises(ValueError, match="PaperStrategyRecommendationReasonTrendDbRow"):
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


def test_reason_trend_db_row_rejects_corrupted_stored_payload_flags():
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = codec.PaperStrategyRecommendationReasonTrendDbRow(
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


def test_reason_trend_db_row_rejects_floats_in_json_payloads():
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="payload_json"):
        codec.PaperStrategyRecommendationReasonTrendDbRow(
            **{**_row_values(row), "payload_json": {**row.payload_json, "bad_float": 0.1}},
        )


def test_reason_trend_db_row_rejects_malformed_stored_payload():
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = codec.PaperStrategyRecommendationReasonTrendDbRow(
        **{
            **_row_values(row),
            "payload_json": {
                key: value
                for key, value in row.payload_json.items()
                if key != "source_summaries"
            },
        },
    )

    with pytest.raises(ValueError, match="payload_json"):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 20, 15, 31, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "reason-trend-v1"}, "config_version"),
        ({"status": "stable"}, "status"),
        ({"source_report_count": 3}, "source_report_count"),
        (
            {"first_generated_at": datetime(2026, 6, 20, 13, 0, tzinfo=UTC)},
            "first_generated_at",
        ),
        (
            {"latest_generated_at": datetime(2026, 6, 20, 16, 0, tzinfo=UTC)},
            "latest_generated_at",
        ),
        (
            {"latest_primary_reason_code_counts_json": {"other": 1}},
            "latest_primary_reason_code_counts_json",
        ),
        (
            {"total_primary_reason_code_counts_json": {"other": 1}},
            "total_primary_reason_code_counts_json",
        ),
        ({"top_new_reason_codes_json": {"other": 1}}, "top_new_reason_codes_json"),
        ({"persistent_reason_codes_json": ["other"]}, "persistent_reason_codes_json"),
        ({"latest_reason_code_count": 5}, "latest_reason_code_count"),
        ({"latest_no_reason_code_count": 2}, "latest_no_reason_code_count"),
        ({"latest_blocked_reason_count": 1}, "latest_blocked_reason_count"),
        (
            {"latest_no_reason_code_share": Decimal("0.500000")},
            "latest_no_reason_code_share",
        ),
        (
            {"latest_blocked_reason_share": Decimal("0.100000")},
            "latest_blocked_reason_share",
        ),
        ({"max_blocked_reason_share": Decimal("0.600000")}, "max_blocked_reason_share"),
        ({"max_no_reason_code_share": Decimal("0.600000")}, "max_no_reason_code_share"),
        ({"top_reason_code_limit": 6}, "top_reason_code_limit"),
        ({"blocked_reason_codes_json": ["blocked_forecast_quality"]}, "blocked_reason_codes"),
    ),
)
def test_reason_trend_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = codec.PaperStrategyRecommendationReasonTrendDbRow(
        **{**_row_values(row), **overrides},
    )

    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"source_report_count": True}, "source_report_count"),
        ({"latest_no_reason_code_share": Decimal("0.2500001")}, "latest_no_reason"),
        ({"latest_primary_reason_code_counts_json": {"bad reason": 1}}, "canonical"),
        ({"top_new_reason_codes_json": {"new_reason": 0}}, "positive int"),
        ({"persistent_reason_codes_json": ["Alpha"]}, "canonical"),
        ({"top_reason_code_limit": 0}, "top_reason_code_limit"),
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
        codec.PaperStrategyRecommendationReasonTrendDbRow(
            **{**_row_values(row), **overrides},
        )


def test_reason_trend_db_row_module_is_pure_codec():
    _codec_module()
    source = Path(
        "src/polymarket_alpha_lab/strategy_recommendation_reason_trend_db_row.py",
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
