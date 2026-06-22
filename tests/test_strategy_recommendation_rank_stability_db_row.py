from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

import pytest

from polymarket_alpha_lab.strategy_recommendation_rank_stability import (
    PaperStrategyRecommendationRankStabilityReport,
    PaperStrategyRecommendationRankStabilityRow,
)


GENERATED_AT = datetime(2026, 6, 22, 8, 0, tzinfo=UTC)
LATEST_GENERATED_AT = datetime(2026, 6, 22, 7, 55, tzinfo=UTC)
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


class RankStabilityReportSubclass(PaperStrategyRecommendationRankStabilityReport):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _stable_row() -> PaperStrategyRecommendationRankStabilityRow:
    return PaperStrategyRecommendationRankStabilityRow(
        market_slug="alpha",
        stability_status="stable",
        latest_selected_side="yes",
        latest_queue_status="ready",
        present_snapshot_count=3,
        ready_snapshot_count=3,
        first_rank=1,
        latest_rank=1,
        rank_delta=0,
        max_rank_movement=1,
        first_score=d("0.700000"),
        latest_score=d("0.720000"),
        score_delta=d("0.020000"),
        max_score_delta=d("0.040000"),
        first_notional=d("10.000000"),
        latest_notional=d("12.500000"),
        notional_delta=d("2.500000"),
        selected_side_changed=False,
        queue_status_changed=False,
        reason_codes=("stable_ready",),
    )


def _blocked_row() -> PaperStrategyRecommendationRankStabilityRow:
    return PaperStrategyRecommendationRankStabilityRow(
        market_slug="beta",
        stability_status="blocked",
        latest_selected_side="no",
        latest_queue_status="ready",
        present_snapshot_count=3,
        ready_snapshot_count=3,
        first_rank=1,
        latest_rank=3,
        rank_delta=2,
        max_rank_movement=2,
        first_score=d("0.900000"),
        latest_score=d("0.750000"),
        score_delta=d("-0.150000"),
        max_score_delta=d("0.150000"),
        first_notional=d("20.000000"),
        latest_notional=d("15.000000"),
        notional_delta=d("-5.000000"),
        selected_side_changed=True,
        queue_status_changed=False,
        reason_codes=("selected_side_changed",),
    )


