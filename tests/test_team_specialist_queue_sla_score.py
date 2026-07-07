from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_queue_sla_score.py"
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_queue_sla_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def hidden_word(hex_value: str) -> str:
    return bytes.fromhex(hex_value).decode("ascii")


def queue_input(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "team_id": "team-alpha",
        "specialist_id": "specialist-sla-alpha",
        "open_research_item_count": d("2"),
        "items_over_sla_count": d("0"),
        "oldest_item_age_hours": d("8.000000"),
        "average_item_age_hours": d("4.000000"),
        "manual_research_capacity_per_day": d("10.000000"),
    }
    values.update(overrides)
    return module.TeamSpecialistQueueSlaScoreInput(**values)


def score(**overrides: object) -> Any:
    module = api()
    return module.score_team_specialist_queue_sla(
        queue_input(**overrides),
        config=module.TeamSpecialistQueueSlaScoreConfig(),
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
                assert item != hidden_word("626c6f636b6564")
            assert_status_vocabulary(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_status_vocabulary(item)


def test_fresh_queue_passes_sla_and_keeps_manual_priority_low() -> None:
    report = score()

    assert report.team_id == "team-alpha"
    assert report.specialist_id == "specialist-sla-alpha"
    assert report.open_research_item_count == d("2")
    assert report.items_over_sla_count == d("0")
    assert report.oldest_item_age_hours == d("8.000000")
    assert report.average_item_age_hours == d("4.000000")
    assert report.manual_research_capacity_per_day == d("10.000000")
    assert report.queue_load_ratio == d("0.200000")
    assert report.over_sla_item_ratio == d("0.000000")
    assert report.oldest_age_sla_ratio == d("0.333333")
    assert report.average_age_sla_ratio == d("0.166667")
    assert report.queue_sla_score == d("0.178333")
    assert report.sla_status == "pass"
    assert report.manual_research_priority_status == "pass"
    assert report.report_status == "pass"
    assert report.reason_codes == (
        "queue_sla_pass",
        "oldest_age_clear",
        "over_sla_items_clear",
        "average_age_clear",
        "manual_capacity_clear",
    )


def test_aging_queue_watches_before_breaching_sla() -> None:
    report = score(
        open_research_item_count=d("6"),
        items_over_sla_count=d("1"),
        oldest_item_age_hours=d("20.000000"),
        average_item_age_hours=d("12.000000"),
        manual_research_capacity_per_day=d("8.000000"),
    )

    assert report.queue_load_ratio == d("0.750000")
    assert report.over_sla_item_ratio == d("0.166667")
    assert report.oldest_age_sla_ratio == d("0.833333")
    assert report.average_age_sla_ratio == d("0.500000")
    assert report.queue_sla_score == d("0.541667")
    assert report.sla_status == "watch"
    assert report.manual_research_priority_status == "watch"
    assert report.report_status == "watch"
    assert report.reason_codes == (
        "queue_sla_watch",
        "oldest_age_watch",
        "over_sla_items_watch",
        "average_age_clear",
        "manual_capacity_watch",
    )


def test_over_sla_backlog_blocks_manual_research_priority() -> None:
    report = score(
        open_research_item_count=d("10"),
        items_over_sla_count=d("6"),
        oldest_item_age_hours=d("36.000000"),
        average_item_age_hours=d("30.000000"),
        manual_research_capacity_per_day=d("5.000000"),
    )

    assert report.queue_load_ratio == d("1.000000")
    assert report.uncapped_queue_load_ratio == d("2.000000")
    assert report.over_sla_item_ratio == d("0.600000")
    assert report.oldest_age_sla_ratio == d("1.000000")
    assert report.average_age_sla_ratio == d("1.000000")
    assert report.queue_sla_score == d("1.000000")
    assert report.sla_status == "block"
    assert report.manual_research_priority_status == "block"
    assert report.report_status == "block"
    assert report.reason_codes == (
        "queue_sla_block",
        "oldest_age_over_sla",
        "over_sla_items_block",
        "average_age_over_sla",
        "manual_capacity_block",
    )


def test_decimal_exact_type_validation_rejects_int_float_and_subclass_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="open_research_item_count must be exactly Decimal"):
        queue_input(open_research_item_count=1)

    with pytest.raises(ValueError, match="manual_research_capacity_per_day must be exactly Decimal"):
        queue_input(manual_research_capacity_per_day=10.0)

    with pytest.raises(ValueError, match="items_over_sla_count must be exactly Decimal"):
        queue_input(items_over_sla_count=_DecimalSubclass("1"))

    with pytest.raises(ValueError, match="oldest_item_age_hours must use six decimal places or fewer"):
        queue_input(oldest_item_age_hours=d("1.0000001"))

    with pytest.raises(ValueError, match="items_over_sla_count must not exceed open_research_item_count"):
        queue_input(open_research_item_count=d("2"), items_over_sla_count=d("3"))

    with pytest.raises(ValueError, match="score weights must sum to 1.000000"):
        module.TeamSpecialistQueueSlaScoreConfig(queue_load_weight=d("0.110000"))


def test_public_payload_rejects_leaks_and_non_public_status_words() -> None:
    module = api()
    leak = hidden_word("77616c6c6574")

    with pytest.raises(ValueError, match="unsafe public value"):
        queue_input(team_id=f"team-{leak}")

    payload = score().payload
    assert_status_vocabulary(payload)
    payload_text = json.dumps(payload, sort_keys=True)
    for hidden in (
        "7261775f63616e6469646174655f6964",
        "63616e6469646174655f6964",
        "6d61726b65745f6964",
        "6d61726b65745f736c7567",
        "7175657374696f6e",
        "736f757263655f726566",
        "75726c",
        "736f757263655f74657874",
        "64736e",
        "7461626c65",
        "746f6b656e",
        "77616c6c6574",
        "61757468",
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
        module.team_specialist_queue_sla_score_payload(tampered_payload)

    tampered_payload = dict(payload)
    tampered_payload["team_id"] = f"team-{hidden_word('7472616465')}"
    with pytest.raises(ValueError, match="unsafe public value"):
        module.team_specialist_queue_sla_score_payload(tampered_payload)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistQueueSlaScoreConfig()
    input_signal = queue_input()
    report = score()

    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_QUEUE_SLA_SCORE_CONFIG_VERSION",
        "TEAM_SPECIALIST_QUEUE_SLA_SCORE_STATUSES",
        "TeamSpecialistQueueSlaScoreConfig",
        "TeamSpecialistQueueSlaScoreInput",
        "TeamSpecialistQueueSlaScoreReport",
        "score_team_specialist_queue_sla",
        "team_specialist_queue_sla_score_payload",
    )

    for item in (config, input_signal, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]

    numeric_fields = {
        "research_sla_hours",
        "oldest_age_weight",
        "over_sla_share_weight",
        "average_age_weight",
        "queue_load_weight",
        "watch_sla_ratio",
        "block_sla_ratio",
        "over_sla_share_watch_floor",
        "over_sla_share_block_floor",
        "score_watch_floor",
        "score_block_floor",
        "open_research_item_count",
        "items_over_sla_count",
        "oldest_item_age_hours",
        "average_item_age_hours",
        "manual_research_capacity_per_day",
        "uncapped_queue_load_ratio",
        "queue_load_ratio",
        "over_sla_item_ratio",
        "oldest_age_sla_ratio",
        "average_age_sla_ratio",
        "queue_sla_score",
    }
    for cls in (
        module.TeamSpecialistQueueSlaScoreConfig,
        module.TeamSpecialistQueueSlaScoreInput,
        module.TeamSpecialistQueueSlaScoreReport,
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
        module.TeamSpecialistQueueSlaScoreConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        replace(input_signal, report_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)


def test_payload_is_deterministic_and_digest_consistent() -> None:
    module = api()
    report = score(
        open_research_item_count=d("6"),
        items_over_sla_count=d("1"),
        oldest_item_age_hours=d("20.000000"),
        average_item_age_hours=d("12.000000"),
        manual_research_capacity_per_day=d("8.000000"),
    )
    rebuilt = score(
        manual_research_capacity_per_day=d("8.000000"),
        average_item_age_hours=d("12.000000"),
        oldest_item_age_hours=d("20.000000"),
        items_over_sla_count=d("1"),
        open_research_item_count=d("6"),
    )

    payload = module.team_specialist_queue_sla_score_payload(report)
    assert payload == report.payload
    assert payload == rebuilt.payload
    assert report.derived_validation_digest == rebuilt.derived_validation_digest
    assert payload["queue_sla_score"] == "0.541667"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert_no_float_or_int_values(payload)
    json.dumps(payload, sort_keys=True)

    with pytest.raises(ValueError, match="queue_sla_score must match components"):
        replace(report, queue_sla_score=d("0.000000"))

    with pytest.raises(ValueError, match="manual_research_priority_status must match score"):
        replace(report, manual_research_priority_status="pass")

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)

    tampered_payload = dict(payload)
    tampered_payload["queue_sla_score"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest must match public payload"):
        module.team_specialist_queue_sla_score_payload(tampered_payload)


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
        "7261775f63616e6469646174655f6964",
        "63616e6469646174655f6964",
        "6d61726b65745f6964",
        "6d61726b65745f736c7567",
        "7175657374696f6e",
        "736f757263655f726566",
        "75726c",
        "736f757263655f74657874",
        "64736e",
        "7461626c65",
        "746f6b656e",
        "77616c6c6574",
        "61757468",
        "6f72646572",
        "7472616465",
        "706f736974696f6e",
        "627579",
        "73656c6c",
        "7265636f6d6d656e646174696f6e",
    ):
        assert hidden_word(hidden) not in source
