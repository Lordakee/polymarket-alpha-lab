from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_probability_recommendation_queue import (
    PaperProbabilityRecommendationQueueConfig,
    PaperProbabilityRecommendationQueueReport,
    build_paper_probability_recommendation_queue_report,
)
from polymarket_alpha_lab.paper_probability_side_edge import (
    PaperProbabilitySideEdgeRow,
)


GENERATED_AT = datetime(2026, 6, 20, 15, 30, tzinfo=UTC)
SOURCE_CONFIG_VERSION = "probability-recommendation-queue-v0"
ZERO = Decimal("0.000000")


class QueueReportSubclass(PaperProbabilityRecommendationQueueReport):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _codec():
    try:
        return importlib.import_module(
            "polymarket_alpha_lab.paper_probability_recommendation_queue_db_row",
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"codec module missing: {exc}")


def _side_edge_row(
    market_slug: str,
    *,
    question: str | None = None,
    side: str = "yes",
    side_probability: Decimal = d("0.700000"),
    market_implied_probability: Decimal = d("0.600000"),
    total_cost_per_share: Decimal = d("0.010000"),
    recommendation_score: Decimal | None = None,
    action: str = "recommend",
    depth_status: str | None = None,
    requested_paper_shares: Decimal = d("100.000000"),
    max_executable_shares: Decimal = d("100.000000"),
    reason_codes: tuple[str, ...] = ("source_reason",),
) -> PaperProbabilitySideEdgeRow:
    gross_probability_edge = side_probability - market_implied_probability
    net_probability_edge = gross_probability_edge - total_cost_per_share
    executable_paper_shares = min(requested_paper_shares, max_executable_shares)
    if requested_paper_shares <= ZERO or max_executable_shares <= ZERO:
        executable_paper_shares = ZERO
        inferred_depth_status = "no_depth"
    elif max_executable_shares < requested_paper_shares:
        inferred_depth_status = "partial_depth"
    else:
        inferred_depth_status = "sufficient_depth"
    if recommendation_score is None:
        recommendation_score = net_probability_edge if action != "reject" else ZERO
    return PaperProbabilitySideEdgeRow(
        market_slug=market_slug,
        question=question or f"Will {market_slug} resolve yes?",
        side=side,
        side_probability=side_probability,
        market_implied_probability=market_implied_probability,
        gross_probability_edge=gross_probability_edge,
        total_cost_per_share=total_cost_per_share,
        net_probability_edge=net_probability_edge,
        recommendation_score=recommendation_score,
        action=action,
        depth_status=depth_status or inferred_depth_status,
        requested_paper_shares=requested_paper_shares,
        max_executable_shares=max_executable_shares,
        executable_paper_shares=executable_paper_shares,
        reason_codes=reason_codes,
    )


def _config(*, max_queue_rows: int = 5) -> PaperProbabilityRecommendationQueueConfig:
    return PaperProbabilityRecommendationQueueConfig(
        config_version=SOURCE_CONFIG_VERSION,
        max_queue_rows=max_queue_rows,
        min_recommendation_score=d("0.050000"),
        include_watch=True,
    )


