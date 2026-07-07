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
    / "team_specialist_workload_volatility_score.py"
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_workload_volatility_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def hidden_word(hex_value: str) -> str:
    return bytes.fromhex(hex_value).decode("ascii")


def workload_input(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "team_id": "team-alpha",
        "specialist_id": "specialist-research-alpha",
        "current_open_count": d("5"),
        "prior_open_count": d("5"),
        "urgent_ratio": d("0.050000"),
        "completion_variability_score": d("0.100000"),
        "stale_item_ratio": d("0.050000"),
        "capacity_utilization_score": d("0.400000"),
    }
    values.update(overrides)
    return module.TeamSpecialistWorkloadVolatilityScoreInput(**values)


def score(**overrides: object) -> Any:
    module = api()
    return module.score_team_specialist_workload_volatility(
        workload_input(**overrides),
        config=module.TeamSpecialistWorkloadVolatilityScoreConfig(),
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
    forbidden_statuses = {
        hidden_word("7265616479"),
        hidden_word("626c6f636b6564"),
        hidden_word("6d617463686564"),
        hidden_word("737570706f72746564"),
    }
    if isinstance(value, dict):
        for key, item in value.items():
            if key.endswith("_status"):
                assert item in {"pass", "watch", "block"}
                assert item not in forbidden_statuses
            assert_status_vocabulary(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_status_vocabulary(item)


def test_stable_workload_passes_new_research_routing() -> None:
    report = score()

    assert is_dataclass(report)
    assert report.team_id == "team-alpha"
    assert report.specialist_id == "specialist-research-alpha"
    assert report.current_open_count == d("5")
    assert report.prior_open_count == d("5")
    assert report.urgent_ratio == d("0.050000")
    assert report.completion_variability_score == d("0.100000")
    assert report.stale_item_ratio == d("0.050000")
    assert report.capacity_utilization_score == d("0.400000")
    assert report.open_count_delta == d("0.000000")
    assert report.absolute_open_count_delta == d("0.000000")
    assert report.open_count_volatility_ratio == d("0.000000")
    assert report.workload_volatility_score == d("0.102000")
    assert report.workload_volatility_status == "pass"
    assert report.routing_priority_status == "pass"
    assert report.report_status == "pass"
    assert report.reduce_new_research_routing_priority is False
    assert report.reason_codes == (
        "workload_volatility_pass",
        "open_count_change_pass",
        "urgent_ratio_clear",
        "completion_variability_clear",
        "stale_item_ratio_clear",
        "capacity_utilization_clear",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_severe_workload_volatility_blocks_new_research_routing() -> None:
    report = score(
        current_open_count=d("18"),
        prior_open_count=d("6"),
        urgent_ratio=d("0.650000"),
        completion_variability_score=d("0.800000"),
        stale_item_ratio=d("0.550000"),
        capacity_utilization_score=d("0.980000"),
    )

    assert report.open_count_delta == d("12.000000")
    assert report.absolute_open_count_delta == d("12.000000")
    assert report.open_count_volatility_ratio == d("1.000000")
    assert report.workload_volatility_score == d("0.826800")
    assert report.workload_volatility_status == "block"
    assert report.routing_priority_status == "block"
    assert report.report_status == "block"
    assert report.reduce_new_research_routing_priority is True
    assert report.reason_codes == (
        "workload_volatility_block",
        "open_count_change_block",
        "urgent_ratio_pressure",
        "completion_variability_pressure",
        "stale_item_ratio_pressure",
        "capacity_utilization_pressure",
    )


def test_moderate_workload_volatility_watches_new_research_routing() -> None:
    report = score(
        current_open_count=d("8"),
        prior_open_count=d("6"),
        urgent_ratio=d("0.150000"),
        completion_variability_score=d("0.350000"),
        stale_item_ratio=d("0.200000"),
        capacity_utilization_score=d("0.800000"),
    )

    assert report.open_count_delta == d("2.000000")
    assert report.absolute_open_count_delta == d("2.000000")
    assert report.open_count_volatility_ratio == d("0.333333")
    assert report.workload_volatility_score == d("0.360000")
    assert report.workload_volatility_status == "watch"
    assert report.routing_priority_status == "watch"
    assert report.report_status == "watch"
    assert report.reduce_new_research_routing_priority is True
    assert report.reason_codes == (
        "workload_volatility_watch",
        "open_count_change_watch",
        "urgent_ratio_clear",
        "completion_variability_watch",
        "stale_item_ratio_watch",
        "capacity_utilization_watch",
    )


def test_decimal_exact_type_validation_rejects_int_float_and_subclass_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="current_open_count must be exactly Decimal"):
        workload_input(current_open_count=5)

    with pytest.raises(ValueError, match="urgent_ratio must be exactly Decimal"):
        workload_input(urgent_ratio=0.05)

    with pytest.raises(ValueError, match="prior_open_count must be exactly Decimal"):
        workload_input(prior_open_count=_DecimalSubclass("5"))

    with pytest.raises(ValueError, match="stale_item_ratio must use six decimal places or fewer"):
        workload_input(stale_item_ratio=d("0.1234567"))

    with pytest.raises(ValueError, match="capacity_utilization_score must be <= 1.000000"):
        workload_input(capacity_utilization_score=d("1.000001"))

    with pytest.raises(ValueError, match="score weights must sum to 1.000000"):
        module.TeamSpecialistWorkloadVolatilityScoreConfig(
            capacity_utilization_weight=d("0.170000"),
        )

    with pytest.raises(ValueError, match="score watch threshold must not exceed block threshold"):
        module.TeamSpecialistWorkloadVolatilityScoreConfig(
            score_watch_floor=d("0.700000"),
        )


def test_public_payload_rejects_leaks_and_non_public_status_words() -> None:
    module = api()
    leak = hidden_word("77616c6c6574")

    with pytest.raises(ValueError, match="unsafe public value"):
        workload_input(team_id=f"team-{leak}")

    payload = score().payload
    assert_status_vocabulary(payload)
    payload_text = json.dumps(payload, sort_keys=True)
    for hidden in (
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
        "736563726574",
        "61757468",
        "77616c6c6574",
        "6f72646572",
        "7472616465",
        "627579",
        "73656c6c",
        "7265636f6d6d656e646174696f6e",
        "706f736974696f6e5f73697a65",
    ):
        assert hidden_word(hidden) not in payload_text.lower()

    tampered_payload = dict(payload)
    tampered_payload[hidden_word("6d61726b65745f6964")] = "redacted"
    with pytest.raises(ValueError, match="unsafe public key"):
        module.team_specialist_workload_volatility_score_payload(tampered_payload)

    tampered_payload = dict(payload)
    tampered_payload["team_id"] = f"team-{hidden_word('7472616465')}"
    with pytest.raises(ValueError, match="unsafe public value"):
        module.team_specialist_workload_volatility_score_payload(tampered_payload)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistWorkloadVolatilityScoreConfig()
    input_signal = workload_input()
    report = score()

    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_WORKLOAD_VOLATILITY_SCORE_CONFIG_VERSION",
        "TEAM_SPECIALIST_WORKLOAD_VOLATILITY_SCORE_STATUSES",
        "TeamSpecialistWorkloadVolatilityScoreConfig",
        "TeamSpecialistWorkloadVolatilityScoreInput",
        "TeamSpecialistWorkloadVolatilityScoreReport",
        "score_team_specialist_workload_volatility",
        "team_specialist_workload_volatility_score_payload",
    )

    for item in (config, input_signal, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]

    numeric_fields = {
        "open_count_change_weight",
        "urgent_ratio_weight",
        "completion_variability_weight",
        "stale_item_ratio_weight",
        "capacity_utilization_weight",
        "open_count_change_watch_ratio",
        "open_count_change_block_ratio",
        "urgent_ratio_watch_floor",
        "urgent_ratio_block_floor",
        "completion_variability_watch_floor",
        "completion_variability_block_floor",
        "stale_item_ratio_watch_floor",
        "stale_item_ratio_block_floor",
        "capacity_utilization_watch_floor",
        "capacity_utilization_block_floor",
        "score_watch_floor",
        "score_block_floor",
        "current_open_count",
        "prior_open_count",
        "urgent_ratio",
        "completion_variability_score",
        "stale_item_ratio",
        "capacity_utilization_score",
        "open_count_delta",
        "absolute_open_count_delta",
        "open_count_volatility_ratio",
        "workload_volatility_score",
    }

    for cls in (
        module.TeamSpecialistWorkloadVolatilityScoreConfig,
        module.TeamSpecialistWorkloadVolatilityScoreInput,
        module.TeamSpecialistWorkloadVolatilityScoreReport,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in numeric_fields:
                assert hints[item.name] is Decimal

    for item in (config, input_signal, report):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in numeric_fields:
                assert type(value) is Decimal

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistWorkloadVolatilityScoreConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        replace(input_signal, report_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)


def test_deterministic_payload_and_report_consistency_reject_manual_tampering() -> None:
    module = api()
    report = score(
        current_open_count=d("8"),
        prior_open_count=d("6"),
        urgent_ratio=d("0.150000"),
        completion_variability_score=d("0.350000"),
        stale_item_ratio=d("0.200000"),
        capacity_utilization_score=d("0.800000"),
    )
    same_report = score(
        current_open_count=d("8"),
        prior_open_count=d("6"),
        urgent_ratio=d("0.150000"),
        completion_variability_score=d("0.350000"),
        stale_item_ratio=d("0.200000"),
        capacity_utilization_score=d("0.800000"),
    )

    payload = module.team_specialist_workload_volatility_score_payload(report)
    assert payload == report.payload
    assert payload == same_report.payload
    assert payload["current_open_count"] == "8"
    assert payload["open_count_volatility_ratio"] == "0.333333"
    assert payload["workload_volatility_score"] == "0.360000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert_no_float_or_int_values(payload)
    json.dumps(payload, sort_keys=True)

    with pytest.raises(ValueError, match="workload_volatility_score must match components"):
        replace(report, workload_volatility_score=d("0.000000"))

    with pytest.raises(ValueError, match="routing_priority_status must match volatility status"):
        replace(report, routing_priority_status="pass")

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)

    tampered_payload = dict(payload)
    tampered_payload["workload_volatility_score"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest must match public payload"):
        module.team_specialist_workload_volatility_score_payload(tampered_payload)


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
        "736563726574",
        "7375706162617365",
    ):
        assert hidden_word(hidden) not in source
