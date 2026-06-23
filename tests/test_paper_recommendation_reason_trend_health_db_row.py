from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.paper_recommendation_reason_trend_health import (
    PaperRecommendationReasonTrendHealthReport,
)


GENERATED_AT = datetime(2026, 6, 22, 18, 30, tzinfo=UTC)


class ReasonTrendHealthReportSubclass(PaperRecommendationReasonTrendHealthReport):
    pass


def _codec_module():
    from polymarket_alpha_lab import paper_recommendation_reason_trend_health_db_row

    return paper_recommendation_reason_trend_health_db_row


def _report() -> PaperRecommendationReasonTrendHealthReport:
    return PaperRecommendationReasonTrendHealthReport(
        generated_at=GENERATED_AT,
        config_version="paper-recommendation-reason-trend-health-v0",
        health_status="watch",
        source_report_count=3,
        reason_code_count=2,
        blocked_status_count=1,
        blocked_status_share=Decimal("0.250000"),
        reject_status_count=0,
        reject_status_share=Decimal("0.000000"),
        new_reason_code_count=2,
        transition_count=1,
        persistent_reason_codes=("alpha",),
        reason_codes=("alpha", "beta"),
        max_blocked_status_share=Decimal("0.500000"),
        max_reject_status_share=Decimal("0.500000"),
        max_new_reason_code_count=1,
        max_transition_count=1,
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


def test_reason_trend_health_db_row_serializes_payload_and_round_trips() -> None:
    codec = _codec_module()
    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperRecommendationReasonTrendHealthDbRow
    assert len(row.report_sha256) == 64
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "paper-recommendation-reason-trend-health-v0"
    assert row.health_status == "watch"
    assert row.source_report_count == 3
    assert row.reason_code_count == 2
    assert row.blocked_status_count == 1
    assert row.blocked_status_share == Decimal("0.250000")
    assert row.reject_status_count == 0
    assert row.reject_status_share == Decimal("0.000000")
    assert row.new_reason_code_count == 2
    assert row.transition_count == 1
    assert row.persistent_reason_codes_json == ["alpha"]
    assert row.reason_codes_json == ["alpha", "beta"]
    assert row.max_blocked_status_share == Decimal("0.500000")
    assert row.max_reject_status_share == Decimal("0.500000")
    assert row.max_new_reason_code_count == 1
    assert row.max_transition_count == 1
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json["blocked_status_share"] == "0.250000"
    assert row.payload_json["reject_status_share"] == "0.000000"
    assert row.payload_json["persistent_reason_codes"] == ["alpha"]
    assert row.payload_json["reason_codes"] == ["alpha", "beta"]
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    _assert_no_floats(row.payload_json)
    _assert_no_floats(row.persistent_reason_codes_json)
    _assert_no_floats(row.reason_codes_json)

    encoded = json.dumps(
        row.payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    assert row.report_sha256 == hashlib.sha256(encoded).hexdigest()
    assert codec.from_db_row(row) == report
    assert codec.paper_recommendation_reason_trend_health_report_to_db_row(report) == row
    assert codec.paper_recommendation_reason_trend_health_report_from_db_row(row) == report


def test_reason_trend_health_db_row_hash_is_deterministic() -> None:
    codec = _codec_module()
    report = _report()
    same_report = PaperRecommendationReasonTrendHealthReport(**report.__dict__)
    different_report = PaperRecommendationReasonTrendHealthReport(
        **{**report.__dict__, "config_version": "paper-recommendation-reason-trend-health-v1"},
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_reason_trend_health_db_row_is_frozen() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_reason_trend_health_db_row_rejects_wrong_report_types_and_subclasses() -> None:
    codec = _codec_module()

    with pytest.raises(ValueError, match="PaperRecommendationReasonTrendHealthReport"):
        codec.to_db_row(object())

    report = _report()
    with pytest.raises(ValueError, match="PaperRecommendationReasonTrendHealthReport"):
        codec.to_db_row(ReasonTrendHealthReportSubclass(**report.__dict__))


def test_reason_trend_health_db_row_rejects_wrong_row_types_and_subclasses() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    class ReasonTrendHealthDbRowSubclass(codec.PaperRecommendationReasonTrendHealthDbRow):
        pass

    with pytest.raises(ValueError, match="PaperRecommendationReasonTrendHealthDbRow"):
        codec.from_db_row(object())
    with pytest.raises(ValueError, match="PaperRecommendationReasonTrendHealthDbRow"):
        codec.from_db_row(ReasonTrendHealthDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_reason_trend_health_db_row_rejects_false_report_flags_before_write(
    flag_name: str,
) -> None:
    codec = _codec_module()
    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_reason_trend_health_db_row_rejects_corrupted_payload_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = codec.PaperRecommendationReasonTrendHealthDbRow(
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


def test_reason_trend_health_db_row_rejects_floats_in_json_payloads() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="payload_json"):
        codec.PaperRecommendationReasonTrendHealthDbRow(
            **{**_row_values(row), "payload_json": {**row.payload_json, "bad_float": 0.1}},
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 22, 18, 31, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "paper-recommendation-reason-trend-health-v1"}, "config_version"),
        ({"health_status": "blocked"}, "health_status"),
        ({"source_report_count": 4}, "source_report_count"),
        ({"reason_code_count": 3}, "reason_code_count"),
        ({"blocked_status_count": 2}, "blocked_status_count"),
        ({"blocked_status_share": Decimal("0.500000")}, "blocked_status_share"),
        ({"reject_status_count": 1}, "reject_status_count"),
        ({"reject_status_share": Decimal("0.250000")}, "reject_status_share"),
        ({"new_reason_code_count": 3}, "new_reason_code_count"),
        ({"transition_count": 2}, "transition_count"),
        ({"persistent_reason_codes_json": []}, "persistent_reason_codes"),
        ({"reason_codes_json": ["alpha"]}, "reason_codes"),
        ({"max_new_reason_code_count": 2}, "max_new_reason_code_count"),
        ({"max_transition_count": 2}, "max_transition_count"),
    ),
)
def test_reason_trend_health_db_row_rejects_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = codec.PaperRecommendationReasonTrendHealthDbRow(
        **{**_row_values(row), **overrides},
    )

    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"health_status": "stable"}, "health_status"),
        ({"blocked_status_share": Decimal("1.000001")}, "blocked_status_share"),
        ({"reject_status_share": 0.0}, "reject_status_share"),
        ({"source_report_count": True}, "source_report_count"),
        ({"persistent_reason_codes_json": "alpha"}, "persistent_reason_codes_json"),
        ({"reason_codes_json": [1]}, "reason_codes_json"),
        ({"paper_only": False}, "paper_only"),
    ),
)
def test_reason_trend_health_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperRecommendationReasonTrendHealthDbRow(
            **{**_row_values(row), **overrides},
        )


def test_reason_trend_health_db_row_module_is_pure_codec() -> None:
    _codec_module()
    source = Path(
        "src/polymarket_alpha_lab/paper_recommendation_reason_trend_health_db_row.py",
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
