from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module("polymarket_alpha_lab.cost_edge_decay_response_queue")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": module.DEFAULT_COST_EDGE_DECAY_RESPONSE_QUEUE_CONFIG_VERSION,
        "stale_observation_count": 3,
        "review_decay_threshold": d("0.020000"),
        "abstain_cost_adjusted_edge_threshold": d("0.010000"),
    }
    values.update(overrides)
    return module.CostEdgeDecayResponseQueueConfig(**values)


def observation(edge_key: str, sequence: int, edge: str, **overrides: object):
    module = api()
    values = {
        "edge_key": edge_key,
        "observation_sequence": sequence,
        "observed_at": datetime(2026, 7, 2, 9, sequence, tzinfo=UTC),
        "cost_adjusted_edge": d(edge),
        "source_count": d("1"),
    }
    values.update(overrides)
    return module.CostEdgeDecayObservation(**values)


def report(*rows, cfg=None):
    module = api()
    return module.build_cost_edge_decay_response_queue_report(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_response_queue_reduces_edge_decay_observations_into_status_rows() -> None:
    queue = report(
        observation("alpha", 1, "0.080000"),
        observation("alpha", 2, "0.055000"),
        observation("alpha", 3, "0.040000"),
        observation("alpha", 4, "0.020000"),
        observation("beta", 1, "0.030000"),
        observation("beta", 2, "0.029000"),
        observation("delta", 1, "0.020000"),
        observation("delta", 2, "0.019500"),
        observation("delta", 3, "0.019000"),
        observation("gamma", 1, "0.009000"),
        observation("gamma", 2, "0.008000"),
        observation("gamma", 3, "0.007000"),
    )

    assert is_dataclass(queue)
    assert queue.generated_at == GENERATED_AT
    assert queue.config_version == "cost-edge-decay-response-queue-v0"
    assert queue.observation_count == d("12")
    assert queue.edge_count == d("4")
    assert queue.review_needed_count == d("1")
    assert queue.abstain_until_refresh_count == d("1")
    assert queue.stale_edge_count == d("1")
    assert queue.monitor_only_count == d("1")
    assert queue.status == "response_queue_attention"
    assert queue.reason_codes == (
        "review_needed_edges_present",
        "stale_edges_require_refresh",
        "abstain_until_refresh_edges_present",
    )
    assert queue.boundary_statement == (
        "Report-only cost-edge decay response queue; no investment guidance or trade instructions."
    )
    assert queue.paper_only is True
    assert queue.report_only is True
    assert queue.readonly is True

    assert tuple(row.edge_key for row in queue.response_rows) == (
        "alpha",
        "gamma",
        "delta",
        "beta",
    )
    review = queue.response_rows[0]
    assert review.response_status == "review_needed"
    assert review.observation_count == d("4")
    assert review.first_cost_adjusted_edge == d("0.080000")
    assert review.latest_cost_adjusted_edge == d("0.020000")
    assert review.peak_cost_adjusted_edge == d("0.080000")
    assert review.edge_delta == d("-0.060000")
    assert review.edge_decay == d("0.060000")
    assert review.reason_codes == ("edge_decay_review_needed",)

    stale = queue.response_rows[1]
    assert stale.edge_key == "gamma"
    assert stale.response_status == "abstain_until_refresh"
    assert stale.latest_cost_adjusted_edge == d("0.007000")
    assert stale.edge_decay == d("0.002000")
    assert stale.reason_codes == (
        "stale_edge",
        "edge_below_refresh_threshold",
    )

    stale_edge = queue.response_rows[2]
    assert stale_edge.edge_key == "delta"
    assert stale_edge.response_status == "stale_edge"
    assert stale_edge.latest_cost_adjusted_edge == d("0.019000")
    assert stale_edge.edge_decay == d("0.001000")
    assert stale_edge.reason_codes == ("stale_edge",)

    monitor = queue.response_rows[3]
    assert monitor.edge_key == "beta"
    assert monitor.response_status == "monitor_only"
    assert monitor.edge_delta == d("-0.001000")
    assert monitor.reason_codes == ("edge_decay_clear",)


def test_empty_response_queue_is_report_only_and_zero_counted() -> None:
    queue = report()

    assert queue.observation_count == d("0")
    assert queue.edge_count == d("0")
    assert queue.review_needed_count == d("0")
    assert queue.abstain_until_refresh_count == d("0")
    assert queue.stale_edge_count == d("0")
    assert queue.monitor_only_count == d("0")
    assert queue.status == "response_queue_clear"
    assert queue.reason_codes == ("cost_edge_decay_response_queue_clear",)
    assert queue.response_rows == ()


def test_response_queue_payload_is_json_ready_redacted_and_no_float() -> None:
    payload = api().cost_edge_decay_response_queue_payload(
        report(
            observation("alpha", 1, "0.050000"),
            observation("alpha", 2, "0.010000"),
        ),
    )

    payload_text = repr(payload).lower()
    assert "market_slug" not in payload_text
    assert "question" not in payload_text
    assert "payload" not in payload_text
    assert "recommend" not in payload_text
    assert "wallet" not in payload_text
    assert "order" not in payload_text
    assert "advice" not in payload_text
    assert payload["observation_count"] == "2"
    assert payload["response_rows"][0]["edge_key"] == "alpha"
    assert payload["response_rows"][0]["edge_decay"] == "0.040000"


def test_response_queue_has_deterministic_validation_digest_and_rejects_tampering() -> None:
    queue = report(
        observation("alpha", 1, "0.050000"),
        observation("alpha", 2, "0.010000"),
    )
    rebuilt = report(
        observation("alpha", 1, "0.050000"),
        observation("alpha", 2, "0.010000"),
    )

    assert queue.derived_validation_digest == rebuilt.derived_validation_digest
    assert len(queue.derived_validation_digest) == 64
    assert int(queue.derived_validation_digest, 16) >= 0

    payload = api().cost_edge_decay_response_queue_payload(queue)
    assert payload["derived_validation_digest"] == queue.derived_validation_digest

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(queue, derived_validation_digest="0" * 64)

    object.__setattr__(queue, "derived_validation_digest", rebuilt.derived_validation_digest)
    object.__setattr__(queue.response_rows[0], "edge_decay", d("0.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api().cost_edge_decay_response_queue_payload(queue)


def test_response_queue_rejects_invalid_inputs_and_duplicates() -> None:
    module = api()

    with pytest.raises(ValueError, match="observations must be a list or tuple"):
        module.build_cost_edge_decay_response_queue_report(
            object(),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report(object())
    with pytest.raises(ValueError, match="config must be"):
        module.build_cost_edge_decay_response_queue_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_cost_edge_decay_response_queue_report(
            (),
            config=config(),
            generated_at=object(),
        )
    with pytest.raises(ValueError, match="duplicate"):
        report(
            observation("alpha", 1, "0.050000"),
            observation("alpha", 1, "0.040000"),
        )


def test_response_queue_rejects_non_decimal_and_scalar_subclasses() -> None:
    module = api()

    with pytest.raises(ValueError, match="cost_adjusted_edge must be a Decimal"):
        module.CostEdgeDecayObservation(
            edge_key="alpha",
            observation_sequence=1,
            observed_at=datetime(2026, 7, 2, 9, 1, tzinfo=UTC),
            cost_adjusted_edge=0.02,
            source_count=d("1"),
        )
    with pytest.raises(ValueError, match="cost_adjusted_edge"):
        module.CostEdgeDecayObservation(
            edge_key="alpha",
            observation_sequence=1,
            observed_at=datetime(2026, 7, 2, 9, 1, tzinfo=UTC),
            cost_adjusted_edge=_DecimalSubclass("0.020000"),
            source_count=d("1"),
        )
    with pytest.raises(ValueError, match="edge_key"):
        observation(_StringSubclass("alpha"), 1, "0.020000")
    with pytest.raises(ValueError, match="generated_at"):
        module.build_cost_edge_decay_response_queue_report(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )


def test_response_queue_dataclasses_are_frozen_and_revalidate_flags_and_counts() -> None:
    module = api()
    queue = report(
        observation("alpha", 1, "0.050000"),
        observation("alpha", 2, "0.010000"),
    )

    with pytest.raises(FrozenInstanceError):
        queue.status = "response_queue_clear"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(queue, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(queue, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(queue, readonly=False)
    with pytest.raises(ValueError, match="observation_count"):
        replace(queue, observation_count=d("9"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(queue, reason_codes=("cost_edge_decay_response_queue_clear",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(queue.response_rows[0], paper_only=False)
    with pytest.raises(ValueError, match="paper_only"):
        module.CostEdgeDecayResponseQueueConfig(
            config_version="cost-edge-decay-response-queue-v0",
            paper_only=False,
        )


def test_module_scope_has_no_live_mutation_advice_or_float_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/cost_edge_decay_response_queue.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "market_slug",
        "question",
        "payload_json",
        "investment_recommendation",
        "durable",
        "open(",
        "fast",
        "rank",
        "advice",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def test_module_exports_are_local_only() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_COST_EDGE_DECAY_RESPONSE_QUEUE_CONFIG_VERSION",
        "CostEdgeDecayResponseQueueConfig",
        "CostEdgeDecayObservation",
        "CostEdgeDecayResponseRow",
        "CostEdgeDecayResponseQueueReport",
        "build_cost_edge_decay_response_queue_report",
        "cost_edge_decay_response_queue_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "cost_edge_decay_response_queue" not in getattr(root, "__all__", ())
