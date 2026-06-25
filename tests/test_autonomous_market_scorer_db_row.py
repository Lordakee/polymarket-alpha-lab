from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.autonomous_market_scorer import (
    AutonomousMarketScorerReport,
    AutonomousMarketScoreRow,
)


GENERATED_AT = datetime(2026, 6, 25, 14, 30, tzinfo=UTC)
SHA256_HEX = "a" * 64


def d(value: str) -> Decimal:
    return Decimal(value)


def _score_row() -> AutonomousMarketScoreRow:
    return AutonomousMarketScoreRow(
        condition_id="condition-alpha",
        market_slug="alpha-market",
        question="Will alpha happen?",
        scoring_side="yes",
        confidence_score=d("0.800000"),
        liquidity_score=d("0.700000"),
        spread_score=d("0.600000"),
        edge_score=d("0.500000"),
        cost_score=d("0.900000"),
        risk_score=d("0.300000"),
        total_score=d("0.650000"),
        score_status="scored",
        recommended_notional=d("10.000000"),
        estimated_edge=d("0.050000"),
        reason_codes=("alpha_scored",),
    )


def _report(
    *,
    generated_at: datetime = GENERATED_AT,
    config_version: str = "autonomous-market-scorer-v0",
) -> AutonomousMarketScorerReport:
    return AutonomousMarketScorerReport(
        generated_at=generated_at,
        config_version=config_version,
        gate_status="pass",
        markets_scored=1,
        markets_skipped=0,
        markets_blocked=0,
        top_total_score=d("0.650000"),
        average_total_score=d("0.650000"),
        total_recommended_notional=d("10.000000"),
        score_rows=(_score_row(),),
        reason_codes=("autonomous_market_scorer_pass",),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _row_values(row: object) -> dict[str, object]:
    return dict(row.__dict__)


def _canonical_payload_sha256(payload_json: dict[str, object]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("scorer DB JSON contains floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_scorer_db_row_serializes_canonical_payload_and_round_trips() -> None:
    import polymarket_alpha_lab.autonomous_market_scorer_db_row as codec

    row = codec.to_db_row(_report())

    assert type(row) is codec.AutonomousMarketScorerDbRow
    assert len(row.report_sha256) == 64
    assert row.report_sha256 == row.report_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "autonomous-market-scorer-v0"
    assert row.gate_status == "pass"
    assert row.markets_scored == 1
    assert row.markets_skipped == 0
    assert row.markets_blocked == 0
    assert row.top_total_score == d("0.650000")
    assert row.average_total_score == d("0.650000")
    assert row.total_recommended_notional == d("10.000000")
    assert row.reason_codes_json == ["autonomous_market_scorer_pass"]
    assert row.score_rows_json == row.payload_json["score_rows"]
    assert row.score_rows_json[0]["recommended_notional"] == "10.000000"
    assert row.score_rows_json[0]["reason_codes"] == ["alpha_scored"]
    assert row.payload_json["generated_at"] == "2026-06-25T14:30:00+00:00"
    assert row.payload_json["top_total_score"] == "0.650000"
    assert row.payload_json["average_total_score"] == "0.650000"
    assert row.payload_json["total_recommended_notional"] == "10.000000"
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    _assert_no_floats(row.reason_codes_json)
    _assert_no_floats(row.score_rows_json)
    _assert_no_floats(row.payload_json)
    assert row.report_sha256 == _canonical_payload_sha256(row.payload_json)
    assert codec.from_db_row(row) == _report()
    assert codec.autonomous_market_scorer_report_to_db_row(_report()) == row
    assert codec.autonomous_market_scorer_report_from_db_row(row) == _report()


def test_scorer_db_row_normalizes_generated_at_to_utc_before_hashing() -> None:
    import polymarket_alpha_lab.autonomous_market_scorer_db_row as codec

    same_in_pacific = GENERATED_AT.astimezone(timezone(timedelta(hours=-7)))

    utc_row = codec.to_db_row(_report(generated_at=GENERATED_AT))
    pacific_row = codec.to_db_row(_report(generated_at=same_in_pacific))

    assert pacific_row.generated_at == GENERATED_AT
    assert pacific_row.payload_json == utc_row.payload_json
    assert pacific_row.report_sha256 == utc_row.report_sha256


def test_scorer_db_row_hash_is_deterministic_for_equivalent_reports() -> None:
    import polymarket_alpha_lab.autonomous_market_scorer_db_row as codec

    report = _report()
    same_report = AutonomousMarketScorerReport(**report.__dict__)
    different_report = _report(config_version="autonomous-market-scorer-v1")

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_scorer_db_row_is_frozen() -> None:
    import polymarket_alpha_lab.autonomous_market_scorer_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_scorer_db_row_rejects_wrong_report_type() -> None:
    import polymarket_alpha_lab.autonomous_market_scorer_db_row as codec

    with pytest.raises(ValueError, match="AutonomousMarketScorerReport"):
        codec.to_db_row(object())


def test_scorer_db_row_rejects_wrong_row_types_and_subclasses() -> None:
    import polymarket_alpha_lab.autonomous_market_scorer_db_row as codec

    row = codec.to_db_row(_report())

    class ScorerDbRowSubclass(codec.AutonomousMarketScorerDbRow):
        pass

    with pytest.raises(ValueError, match="AutonomousMarketScorerDbRow"):
        codec.from_db_row(object())
    with pytest.raises(ValueError, match="AutonomousMarketScorerDbRow"):
        codec.from_db_row(ScorerDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_scorer_db_row_rejects_false_report_flags_before_write(
    flag_name: str,
) -> None:
    import polymarket_alpha_lab.autonomous_market_scorer_db_row as codec

    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_scorer_db_row_rejects_corrupted_payload_flags() -> None:
    import polymarket_alpha_lab.autonomous_market_scorer_db_row as codec

    row = codec.to_db_row(_report())
    payload = {**row.payload_json, "readonly": False}
    malformed = codec.AutonomousMarketScorerDbRow(
        **{
            **_row_values(row),
            "report_sha256": _canonical_payload_sha256(payload),
            "payload_json": payload,
        },
    )

    with pytest.raises(ValueError, match="readonly"):
        codec.from_db_row(malformed)


def test_scorer_db_row_rejects_hash_mismatch() -> None:
    import polymarket_alpha_lab.autonomous_market_scorer_db_row as codec

    row = codec.to_db_row(_report())
    malformed = codec.AutonomousMarketScorerDbRow(
        **{
            **_row_values(row),
            "payload_json": {**row.payload_json, "config_version": "changed"},
        },
    )

    with pytest.raises(ValueError, match="report_sha256"):
        codec.from_db_row(malformed)


def test_scorer_db_row_rejects_recursive_floats_in_json_payloads() -> None:
    import polymarket_alpha_lab.autonomous_market_scorer_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="score_rows_json"):
        replace(
            row,
            score_rows_json=[
                {**row.score_rows_json[0], "recommended_notional": 1.0},
            ],
        )
    with pytest.raises(ValueError, match="payload_json"):
        replace(row, payload_json={**row.payload_json, "bad_float": 0.1})


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 25, 14, 31, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "autonomous-market-scorer-v1"}, "config_version"),
        ({"gate_status": "watch"}, "gate_status"),
        ({"markets_scored": 2}, "markets_scored"),
        ({"markets_skipped": 1}, "markets_skipped"),
        ({"markets_blocked": 1}, "markets_blocked"),
        ({"top_total_score": d("0.660000")}, "top_total_score"),
        ({"average_total_score": d("0.660000")}, "average_total_score"),
        ({"total_recommended_notional": d("11.000000")}, "total_recommended"),
        ({"reason_codes_json": ["other_reason"]}, "reason_codes_json"),
        ({"score_rows_json": []}, "score_rows_json"),
    ),
)
def test_scorer_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    import polymarket_alpha_lab.autonomous_market_scorer_db_row as codec

    row = codec.to_db_row(_report())
    malformed = codec.AutonomousMarketScorerDbRow(**{**_row_values(row), **overrides})

    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"gate_status": "paused"}, "gate_status"),
        ({"markets_scored": True}, "markets_scored"),
        ({"markets_skipped": -1}, "markets_skipped"),
        ({"top_total_score": d("-0.000001")}, "top_total_score"),
        ({"average_total_score": d("0.6500001")}, "average_total_score"),
        ({"total_recommended_notional": d("-1.000000")}, "total_recommended"),
        ({"reason_codes_json": "reason"}, "reason_codes_json"),
        ({"score_rows_json": {"condition_id": "condition-alpha"}}, "score_rows_json"),
        ({"payload_json": []}, "payload_json"),
        ({"paper_only": False}, "paper_only"),
    ),
)
def test_scorer_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
) -> None:
    import polymarket_alpha_lab.autonomous_market_scorer_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.AutonomousMarketScorerDbRow(**{**_row_values(row), **overrides})


def test_scorer_db_row_module_is_pure_codec() -> None:
    import polymarket_alpha_lab.autonomous_market_scorer_db_row as codec

    assert codec.__name__.endswith("_db_row")
    source = Path(
        "src/polymarket_alpha_lab/autonomous_market_scorer_db_row.py",
    ).read_text(encoding="utf-8")

    for banned in (
        "psycopg",
        "supabase",
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
        "execute",
    ):
        assert banned not in source.lower()
