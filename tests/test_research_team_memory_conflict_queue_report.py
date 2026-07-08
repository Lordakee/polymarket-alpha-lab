from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(hours=2)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_team_memory_conflict_queue_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_memory_conflict_queue_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_TEAM_MEMORY_CONFLICT_QUEUE_REPORT_CONFIG_VERSION
        ),
        "watch_contradictory_lesson_count": d("1"),
        "block_contradictory_lesson_count": d("3"),
        "watch_stale_calibration_count": d("1"),
        "block_stale_calibration_count": d("3"),
        "watch_unresolved_review_note_count": d("1"),
        "block_unresolved_review_note_count": d("2"),
        "watch_domain_escalation_fit_score": d("0.500000"),
        "block_domain_escalation_fit_score": d("0.850000"),
        "watch_queue_age_hours": d("24.000000"),
        "block_queue_age_hours": d("72.000000"),
        "watch_queue_urgency_score": d("0.350000"),
        "block_queue_urgency_score": d("0.750000"),
    }
    values.update(overrides)
    return module.ResearchTeamMemoryConflictQueueConfig(**values)


def memory_conflict(**overrides: object):
    module = api()
    values = {
        "specialist_key": "macro_rates",
        "aggregate_label": "baseline_memory",
        "contradictory_lesson_count": d("0"),
        "stale_calibration_count": d("0"),
        "unresolved_review_note_count": d("0"),
        "domain_escalation_fit_score": d("0.100000"),
        "queue_age_hours": d("6.000000"),
        "observed_at": OBSERVED_AT,
    }
    values.update(overrides)
    return module.ResearchTeamMemoryConflictQueueInput(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_memory_conflict_queue_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def payload_keys(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            keys.append(str(key))
            keys.extend(payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(payload_keys(item))
        return tuple(keys)
    return ()


def test_conflict_queue_scores_pass_watch_and_block_aggregate_memory() -> None:
    result = build_report(
        memory_conflict(
            specialist_key="macro_rates",
            aggregate_label="review_memory",
            contradictory_lesson_count=d("4"),
            stale_calibration_count=d("3"),
            unresolved_review_note_count=d("2"),
            domain_escalation_fit_score=d("0.900000"),
            queue_age_hours=d("80.000000"),
        ),
        memory_conflict(
            specialist_key="sports_soccer",
            aggregate_label="calibration_memory",
            contradictory_lesson_count=d("1"),
            stale_calibration_count=d("1"),
            unresolved_review_note_count=d("1"),
            domain_escalation_fit_score=d("0.550000"),
            queue_age_hours=d("30.000000"),
        ),
        memory_conflict(
            specialist_key="crypto_research",
            aggregate_label="stable_memory",
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "research-team-memory-conflict-queue-report-v0"
    assert result.memory_conflict_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.contradictory_lesson_total == d("5")
    assert result.stale_calibration_total == d("4")
    assert result.unresolved_review_note_total == d("3")
    assert result.domain_escalation_fit_count == d("2")
    assert result.max_queue_urgency_score == d("1.000000")
    assert result.oldest_queue_age_hours == d("80.000000")
    assert result.status == "block"
    assert result.paper_queue_action == "paper_memory_conflict_queue_block"
    assert result.reason_codes == (
        "memory_conflict_queue_block",
        "contradictory_lessons_block",
        "stale_calibrations_block",
        "unresolved_review_notes_block",
        "domain_escalation_fit_block",
        "queue_age_block",
        "queue_urgency_block",
        "contradictory_lessons_watch",
        "stale_calibrations_watch",
        "unresolved_review_notes_watch",
        "domain_escalation_fit_watch",
        "queue_age_watch",
        "queue_urgency_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64

    blocked, watched, passed = result.rows
    assert tuple(row.conflict_status for row in result.rows) == ("block", "watch", "pass")

    assert blocked.specialist_key == "macro_rates"
    assert blocked.aggregate_label == "review_memory"
    assert blocked.queue_urgency_score == d("1.000000")
    assert blocked.reason_codes == (
        "contradictory_lessons_block",
        "stale_calibrations_block",
        "unresolved_review_notes_block",
        "domain_escalation_fit_block",
        "queue_age_block",
        "queue_urgency_block",
    )

    assert watched.specialist_key == "sports_soccer"
    assert watched.queue_urgency_score == d("0.550000")
    assert watched.reason_codes == (
        "contradictory_lessons_watch",
        "stale_calibrations_watch",
        "unresolved_review_notes_watch",
        "domain_escalation_fit_watch",
        "queue_age_watch",
        "queue_urgency_watch",
    )

    assert passed.specialist_key == "crypto_research"
    assert passed.queue_urgency_score == d("0.100000")
    assert passed.reason_codes == ("memory_conflict_queue_clear",)

    assert result.reason_code_counts[0].reason_code == "memory_conflict_queue_clear"
    assert result.reason_code_counts[0].count == d("1")
    assert result.reason_code_counts[0].memory_conflict_ratio == d("0.333333")


def test_empty_queue_is_pass_with_decimal_counts_and_flags() -> None:
    result = build_report()

    assert result.memory_conflict_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.contradictory_lesson_total == d("0")
    assert result.stale_calibration_total == d("0")
    assert result.unresolved_review_note_total == d("0")
    assert result.domain_escalation_fit_count == d("0")
    assert result.max_queue_urgency_score == d("0.000000")
    assert result.oldest_queue_age_hours == d("0.000000")
    assert result.status == "pass"
    assert result.paper_queue_action == "paper_memory_conflict_queue_monitor"
    assert result.reason_codes == ("memory_conflict_queue_empty",)
    assert result.reason_code_counts == ()
    assert result.rows == ()

    populated = build_report(memory_conflict())
    for value in (result, populated, *populated.rows, *populated.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item.name.endswith(("_count", "_total", "_score", "_hours", "_ratio")):
                assert type(item_value) is Decimal


def test_payload_is_deterministic_decimal_only_public_safe_and_digest_checked() -> None:
    module = api()
    first = build_report(
        memory_conflict(
            specialist_key="macro_rates",
            aggregate_label="review_memory",
            contradictory_lesson_count=d("4"),
            stale_calibration_count=d("3"),
            unresolved_review_note_count=d("2"),
            domain_escalation_fit_score=d("0.900000"),
            queue_age_hours=d("80.000000"),
            observed_at=datetime(
                2026,
                7,
                8,
                4,
                30,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        memory_conflict(
            specialist_key="sports_soccer",
            aggregate_label="calibration_memory",
            contradictory_lesson_count=d("1"),
            stale_calibration_count=d("1"),
            unresolved_review_note_count=d("1"),
            domain_escalation_fit_score=d("0.550000"),
            queue_age_hours=d("30.000000"),
        ),
        generated_at=datetime(
            2026,
            7,
            8,
            5,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )
    second = build_report(
        memory_conflict(
            specialist_key="sports_soccer",
            aggregate_label="calibration_memory",
            contradictory_lesson_count=d("1"),
            stale_calibration_count=d("1"),
            unresolved_review_note_count=d("1"),
            domain_escalation_fit_score=d("0.550000"),
            queue_age_hours=d("30.000000"),
        ),
        memory_conflict(
            specialist_key="macro_rates",
            aggregate_label="review_memory",
            contradictory_lesson_count=d("4"),
            stale_calibration_count=d("3"),
            unresolved_review_note_count=d("2"),
            domain_escalation_fit_score=d("0.900000"),
            queue_age_hours=d("80.000000"),
            observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=UTC),
        ),
    )

    payload = module.research_team_memory_conflict_queue_report_payload(first)
    repeat_payload = module.research_team_memory_conflict_queue_report_payload(second)

    assert first.generated_at == GENERATED_AT
    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload == repeat_payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["memory_conflict_count"] == "2"
    assert payload["rows"][0]["queue_urgency_score"] == "1.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-08T11:30:00+00:00"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert_no_int_or_float_values(payload)
    json.dumps(payload, sort_keys=True)

    unsafe_fragments = (
        "event",
        "market",
        "source",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "database",
        "network",
    )
    assert not any(
        fragment in key.lower()
        for key in payload_keys(payload)
        for fragment in unsafe_fragments
    )
    payload_text = repr(payload).lower()
    assert not any(fragment in payload_text for fragment in unsafe_fragments)

    tampered = dict(payload)
    tampered["pass_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_memory_conflict_queue_report_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, pass_count=d("2"))


def test_rejects_unsafe_labels_bad_types_flags_times_and_manual_tampering() -> None:
    module = api()
    result = build_report(
        memory_conflict(
            specialist_key="macro_rates",
            contradictory_lesson_count=d("4"),
        ),
        memory_conflict(specialist_key="crypto_research"),
    )
    row = result.rows[0]
    payload = module.research_team_memory_conflict_queue_report_payload(result)

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.conflict_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="Decimal"):
        memory_conflict(contradictory_lesson_count=1)
    with pytest.raises(ValueError, match="Decimal"):
        memory_conflict(domain_escalation_fit_score=0.5)
    with pytest.raises(ValueError, match="Decimal"):
        memory_conflict(queue_age_hours=_DecimalSubclass("30.000000"))
    with pytest.raises(ValueError, match="integral"):
        memory_conflict(stale_calibration_count=d("1.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(memory_conflict(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        memory_conflict(observed_at=datetime(2026, 7, 8, 11, 45))
    with pytest.raises(ValueError, match="observed_at"):
        memory_conflict(
            observed_at=_DatetimeSubclass(2026, 7, 8, 11, 45, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="future"):
        build_report(memory_conflict(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique"):
        build_report(memory_conflict(), memory_conflict())
    with pytest.raises(ValueError, match="specialist_key"):
        memory_conflict(specialist_key="market_source")
    with pytest.raises(ValueError, match="aggregate_label"):
        memory_conflict(aggregate_label="wallet_note")
    with pytest.raises(ValueError, match="paper_only"):
        memory_conflict(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_report(memory_conflict(), cfg=object())
    with pytest.raises(ValueError, match="conflict_status"):
        replace(row, conflict_status="pass")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, pass_count=d("2"))
    with pytest.raises(ValueError, match="rows"):
        replace(result, rows=tuple(reversed(result.rows)))

    unsafe = dict(payload)
    unsafe["source_reference"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_team_memory_conflict_queue_report_payload(unsafe)

    numeric = dict(payload)
    numeric["memory_conflict_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        module.research_team_memory_conflict_queue_report_payload(numeric)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.research_team_memory_conflict_queue_report_payload(downgraded)


def test_module_is_report_only_without_external_write_or_execution_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    banned_import_roots = {
        "http",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "urllib",
        "web3",
    }
    banned_call_names = {
        "buy",
        "connect",
        "delete",
        "execute",
        "executemany",
        "get",
        "open",
        "order",
        "patch",
        "post",
        "put",
        "request",
        "sell",
        "send",
        "submit",
        "trade",
        "write",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in banned_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in banned_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in banned_call_names