def _report() -> PaperProbabilityRecommendationQueueReport:
    return build_paper_probability_recommendation_queue_report(
        (
            _side_edge_row(
                "alpha-recommend",
                side_probability=d("0.740000"),
                market_implied_probability=d("0.600000"),
                total_cost_per_share=d("0.010000"),
                reason_codes=("strong_edge", "shared_depth"),
            ),
            _side_edge_row(
                "beta-watch",
                side_probability=d("0.640000"),
                market_implied_probability=d("0.600000"),
                total_cost_per_share=d("0.010000"),
                recommendation_score=d("0.030000"),
                action="watch",
                reason_codes=("below_min_net_probability_edge", "shared_depth"),
            ),
            _side_edge_row(
                "delta-reject",
                side_probability=d("0.520000"),
                market_implied_probability=d("0.600000"),
                total_cost_per_share=d("0.010000"),
                action="reject",
                reason_codes=("nonpositive_net_probability_edge",),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("DB payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def _row_values(row) -> dict[str, object]:
    return {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at,
        "source_config_version": row.source_config_version,
        "input_count": row.input_count,
        "queue_count": row.queue_count,
        "research_review_count": row.research_review_count,
        "await_fresh_context_count": row.await_fresh_context_count,
        "skip_count": row.skip_count,
        "excluded_count": row.excluded_count,
        "reason_code_counts_json": row.reason_code_counts_json,
        "payload_json": row.payload_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _bypassed_row(codec, row, **overrides):
    malformed = object.__new__(codec.PaperProbabilityRecommendationQueueDbRow)
    for key, value in {**_row_values(row), **overrides}.items():
        object.__setattr__(malformed, key, value)
    return malformed


def test_probability_queue_db_row_serializes_canonical_payload_and_round_trips():
    codec = _codec()
    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperProbabilityRecommendationQueueDbRow
    assert len(row.report_sha256) == 64
    assert row.report_sha256 == row.report_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.source_config_version == SOURCE_CONFIG_VERSION
    assert row.input_count == 3
    assert row.queue_count == 3
    assert row.research_review_count == 1
    assert row.await_fresh_context_count == 1
    assert row.skip_count == 1
    assert row.excluded_count == 0
    assert row.reason_code_counts_json == {
        "below_min_net_probability_edge": 1,
        "nonpositive_net_probability_edge": 1,
        "shared_depth": 2,
        "strong_edge": 1,
    }
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json["generated_at"] == "2026-06-20T15:30:00+00:00"
    assert row.payload_json["queue_rows"][0]["recommendation_score"] == "0.130000"
    assert row.payload_json["queue_rows"][1]["recommended_next_step"] == (
        "await_fresh_context"
    )
    assert row.payload_json["queue_rows"][2]["recommended_next_step"] == "skip"
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    assert row.payload_json["queue_rows"][0]["readonly"] is True
    _assert_no_floats(row.payload_json)

    encoded = json.dumps(
        row.payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    assert row.report_sha256 == hashlib.sha256(encoded).hexdigest()
    assert codec.from_db_row(row) == report


def test_probability_queue_db_row_hash_uses_canonical_full_payload():
    codec = _codec()
    report = _report()
    same_report = PaperProbabilityRecommendationQueueReport(**report.__dict__)
    different_report = build_paper_probability_recommendation_queue_report(
        (
            _side_edge_row(
                "omega-recommend",
                side_probability=d("0.710000"),
                market_implied_probability=d("0.600000"),
                total_cost_per_share=d("0.010000"),
                reason_codes=("different_edge",),
            ),
        ),
        config=_config(max_queue_rows=1),
        generated_at=GENERATED_AT,
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_probability_queue_db_row_is_frozen():
    codec = _codec()
    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.paper_only = False  # type: ignore[misc]


def test_probability_queue_db_row_rejects_wrong_report_type_and_subclasses():
    codec = _codec()

    with pytest.raises(ValueError, match="PaperProbabilityRecommendationQueueReport"):
        codec.to_db_row(object())

    report = _report()
    subclass = QueueReportSubclass(**report.__dict__)
    with pytest.raises(ValueError, match="PaperProbabilityRecommendationQueueReport"):
        codec.to_db_row(subclass)


def test_probability_queue_db_row_rejects_wrong_row_type_and_subclasses():
    codec = _codec()
    row = codec.to_db_row(_report())

    class QueueDbRowSubclass(codec.PaperProbabilityRecommendationQueueDbRow):
        pass

    subclass = QueueDbRowSubclass(**_row_values(row))

    with pytest.raises(ValueError, match="PaperProbabilityRecommendationQueueDbRow"):
        codec.from_db_row(object())

    with pytest.raises(ValueError, match="PaperProbabilityRecommendationQueueDbRow"):
        codec.from_db_row(subclass)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_probability_queue_db_row_rejects_false_report_flags(flag_name: str):
    codec = _codec()
    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_probability_queue_db_row_rejects_deep_false_report_flags_before_write():
    codec = _codec()
    report = _report()
    object.__setattr__(report.queue_rows[0], "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        codec.to_db_row(report)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_probability_queue_db_row_constructor_rejects_top_level_payload_hard_flags(
    flag_name: str,
) -> None:
    codec = _codec()
    row = codec.to_db_row(_report())
    payload_json = {**row.payload_json, flag_name: False}

    with pytest.raises(ValueError, match=flag_name):
        codec.PaperProbabilityRecommendationQueueDbRow(
            **{**_row_values(row), "payload_json": payload_json},
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_probability_queue_db_row_constructor_rejects_nested_payload_hard_flags(
    flag_name: str,
) -> None:
    codec = _codec()
    row = codec.to_db_row(_report())
    payload_json = {
        **row.payload_json,
        "queue_rows": (
            {**row.payload_json["queue_rows"][0], flag_name: False},
            *row.payload_json["queue_rows"][1:],
        ),
    }

    with pytest.raises(ValueError, match=flag_name):
        codec.PaperProbabilityRecommendationQueueDbRow(
            **{**_row_values(row), "payload_json": payload_json},
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 20, 15, 31, tzinfo=UTC)}, "generated_at"),
        ({"source_config_version": "different-queue-v0"}, "source_config_version"),
        ({"input_count": 4}, "input_count"),
        ({"queue_count": 2}, "queue_count"),
        ({"research_review_count": 2}, "research_review_count"),
        ({"await_fresh_context_count": 2}, "await_fresh_context_count"),
        ({"skip_count": 2}, "skip_count"),
        ({"excluded_count": 1}, "excluded_count"),
        (
            {"reason_code_counts_json": {"strong_edge": 1}},
            "reason_code_counts_json",
        ),
    ),
)
def test_probability_queue_db_row_constructor_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperProbabilityRecommendationQueueDbRow(
            **{**_row_values(row), **overrides},
        )


def test_probability_queue_from_db_row_defends_against_bypassed_malformed_rows():
    codec = _codec()
    row = codec.to_db_row(_report())
    payload_json = {
        **row.payload_json,
        "queue_rows": (
            {**row.payload_json["queue_rows"][0], "readonly": False},
            *row.payload_json["queue_rows"][1:],
        ),
    }
    malformed = _bypassed_row(codec, row, payload_json=payload_json)

    with pytest.raises(ValueError, match="readonly"):
        codec.from_db_row(malformed)


def test_probability_queue_from_db_row_defends_against_bypassed_hash_mismatch():
    codec = _codec()
    row = codec.to_db_row(_report())
    malformed = _bypassed_row(codec, row, report_sha256="b" * 64)

    with pytest.raises(ValueError, match="report_sha256"):
        codec.from_db_row(malformed)


def test_probability_queue_db_row_wraps_payload_recovery_errors_as_value_error():
    codec = _codec()
    row = codec.to_db_row(_report())
    malformed = _bypassed_row(
        codec,
        row,
        payload_json={
            key: value for key, value in row.payload_json.items() if key != "queue_rows"
        },
    )

    with pytest.raises(ValueError, match="payload_json"):
        codec.from_db_row(malformed)


def test_probability_queue_db_row_validates_row_shape_and_rejects_floats():
    codec = _codec()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="report_sha256"):
        codec.PaperProbabilityRecommendationQueueDbRow(
            **{**_row_values(row), "report_sha256": "bad"},
        )

    with pytest.raises(ValueError, match="payload_json"):
        codec.PaperProbabilityRecommendationQueueDbRow(
            **{
                **_row_values(row),
                "payload_json": {**row.payload_json, "bad_float": 0.1},
            },
        )


def test_probability_queue_db_row_module_is_pure_codec():
    _codec()
    source = Path(
        "src/polymarket_alpha_lab/paper_probability_recommendation_queue_db_row.py",
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
