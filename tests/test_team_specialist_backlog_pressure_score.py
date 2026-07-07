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
    / "team_specialist_backlog_pressure_score.py"
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_backlog_pressure_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def hidden_word(hex_value: str) -> str:
    return bytes.fromhex(hex_value).decode("ascii")


def backlog_input(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "team_id": "team-alpha",
        "specialist_id": "specialist-review-alpha",
        "open_item_count": d("2"),
        "urgent_item_count": d("0"),
        "stale_item_count": d("0"),
        "average_age_hours": d("8.000000"),
        "capacity_per_day": d("10.000000"),
        "recent_completion_count": d("10"),
        "calibration_score": d("0.900000"),
    }
    values.update(overrides)
    return module.TeamSpecialistBacklogPressureScoreInput(**values)


def score(**overrides: object) -> Any:
    module = api()
    return module.score_team_specialist_backlog_pressure(
        backlog_input(**overrides),
        config=module.TeamSpecialistBacklogPressureScoreConfig(),
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


def test_low_pressure_backlog_passes_new_review_routing() -> None:
    report = score()

    assert is_dataclass(report)
    assert report.team_id == "team-alpha"
    assert report.specialist_id == "specialist-review-alpha"
    assert report.open_item_count == d("2")
    assert report.urgent_item_count == d("0")
    assert report.stale_item_count == d("0")
    assert report.average_age_hours == d("8.000000")
    assert report.capacity_per_day == d("10.000000")
    assert report.recent_completion_count == d("10")
    assert report.calibration_score == d("0.900000")
    assert report.backlog_to_capacity_ratio == d("0.200000")
    assert report.urgent_item_ratio == d("0.000000")
    assert report.stale_item_ratio == d("0.000000")
    assert report.average_age_pressure == d("0.111111")
    assert report.completion_gap_ratio == d("0.000000")
    assert report.calibration_pressure == d("0.100000")
    assert report.backlog_pressure_score == d("0.091111")
    assert report.overload_status == "pass"
    assert report.routing_priority_status == "pass"
    assert report.report_status == "pass"
    assert report.overloaded is False
    assert report.reason_codes == (
        "backlog_pressure_pass",
        "capacity_load_pass",
        "completion_flow_clear",
        "calibration_clear",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_overloaded_backlog_blocks_new_review_routing() -> None:
    report = score(
        open_item_count=d("20"),
        urgent_item_count=d("5"),
        stale_item_count=d("8"),
        average_age_hours=d("96.000000"),
        capacity_per_day=d("8.000000"),
        recent_completion_count=d("2"),
        calibration_score=d("0.400000"),
    )

    assert report.backlog_to_capacity_ratio == d("1.000000")
    assert report.raw_backlog_to_capacity_ratio == d("2.500000")
    assert report.urgent_item_ratio == d("0.250000")
    assert report.stale_item_ratio == d("0.400000")
    assert report.average_age_pressure == d("1.000000")
    assert report.completion_gap_ratio == d("0.750000")
    assert report.calibration_pressure == d("0.600000")
    assert report.backlog_pressure_score == d("0.695000")
    assert report.overload_status == "block"
    assert report.routing_priority_status == "block"
    assert report.report_status == "block"
    assert report.overloaded is True
    assert report.reason_codes == (
        "backlog_pressure_block",
        "capacity_load_block",
        "urgent_item_pressure",
        "stale_item_pressure",
        "average_age_pressure",
        "completion_gap_pressure",
        "calibration_pressure",
    )


def test_stale_backlog_watches_new_review_routing_without_capacity_overload() -> None:
    report = score(
        open_item_count=d("6"),
        urgent_item_count=d("0"),
        stale_item_count=d("3"),
        average_age_hours=d("80.000000"),
        capacity_per_day=d("10.000000"),
        recent_completion_count=d("8"),
        calibration_score=d("0.900000"),
    )

    assert report.backlog_to_capacity_ratio == d("0.600000")
    assert report.stale_item_ratio == d("0.500000")
    assert report.average_age_pressure == d("1.000000")
    assert report.completion_gap_ratio == d("0.200000")
    assert report.backlog_pressure_score == d("0.415000")
    assert report.overload_status == "pass"
    assert report.routing_priority_status == "watch"
    assert report.report_status == "watch"
    assert report.overloaded is False
    assert report.reason_codes == (
        "backlog_pressure_watch",
        "capacity_load_pass",
        "stale_item_pressure",
        "average_age_pressure",
        "completion_flow_watch",
        "calibration_clear",
    )


def test_zero_and_negative_capacity_are_rejected() -> None:
    with pytest.raises(ValueError, match="capacity_per_day must be positive"):
        backlog_input(capacity_per_day=d("0.000000"))

    with pytest.raises(ValueError, match="capacity_per_day must be positive"):
        backlog_input(capacity_per_day=d("-1.000000"))


def test_decimal_exact_type_validation_rejects_int_float_and_subclass_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="open_item_count must be exactly Decimal"):
        backlog_input(open_item_count=1)

    with pytest.raises(ValueError, match="capacity_per_day must be exactly Decimal"):
        backlog_input(capacity_per_day=10.0)

    with pytest.raises(ValueError, match="urgent_item_count must be exactly Decimal"):
        backlog_input(urgent_item_count=_DecimalSubclass("1"))

    with pytest.raises(ValueError, match="average_age_hours must use six decimal places or fewer"):
        backlog_input(average_age_hours=d("1.0000001"))

    with pytest.raises(ValueError, match="stale_item_count must not exceed open_item_count"):
        backlog_input(open_item_count=d("2"), stale_item_count=d("3"))

    with pytest.raises(ValueError, match="urgent_item_count must not exceed open_item_count"):
        backlog_input(open_item_count=d("2"), urgent_item_count=d("3"))

    with pytest.raises(ValueError, match="score weights must sum to 1.000000"):
        module.TeamSpecialistBacklogPressureScoreConfig(
            calibration_weight=d("0.110000"),
        )


def test_public_payload_rejects_leaks_and_non_public_status_words() -> None:
    module = api()
    leak = hidden_word("77616c6c6574")

    with pytest.raises(ValueError, match="unsafe public value"):
        backlog_input(team_id=f"team-{leak}")

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
        module.team_specialist_backlog_pressure_score_payload(tampered_payload)

    tampered_payload = dict(payload)
    tampered_payload["team_id"] = f"team-{hidden_word('7472616465')}"
    with pytest.raises(ValueError, match="unsafe public value"):
        module.team_specialist_backlog_pressure_score_payload(tampered_payload)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistBacklogPressureScoreConfig()
    input_signal = backlog_input()
    report = score()

    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_BACKLOG_PRESSURE_SCORE_CONFIG_VERSION",
        "TEAM_SPECIALIST_BACKLOG_PRESSURE_SCORE_STATUSES",
        "TeamSpecialistBacklogPressureScoreConfig",
        "TeamSpecialistBacklogPressureScoreInput",
        "TeamSpecialistBacklogPressureScoreReport",
        "score_team_specialist_backlog_pressure",
        "team_specialist_backlog_pressure_score_payload",
    )

    for item in (config, input_signal, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]

    numeric_fields = {
        "backlog_load_weight",
        "urgent_share_weight",
        "stale_share_weight",
        "average_age_weight",
        "completion_gap_weight",
        "calibration_weight",
        "capacity_watch_ratio",
        "capacity_block_ratio",
        "score_watch_floor",
        "score_block_floor",
        "stale_age_hours",
        "open_item_count",
        "urgent_item_count",
        "stale_item_count",
        "average_age_hours",
        "capacity_per_day",
        "recent_completion_count",
        "calibration_score",
        "raw_backlog_to_capacity_ratio",
        "backlog_to_capacity_ratio",
        "urgent_item_ratio",
        "stale_item_ratio",
        "average_age_pressure",
        "completion_gap_ratio",
        "calibration_pressure",
        "backlog_pressure_score",
    }

    for cls in (
        module.TeamSpecialistBacklogPressureScoreConfig,
        module.TeamSpecialistBacklogPressureScoreInput,
        module.TeamSpecialistBacklogPressureScoreReport,
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
        module.TeamSpecialistBacklogPressureScoreConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        replace(input_signal, report_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)


def test_payload_and_report_consistency_reject_manual_tampering() -> None:
    module = api()
    report = score(
        open_item_count=d("6"),
        stale_item_count=d("3"),
        average_age_hours=d("80.000000"),
        capacity_per_day=d("10.000000"),
        recent_completion_count=d("8"),
    )

    payload = module.team_specialist_backlog_pressure_score_payload(report)
    assert payload == report.payload
    assert payload["open_item_count"] == "6"
    assert payload["capacity_per_day"] == "10.000000"
    assert payload["backlog_pressure_score"] == "0.415000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert_no_float_or_int_values(payload)
    json.dumps(payload, sort_keys=True)

    with pytest.raises(ValueError, match="backlog_pressure_score must match components"):
        replace(report, backlog_pressure_score=d("0.000000"))

    with pytest.raises(ValueError, match="routing_priority_status must match score and overload"):
        replace(report, routing_priority_status="pass")

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)

    tampered_payload = dict(payload)
    tampered_payload["backlog_pressure_score"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest must match public payload"):
        module.team_specialist_backlog_pressure_score_payload(tampered_payload)


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