def _report() -> PaperStrategyRecommendationRankStabilityReport:
    rows = (_stable_row(), _blocked_row())
    return PaperStrategyRecommendationRankStabilityReport(
        generated_at=GENERATED_AT,
        config_version="strategy-recommendation-rank-stability-v0",
        source_report_count=3,
        candidate_count=2,
        stability_status="blocked",
        stable_count=1,
        watch_count=0,
        blocked_count=1,
        stable_ready_count=1,
        unstable_ready_count=1,
        selected_side_changed_count=1,
        queue_status_changed_count=0,
        latest_generated_at=LATEST_GENERATED_AT,
        top_stable_market_slug="alpha",
        reason_codes=("blocked_stability_candidates_present",),
        rows=rows,
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
        pytest.fail("rank stability DB JSON must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_rank_stability_db_row_serializes_canonical_payload_and_round_trips() -> None:
    from polymarket_alpha_lab import strategy_recommendation_rank_stability_db_row as codec

    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperStrategyRecommendationRankStabilityDbRow
    assert SHA256_RE.fullmatch(row.report_sha256)
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "strategy-recommendation-rank-stability-v0"
    assert row.stability_status == "blocked"
    assert row.reason_codes_json == ["blocked_stability_candidates_present"]
    assert row.source_report_count == 3
    assert row.candidate_count == 2
    assert row.stable_count == 1
    assert row.watch_count == 0
    assert row.blocked_count == 1
    assert row.stable_ready_count == 1
    assert row.unstable_ready_count == 1
    assert row.selected_side_changed_count == 1
    assert row.queue_status_changed_count == 0
    assert row.latest_generated_at == LATEST_GENERATED_AT
    assert row.top_stable_market_slug == "alpha"
    assert row.rows_json == row.payload_json["rows"]
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json["generated_at"] == "2026-06-22T08:00:00+00:00"
    assert row.payload_json["latest_generated_at"] == "2026-06-22T07:55:00+00:00"
    assert row.payload_json["rows"][0]["latest_score"] == "0.720000"
    assert row.payload_json["rows"][1]["score_delta"] == "-0.150000"
    assert row.payload_json["rows"][1]["notional_delta"] == "-5.000000"
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    _assert_no_floats(row.rows_json)
    _assert_no_floats(row.payload_json)

    assert row.report_sha256 == _canonical_payload_sha256(row.payload_json)
    assert codec.from_db_row(row) == report
    assert codec.strategy_recommendation_rank_stability_report_to_db_row(report) == row
    assert codec.strategy_recommendation_rank_stability_report_from_db_row(row) == report


def test_rank_stability_db_row_hash_is_deterministic_for_equivalent_reports() -> None:
    from polymarket_alpha_lab import strategy_recommendation_rank_stability_db_row as codec

    report = _report()
    same_report = PaperStrategyRecommendationRankStabilityReport(**report.__dict__)
    different_report = PaperStrategyRecommendationRankStabilityReport(
        **{**report.__dict__, "config_version": "strategy-recommendation-rank-stability-v1"},
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_rank_stability_db_row_is_frozen() -> None:
    from polymarket_alpha_lab import strategy_recommendation_rank_stability_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_rank_stability_db_row_rejects_wrong_report_types_and_subclasses() -> None:
    from polymarket_alpha_lab import strategy_recommendation_rank_stability_db_row as codec

    with pytest.raises(ValueError, match="PaperStrategyRecommendationRankStabilityReport"):
        codec.to_db_row(object())

    report = _report()
    subclass = RankStabilityReportSubclass(**report.__dict__)
    with pytest.raises(ValueError, match="PaperStrategyRecommendationRankStabilityReport"):
        codec.to_db_row(subclass)


def test_rank_stability_db_row_rejects_wrong_row_types_and_subclasses() -> None:
    from polymarket_alpha_lab import strategy_recommendation_rank_stability_db_row as codec

    row = codec.to_db_row(_report())

    class RankStabilityDbRowSubclass(codec.PaperStrategyRecommendationRankStabilityDbRow):
        pass

    with pytest.raises(ValueError, match="PaperStrategyRecommendationRankStabilityDbRow"):
        codec.from_db_row(object())
    with pytest.raises(ValueError, match="PaperStrategyRecommendationRankStabilityDbRow"):
        codec.from_db_row(RankStabilityDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_rank_stability_db_row_rejects_false_report_flags_before_write(
    flag_name: str,
) -> None:
    from polymarket_alpha_lab import strategy_recommendation_rank_stability_db_row as codec

    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_rank_stability_db_row_rejects_corrupted_stored_payload_flags() -> None:
    from polymarket_alpha_lab import strategy_recommendation_rank_stability_db_row as codec

    row = codec.to_db_row(_report())
    payload = {
        **row.payload_json,
        "rows": [
            {**row.payload_json["rows"][0], "readonly": False},
            row.payload_json["rows"][1],
        ],
    }
    malformed = codec.PaperStrategyRecommendationRankStabilityDbRow(
        **{
            **_row_values(row),
            "report_sha256": _canonical_payload_sha256(payload),
            "payload_json": payload,
            "rows_json": payload["rows"],
        },
    )

    with pytest.raises(ValueError, match="readonly"):
        codec.from_db_row(malformed)


def test_rank_stability_db_row_rejects_recursive_floats_in_json_payloads() -> None:
    from polymarket_alpha_lab import strategy_recommendation_rank_stability_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="rows_json"):
        replace(
            row,
            rows_json=[
                {**row.rows_json[0], "latest_score": 0.72},
                row.rows_json[1],
            ],
        )
    with pytest.raises(ValueError, match="payload_json"):
        replace(row, payload_json={**row.payload_json, "bad_float": 0.1})


def test_rank_stability_db_row_rejects_malformed_stored_payload() -> None:
    from polymarket_alpha_lab import strategy_recommendation_rank_stability_db_row as codec

    row = codec.to_db_row(_report())
    payload = {key: value for key, value in row.payload_json.items() if key != "rows"}
    malformed = codec.PaperStrategyRecommendationRankStabilityDbRow(
        **{
            **_row_values(row),
            "report_sha256": _canonical_payload_sha256(payload),
            "payload_json": payload,
        },
    )

    with pytest.raises(ValueError, match="payload_json"):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 22, 8, 1, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "strategy-recommendation-rank-stability-v1"}, "config_version"),
        ({"stability_status": "watch"}, "stability_status"),
        ({"reason_codes_json": ["unstable_ready_candidates_present"]}, "reason_codes_json"),
        ({"source_report_count": 4}, "source_report_count"),
        ({"candidate_count": 3}, "candidate_count"),
        ({"stable_count": 2}, "stable_count"),
        ({"watch_count": 1}, "watch_count"),
        ({"blocked_count": 0}, "blocked_count"),
        ({"stable_ready_count": 0}, "stable_ready_count"),
        ({"unstable_ready_count": 0}, "unstable_ready_count"),
        ({"selected_side_changed_count": 0}, "selected_side_changed_count"),
        ({"queue_status_changed_count": 1}, "queue_status_changed_count"),
        ({"latest_generated_at": datetime(2026, 6, 22, 7, 54, tzinfo=UTC)}, "latest_generated_at"),
        ({"top_stable_market_slug": "gamma"}, "top_stable_market_slug"),
    ),
)
def test_rank_stability_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    from polymarket_alpha_lab import strategy_recommendation_rank_stability_db_row as codec

    row = codec.to_db_row(_report())
    malformed = codec.PaperStrategyRecommendationRankStabilityDbRow(
        **{**_row_values(row), **overrides},
    )

    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)


def test_rank_stability_db_row_runs_scalar_payload_validation_on_decode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from polymarket_alpha_lab import strategy_recommendation_rank_stability_db_row as codec

    row = codec.to_db_row(_report())
    calls: list[codec.PaperStrategyRecommendationRankStabilityDbRow] = []

    def record_validation(
        row_arg: codec.PaperStrategyRecommendationRankStabilityDbRow,
    ) -> None:
        calls.append(row_arg)

    monkeypatch.setattr(codec, "_validate_row_scalars_match_payload", record_validation)

    assert codec.from_db_row(row) == _report()
    assert calls == [row]


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"stability_status": "pass"}, "stability_status"),
        ({"source_report_count": True}, "source_report_count"),
        ({"rows_json": {"market_slug": "alpha"}}, "rows_json"),
        ({"paper_only": False}, "paper_only"),
    ),
)
def test_rank_stability_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
) -> None:
    from polymarket_alpha_lab import strategy_recommendation_rank_stability_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperStrategyRecommendationRankStabilityDbRow(
            **{**_row_values(row), **overrides},
        )


def test_rank_stability_db_row_module_is_pure_codec() -> None:
    from polymarket_alpha_lab import strategy_recommendation_rank_stability_db_row

    assert strategy_recommendation_rank_stability_db_row.__name__.endswith("_db_row")
    source = Path(
        "src/polymarket_alpha_lab/strategy_recommendation_rank_stability_db_row.py",
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
