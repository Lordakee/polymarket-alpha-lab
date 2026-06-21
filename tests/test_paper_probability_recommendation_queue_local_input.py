from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

import pytest

from polymarket_alpha_lab.paper_probability_recommendation_queue import (
    PaperProbabilityRecommendationQueueConfig,
    build_paper_probability_recommendation_queue_report,
)
from polymarket_alpha_lab.paper_probability_recommendation_queue_local_input import (
    read_paper_probability_recommendation_queue_side_edge_rows,
)
from polymarket_alpha_lab.paper_probability_side_edge import PaperProbabilitySideEdgeRow


GENERATED_AT = datetime(2026, 6, 19, 12, 30, tzinfo=UTC)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def q(value: Decimal) -> str:
    return str(value.quantize(QUANTUM))


def side_edge_row_payload(
    market_slug: str,
    *,
    side: str = "yes",
    side_probability: str = "0.740000",
    market_implied_probability: str = "0.600000",
    total_cost_per_share: str = "0.010000",
    action: str = "recommend",
    requested_paper_shares: str = "100.000000",
    max_executable_shares: str = "100.000000",
    reason_codes: list[str] | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    side_probability_value = d(side_probability)
    market_implied_probability_value = d(market_implied_probability)
    total_cost_per_share_value = d(total_cost_per_share)
    gross_probability_edge = side_probability_value - market_implied_probability_value
    net_probability_edge = gross_probability_edge - total_cost_per_share_value
    requested_paper_shares_value = d(requested_paper_shares)
    max_executable_shares_value = d(max_executable_shares)
    if requested_paper_shares_value <= ZERO or max_executable_shares_value <= ZERO:
        executable_paper_shares = ZERO
        depth_status = "no_depth"
    elif max_executable_shares_value < requested_paper_shares_value:
        executable_paper_shares = max_executable_shares_value
        depth_status = "partial_depth"
    else:
        executable_paper_shares = requested_paper_shares_value
        depth_status = "sufficient_depth"
    recommendation_score = ZERO if action == "reject" else net_probability_edge
    payload: dict[str, Any] = {
        "market_slug": market_slug,
        "question": f"Will {market_slug} resolve yes?",
        "side": side,
        "side_probability": q(side_probability_value),
        "market_implied_probability": q(market_implied_probability_value),
        "gross_probability_edge": q(gross_probability_edge),
        "total_cost_per_share": q(total_cost_per_share_value),
        "net_probability_edge": q(net_probability_edge),
        "recommendation_score": q(recommendation_score),
        "action": action,
        "depth_status": depth_status,
        "requested_paper_shares": q(requested_paper_shares_value),
        "max_executable_shares": q(max_executable_shares_value),
        "executable_paper_shares": q(executable_paper_shares),
        "reason_codes": reason_codes or ["source_reason"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    payload.update(overrides)
    return payload


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def test_reads_jsonl_side_edge_rows_that_feed_queue_reducer(tmp_path: Path) -> None:
    path = tmp_path / "side-edge-rows.jsonl"
    payloads = (
        side_edge_row_payload("alpha-recommend", reason_codes=["strong_edge"]),
        side_edge_row_payload(
            "beta-watch",
            side_probability="0.640000",
            market_implied_probability="0.600000",
            total_cost_per_share="0.010000",
            action="watch",
            reason_codes=["below_min_net_probability_edge"],
        ),
    )
    path.write_text(
        "\n".join(json.dumps(payload, sort_keys=True) for payload in payloads) + "\n\n",
        encoding="utf-8",
    )

    rows = read_paper_probability_recommendation_queue_side_edge_rows(path)

    assert tuple(row.market_slug for row in rows) == ("alpha-recommend", "beta-watch")
    assert all(type(row) is PaperProbabilitySideEdgeRow for row in rows)
    assert rows[0].side_probability == d("0.740000")
    assert rows[0].reason_codes == ("strong_edge",)

    report = build_paper_probability_recommendation_queue_report(
        rows,
        config=PaperProbabilityRecommendationQueueConfig(
            config_version="probability-recommendation-queue-v0",
            max_queue_rows=5,
            min_recommendation_score=d("0.050000"),
            include_watch=True,
        ),
        generated_at=GENERATED_AT,
    )
    assert report.input_count == 2
    assert tuple(row.market_slug for row in report.queue_rows) == (
        "alpha-recommend",
        "beta-watch",
    )


@pytest.mark.parametrize(
    ("name", "wrap", "expected_count"),
    (
        ("array", lambda rows: rows, 2),
        ("rows", lambda rows: {"rows": rows}, 2),
        ("side_edge_rows", lambda rows: {"side_edge_rows": rows}, 2),
        ("inputs", lambda rows: {"inputs": rows}, 2),
        ("input_rows", lambda rows: {"input_rows": rows}, 2),
        ("single", lambda rows: rows[0], 1),
    ),
)
def test_reads_json_arrays_envelopes_and_single_row_objects(
    tmp_path: Path,
    name: str,
    wrap: Callable[[list[dict[str, Any]]], object],
    expected_count: int,
) -> None:
    path = tmp_path / f"{name}.json"
    payloads = [
        side_edge_row_payload("alpha-recommend"),
        side_edge_row_payload("beta-recommend"),
    ]
    write_json(path, wrap(payloads))

    rows = read_paper_probability_recommendation_queue_side_edge_rows(str(path))

    assert len(rows) == expected_count
    assert rows[0].market_slug == "alpha-recommend"


@pytest.mark.parametrize(
    "payload",
    (
        "",
        [],
        {"rows": []},
        {"side_edge_rows": []},
        {"inputs": []},
        {"input_rows": []},
    ),
)
def test_empty_files_and_empty_arrays_return_empty_tuple(
    tmp_path: Path,
    payload: object,
) -> None:
    path = tmp_path / "empty-input.json"
    if payload == "":
        path.write_text("", encoding="utf-8")
    else:
        write_json(path, payload)

    assert read_paper_probability_recommendation_queue_side_edge_rows(path) == ()


def test_rejects_invalid_top_level_scalars_with_path_context(tmp_path: Path) -> None:
    path = tmp_path / "scalar.json"
    path.write_text("42", encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        read_paper_probability_recommendation_queue_side_edge_rows(path)

    message = str(exc_info.value)
    assert str(path) in message
    assert "JSON object, JSON array, or JSONL file" in message


def test_rejects_non_object_rows_with_row_number_and_path_context(
    tmp_path: Path,
) -> None:
    path = tmp_path / "invalid-row.json"
    write_json(path, [side_edge_row_payload("alpha-recommend"), ["not", "an", "object"]])

    with pytest.raises(ValueError) as exc_info:
        read_paper_probability_recommendation_queue_side_edge_rows(path)

    message = str(exc_info.value)
    assert str(path) in message
    assert "row 2" in message
    assert "must be a JSON object" in message


def test_rejects_hard_safety_flag_failures_with_row_context(tmp_path: Path) -> None:
    path = tmp_path / "unsafe-row.json"
    write_json(path, [side_edge_row_payload("unsafe-row", paper_only=False)])

    with pytest.raises(ValueError) as exc_info:
        read_paper_probability_recommendation_queue_side_edge_rows(path)

    message = str(exc_info.value)
    assert "row 1" in message
    assert "PaperProbabilitySideEdgeRow" in message
    assert "paper_only must be True" in message


def test_rejects_unsafe_envelope_hard_flags(tmp_path: Path) -> None:
    path = tmp_path / "unsafe-envelope.json"
    write_json(
        path,
        {
            "rows": [side_edge_row_payload("safe-row")],
            "paper_only": False,
            "report_only": True,
            "readonly": True,
        },
    )

    with pytest.raises(ValueError, match="input envelope must be paper_only"):
        read_paper_probability_recommendation_queue_side_edge_rows(path)


def test_rejects_malformed_decimal_values_with_row_and_path_context(
    tmp_path: Path,
) -> None:
    path = tmp_path / "bad-decimal.json"
    malformed_payload = side_edge_row_payload("bad-decimal")
    malformed_payload["side_probability"] = "not-a-decimal"
    write_json(path, [side_edge_row_payload("alpha-recommend"), malformed_payload])

    with pytest.raises(ValueError) as exc_info:
        read_paper_probability_recommendation_queue_side_edge_rows(path)

    message = str(exc_info.value)
    assert str(path) in message
    assert "row 2" in message
    assert "PaperProbabilitySideEdgeRow" in message
