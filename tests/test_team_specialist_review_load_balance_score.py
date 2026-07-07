from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_review_load_balance_score.py"
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_review_load_balance_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def hidden_word(hex_value: str) -> str:
    return bytes.fromhex(hex_value).decode("ascii")


def load_input(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "team_id": "team-alpha",
        "specialist_id": "specialist-review-alpha",
        "assigned_review_count": d("10"),
        "active_review_count": d("8"),
        "stale_review_count": d("1"),
        "daily_review_capacity": d("10.000000"),
        "completed_review_count": d("8"),
    }
    values.update(overrides)
    return module.TeamSpecialistReviewLoadBalanceScoreInput(**values)


def score(*items: object, cfg: object | None = None) -> Any:
    module = api()
    return module.score_team_specialist_review_load_balance(
        items,
        config=cfg if cfg is not None else module.TeamSpecialistReviewLoadBalanceScoreConfig(),
    )


def assert_no_float_or_int_values(value: Any) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (float, int)):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_or_int_values(item)


def assert_status_vocabulary(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key.endswith("_status"):
                assert item in {"pass", "watch", "block"}
            assert_status_vocabulary(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_status_vocabulary(item)


def test_balanced_review_load_passes_without_rebalance() -> None:
    report = score(
        load_input(specialist_id="specialist-review-b"),
        load_input(specialist_id="specialist-review-a"),
    )

    assert is_dataclass(report)
    assert report.report_status == "pass"
    assert report.load_balance_status == "pass"
    assert report.rebalance_research_queue is False
    assert report.specialist_count == d("2")
    assert report.total_assigned_review_count == d("20")
    assert report.total_active_review_count == d("16")
    assert report.total_stale_review_count == d("2")
    assert report.total_daily_review_capacity == d("20.000000")
    assert report.max_assignment_pressure == d("0.000000")
    assert report.capacity_utilization_spread == d("0.000000")
    assert report.queue_depth_spread_ratio == d("0.000000")
    assert report.stale_review_ratio_spread == d("0.000000")
    assert report.overloaded_specialist_share == d("0.000000")
    assert report.review_load_balance_score == d("0.000000")
    assert report.reason_codes == (
        "review_load_balance_pass",
        "assignment_pressure_clear",
        "utilization_spread_clear",
        "queue_depth_spread_clear",
        "stale_review_spread_clear",
        "overloaded_specialist_share_clear",
    )
    assert tuple(row.specialist_id for row in report.rows) == (
        "specialist-review-a",
        "specialist-review-b",
    )
    assert tuple(row.rank for row in report.rows) == (d("1"), d("2"))
    assert tuple(row.row_status for row in report.rows) == ("pass", "pass")
    assert tuple(row.assigned_review_share for row in report.rows) == (
        d("0.500000"),
        d("0.500000"),
    )
    assert tuple(row.capacity_share for row in report.rows) == (
        d("0.500000"),
        d("0.500000"),
    )


def test_moderately_skewed_review_load_watches_for_research_queue_rebalance() -> None:
    report = score(
        load_input(
            specialist_id="specialist-review-heavy",
            assigned_review_count=d("15"),
            active_review_count=d("12"),
            stale_review_count=d("3"),
            daily_review_capacity=d("10.000000"),
            completed_review_count=d("5"),
        ),
        load_input(
            specialist_id="specialist-review-light",
            assigned_review_count=d("5"),
            active_review_count=d("4"),
            stale_review_count=d("0"),
            daily_review_capacity=d("10.000000"),
            completed_review_count=d("8"),
        ),
    )

    assert report.report_status == "watch"
    assert report.load_balance_status == "watch"
    assert report.rebalance_research_queue is True
    assert report.max_assignment_pressure == d("0.500000")
    assert report.capacity_utilization_spread == d("1.000000")
    assert report.queue_depth_spread_ratio == d("0.666667")
    assert report.stale_review_ratio_spread == d("0.200000")
    assert report.overloaded_specialist_share == d("0.500000")
    assert report.review_load_balance_score == d("0.613333")
    assert report.reason_codes == (
        "review_load_balance_watch",
        "assignment_pressure_watch",
        "utilization_spread_watch",
        "queue_depth_spread_watch",
        "stale_review_spread_watch",
        "overloaded_specialist_share_watch",
    )
    assert tuple(row.row_status for row in report.rows) == ("watch", "pass")
    assert report.rows[0].reason_codes == (
        "review_load_balance_row_assignment_pressure",
        "review_load_balance_row_over_capacity",
        "review_load_balance_row_stale_reviews",
    )


def test_extreme_review_load_imbalance_blocks_new_research_queue_assignment() -> None:
    report = score(
        load_input(
            specialist_id="specialist-review-heavy",
            assigned_review_count=d("19"),
            active_review_count=d("18"),
            stale_review_count=d("10"),
            daily_review_capacity=d("10.000000"),
            completed_review_count=d("2"),
        ),
        load_input(
            specialist_id="specialist-review-light",
            assigned_review_count=d("1"),
            active_review_count=d("1"),
            stale_review_count=d("0"),
            daily_review_capacity=d("10.000000"),
            completed_review_count=d("10"),
        ),
    )

    assert report.report_status == "block"
    assert report.load_balance_status == "block"
    assert report.rebalance_research_queue is True
    assert report.max_assignment_pressure == d("0.900000")
    assert report.capacity_utilization_spread == d("1.800000")
    assert report.queue_depth_spread_ratio == d("0.947368")
    assert report.stale_review_ratio_spread == d("0.526316")
    assert report.overloaded_specialist_share == d("0.500000")
    assert report.review_load_balance_score == d("0.868474")
    assert report.reason_codes == (
        "review_load_balance_block",
        "assignment_pressure_block",
        "utilization_spread_block",
        "queue_depth_spread_block",
        "stale_review_spread_block",
        "overloaded_specialist_share_watch",
    )
    assert tuple(row.row_status for row in report.rows) == ("block", "pass")


def test_decimal_exact_type_validation_rejects_int_float_and_subclass_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="assigned_review_count must be exactly Decimal"):
        load_input(assigned_review_count=1)

    with pytest.raises(ValueError, match="daily_review_capacity must be exactly Decimal"):
        load_input(daily_review_capacity=10.0)

    with pytest.raises(ValueError, match="active_review_count must be exactly Decimal"):
        load_input(active_review_count=_DecimalSubclass("1"))

    with pytest.raises(ValueError, match="daily_review_capacity must use six decimal places or fewer"):
        load_input(daily_review_capacity=d("1.0000001"))

    with pytest.raises(ValueError, match="stale_review_count must not exceed assigned_review_count"):
        load_input(assigned_review_count=d("2"), stale_review_count=d("3"))

    with pytest.raises(ValueError, match="active_review_count must not exceed assigned_review_count"):
        load_input(assigned_review_count=d("2"), active_review_count=d("3"))

    with pytest.raises(ValueError, match="score weights must sum to 1.000000"):
        module.TeamSpecialistReviewLoadBalanceScoreConfig(
            stale_review_spread_weight=d("0.160000"),
        )


def test_public_payload_rejects_leaks_and_uses_only_public_statuses() -> None:
    module = api()
    leak = hidden_word("77616c6c6574")

    with pytest.raises(ValueError, match="unsafe public value"):
        load_input(team_id=f"team-{leak}")

    payload = score(
        load_input(specialist_id="specialist-review-a"),
        load_input(specialist_id="specialist-review-b"),
    ).payload
    assert_status_vocabulary(payload)
    payload_text = json.dumps(payload, sort_keys=True)
    for hidden in (
        "726177",
        "6d61726b65745f6964",
        "63616e6469646174655f6964",
        "6d61726b65745f736c7567",
        "7175657374696f6e",
        "75726c",
        "736f757263655f726566",
        "736f757263655f74657874",
        "64736e",
        "7461626c655f6e616d65",
        "746f6b656e",
        "61757468",
        "77616c6c6574",
        "6f72646572",
        "7472616465",
        "706f736974696f6e",
        "627579",
        "73656c6c",
        "7265636f6d6d656e646174696f6e",
    ):
        assert hidden_word(hidden) not in payload_text.lower()

    tampered_payload = dict(payload)
    tampered_payload[hidden_word("6d61726b65745f6964")] = "redacted"
    with pytest.raises(ValueError, match="unsafe public key"):
        module.team_specialist_review_load_balance_score_payload(tampered_payload)

    tampered_payload = dict(payload)
    tampered_payload["team_id"] = f"team-{hidden_word('7472616465')}"
    with pytest.raises(ValueError, match="unsafe public value"):
        module.team_specialist_review_load_balance_score_payload(tampered_payload)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistReviewLoadBalanceScoreConfig()
    input_signal = load_input()
    report = score(
        load_input(specialist_id="specialist-review-a"),
        load_input(specialist_id="specialist-review-b"),
    )

    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_REVIEW_LOAD_BALANCE_SCORE_CONFIG_VERSION",
        "TEAM_SPECIALIST_REVIEW_LOAD_BALANCE_SCORE_STATUSES",
        "TeamSpecialistReviewLoadBalanceScoreConfig",
        "TeamSpecialistReviewLoadBalanceScoreInput",
        "TeamSpecialistReviewLoadBalanceScoreRow",
        "TeamSpecialistReviewLoadBalanceScoreReport",
        "score_team_specialist_review_load_balance",
        "team_specialist_review_load_balance_score_payload",
    )

    for item in (config, input_signal, report, report.rows[0]):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]

    numeric_fields = {
        "assignment_pressure_weight",
        "capacity_utilization_spread_weight",
        "queue_depth_spread_weight",
        "stale_review_spread_weight",
        "overloaded_specialist_share_weight",
        "assignment_pressure_watch_floor",
        "assignment_pressure_block_floor",
        "capacity_utilization_spread_watch_floor",
        "capacity_utilization_spread_block_floor",
        "queue_depth_spread_watch_floor",
        "queue_depth_spread_block_floor",
        "stale_review_spread_watch_floor",
        "stale_review_spread_block_floor",
        "overloaded_specialist_share_watch_floor",
        "overloaded_specialist_share_block_floor",
        "overloaded_utilization_floor",
        "score_watch_floor",
        "score_block_floor",
        "rank",
        "assigned_review_count",
        "active_review_count",
        "stale_review_count",
        "daily_review_capacity",
        "completed_review_count",
        "assigned_review_share",
        "capacity_share",
        "expected_assigned_review_count",
        "allocation_gap_count",
        "absolute_allocation_gap_count",
        "assignment_pressure",
        "capacity_utilization_ratio",
        "stale_review_ratio",
        "specialist_count",
        "total_assigned_review_count",
        "total_active_review_count",
        "total_stale_review_count",
        "total_daily_review_capacity",
        "max_assignment_pressure",
        "capacity_utilization_spread",
        "queue_depth_spread_ratio",
        "stale_review_ratio_spread",
        "overloaded_specialist_share",
        "review_load_balance_score",
    }

    for cls in (
        module.TeamSpecialistReviewLoadBalanceScoreConfig,
        module.TeamSpecialistReviewLoadBalanceScoreInput,
        module.TeamSpecialistReviewLoadBalanceScoreRow,
        module.TeamSpecialistReviewLoadBalanceScoreReport,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in numeric_fields:
                assert hints[item.name] is Decimal

    for item in (config, input_signal, report, report.rows[0]):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in numeric_fields:
                assert type(value) is Decimal

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistReviewLoadBalanceScoreConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        replace(input_signal, report_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)


def test_payload_is_deterministic_and_digest_consistent() -> None:
    module = api()
    a = load_input(specialist_id="specialist-review-a")
    b = load_input(specialist_id="specialist-review-b")
    first = score(b, a)
    second = score(a, b)

    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest
    payload = module.team_specialist_review_load_balance_score_payload(first)
    assert payload == first.payload
    assert payload["review_load_balance_score"] == "0.000000"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    assert_no_float_or_int_values(payload)
    json.dumps(payload, sort_keys=True)

    with pytest.raises(ValueError, match="review_load_balance_score must match components"):
        replace(first, review_load_balance_score=d("0.100000"))

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(first, derived_validation_digest="0" * 64)

    tampered_payload = dict(payload)
    tampered_payload["review_load_balance_score"] = "0.100000"
    with pytest.raises(ValueError, match="derived_validation_digest must match public payload"):
        module.team_specialist_review_load_balance_score_payload(tampered_payload)


def test_module_scope_has_no_external_write_or_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    for forbidden in (
        "requests",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "supabase",
        "subprocess",
        "open(",
        "read_text",
        "write_text",
        ".connect(",
        ".execute(",
        ".post(",
        ".put(",
        ".delete(",
    ):
        assert forbidden not in source
    for hidden in (
        "6c697665",
        "61757468",
        "77616c6c6574",
        "6f72646572",
        "7472616465",
        "627579",
        "73656c6c",
        "746f6b656e",
        "7375706162617365",
    ):
        assert hidden_word(hidden) not in source
