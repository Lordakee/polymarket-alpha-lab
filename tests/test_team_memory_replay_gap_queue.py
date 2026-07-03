from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timezone
from decimal import Decimal
from importlib import import_module
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 2, 19, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return import_module("polymarket_alpha_lab.team_memory_replay_gap_queue")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": module.DEFAULT_TEAM_MEMORY_REPLAY_GAP_QUEUE_CONFIG_VERSION,
        "stale_replay_after_seconds": d("86400.000000"),
        "unresolved_learning_pressure_threshold": d("2"),
    }
    values.update(overrides)
    return module.TeamMemoryReplayGapQueueConfig(**values)


def replay_row(team_id: str, category_id: str, **overrides: object):
    module = api()
    values = {
        "team_id": team_id,
        "category_id": category_id,
        "latest_replay_validated_at": GENERATED_AT,
        "latest_replay_coverage_ratio": d("1.000000"),
        "unresolved_postmortem_learning_count": d("0"),
        "latest_response_status": "responded",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.TeamMemoryReplayGapRow(**values)


def report(*rows: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_team_memory_replay_gap_queue_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_replay_gap_queue_identifies_missing_stale_learning_and_response_gaps() -> None:
    module = api()
    queue = report(
        replay_row(
            "politics",
            "politics",
            latest_replay_validated_at=None,
            latest_replay_coverage_ratio=d("0.000000"),
            latest_response_status="missing",
        ),
        replay_row(
            "crypto_btc",
            "finance.crypto.btc",
            latest_replay_validated_at=datetime(
                2026,
                6,
                30,
                18,
                0,
                tzinfo=timezone.utc,
            ),
            latest_replay_coverage_ratio=d("0.900000"),
            latest_response_status="responded",
        ),
        replay_row(
            "macro_rates",
            "finance.macro.rates",
            unresolved_postmortem_learning_count=d("3"),
            latest_response_status="pending",
        ),
        replay_row("sports_soccer", "sports.soccer"),
    )

    assert type(queue) is module.TeamMemoryReplayGapQueueReport
    assert is_dataclass(queue)
    assert queue.generated_at == GENERATED_AT
    assert queue.config_version == "team-memory-replay-gap-queue-v0"
    assert queue.response_status == "blocked"
    assert queue.source_row_count == d("4")
    assert queue.row_count == d("4")
    assert queue.missing_replay_validation_count == d("1")
    assert queue.stale_replay_coverage_count == d("1")
    assert queue.unresolved_postmortem_learning_count == d("1")
    assert queue.pending_response_count == d("1")
    assert queue.missing_response_count == d("1")
    assert queue.normal_count == d("1")
    assert queue.max_replay_age_seconds == d("176400.000000")
    assert queue.max_unresolved_postmortem_learning_count == d("3")
    assert queue.reason_codes == (
        "missing_replay_validation",
        "stale_replay_coverage",
        "unresolved_postmortem_learnings",
        "pending_replay_response",
        "missing_replay_response",
        "normal_replay_coverage_observed",
    )
    assert queue.paper_only is True
    assert queue.report_only is True
    assert queue.readonly is True

    assert tuple(row.response_status for row in queue.rows) == (
        "missing_replay_validation",
        "stale_replay_coverage",
        "unresolved_postmortem_learnings",
        "normal_replay_coverage",
    )
    assert queue.rows[0] == module.TeamMemoryReplayGapQueueRow(
        team_id="politics",
        category_id="politics",
        response_status="missing_replay_validation",
        latest_replay_validated_at=None,
        replay_age_seconds=None,
        latest_replay_coverage_ratio=d("0.000000"),
        unresolved_postmortem_learning_count=d("0"),
        latest_response_status="missing",
        reason_codes=("missing_replay_validation", "missing_replay_response"),
    )


def test_gap_queue_accepts_mapping_rows_and_reports_empty_and_normal_states() -> None:
    empty = report()
    mapped = report(
        {
            "team_id": "crypto_eth",
            "category_id": "finance.crypto.eth",
            "latest_replay_validated_at": GENERATED_AT,
            "latest_replay_coverage_ratio": d("1.000000"),
            "unresolved_postmortem_learning_count": d("0"),
            "latest_response_status": "responded",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )

    assert empty.response_status == "pass"
    assert empty.source_row_count == d("0")
    assert empty.rows == ()
    assert empty.reason_codes == ("no_team_memory_replay_rows_supplied",)
    assert empty.max_replay_age_seconds is None
    assert mapped.response_status == "pass"
    assert mapped.reason_codes == ("normal_replay_coverage_observed",)
    assert mapped.rows[0].response_status == "normal_replay_coverage"
    assert mapped.rows[0].replay_age_seconds == d("0.000000")


def test_replay_gap_queue_computes_replay_age_from_decimal_microseconds() -> None:
    generated_at = datetime(2026, 7, 2, 19, 0, 1, 234567, tzinfo=UTC)
    queue = report(
        replay_row(
            "crypto_eth",
            "finance.crypto.eth",
            latest_replay_validated_at=datetime(2026, 7, 2, 19, 0, 0, 1, tzinfo=UTC),
        ),
        generated_at=generated_at,
    )

    assert queue.rows[0].replay_age_seconds == d("1.234566")
    assert queue.max_replay_age_seconds == d("1.234566")


def test_payload_is_json_ready_and_has_no_execution_surface_language() -> None:
    payload = api().team_memory_replay_gap_queue_payload(
        report(
            replay_row(
                "politics",
                "politics",
                latest_replay_validated_at=None,
                latest_replay_coverage_ratio=d("0.000000"),
                latest_response_status="missing",
            ),
        ),
    )

    payload_text = repr(payload).lower()
    for forbidden in (
        "market_slug",
        "question",
        "payload_json",
        "recommend",
        "wallet",
        "account",
        "order",
        "trade",
        "advice",
        "auth",
    ):
        assert forbidden not in payload_text
    assert payload["source_row_count"] == "1"
    assert payload["rows"][0]["team_id"] == "politics"
    assert payload["rows"][0]["response_status"] == "missing_replay_validation"
    assert payload["rows"][0]["latest_replay_validated_at"] is None


def test_replay_gap_queue_dataclasses_are_frozen_strict_and_consistent() -> None:
    module = api()
    queue = report(
        replay_row(
            "politics",
            "politics",
            latest_replay_validated_at=None,
            latest_replay_coverage_ratio=d("0.000000"),
            latest_response_status="missing",
        ),
    )

    assert module.__all__ == (
        "DEFAULT_TEAM_MEMORY_REPLAY_GAP_QUEUE_CONFIG_VERSION",
        "TeamMemoryReplayGapQueueConfig",
        "TeamMemoryReplayGapQueueReport",
        "TeamMemoryReplayGapQueueRow",
        "TeamMemoryReplayGapRow",
        "build_team_memory_replay_gap_queue_report",
        "team_memory_replay_gap_queue_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    with pytest.raises(FrozenInstanceError):
        queue.response_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("team-memory-replay-gap-queue-v0"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=_DatetimeSubclass(2026, 7, 2, 19, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="Decimal"):
        replace(queue.rows[0], latest_replay_coverage_ratio=_DecimalSubclass("0.1"))
    with pytest.raises(ValueError, match="team_id"):
        replay_row(_StringSubclass("politics"), "politics")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(queue.rows[0], reason_codes=("normal_replay_coverage_observed",))
    with pytest.raises(ValueError, match="row_count"):
        replace(queue, row_count=d("2"))


def test_replay_gap_queue_rejects_wrong_inputs_duplicates_and_invalid_values() -> None:
    module = api()
    row = replay_row("politics", "politics")

    with pytest.raises(ValueError, match="TeamMemoryReplayGapQueueConfig"):
        module.build_team_memory_replay_gap_queue_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="rows must be a list or tuple"):
        module.build_team_memory_replay_gap_queue_report(
            object(),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="TeamMemoryReplayGapRow"):
        report(object())
    with pytest.raises(ValueError, match="unique"):
        report(row, row)
    with pytest.raises(ValueError, match="category_id"):
        replay_row("politics", "finance.crypto.btc")
    with pytest.raises(ValueError, match="at most"):
        replay_row(
            "politics",
            "politics",
            latest_replay_coverage_ratio=d("1.100000"),
        )
    with pytest.raises(ValueError, match="whole number"):
        replay_row(
            "politics",
            "politics",
            unresolved_postmortem_learning_count=d("1.500000"),
        )
    with pytest.raises(ValueError, match="future"):
        report(
            replay_row(
                "politics",
                "politics",
                latest_replay_validated_at=datetime(2026, 7, 3, tzinfo=UTC),
            ),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        report(generated_at=datetime(2026, 7, 2, 19, 0))
    with pytest.raises(ValueError, match="datetime"):
        report(generated_at="2026-07-02T19:00:00Z")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="report"):
        module.team_memory_replay_gap_queue_payload(object())


def test_module_scope_has_no_persistence_or_execution_surface() -> None:
    module = api()
    source = Path(module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_calls = {
        "open",
        "connect",
        "requests",
        "post",
        "put",
        "delete",
        "total_seconds",
        "submit_order",
        "cancel_order",
        "place_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name):
                assert target.id not in forbidden_calls
            if isinstance(target, ast.Attribute):
                assert target.attr not in forbidden_calls

    lowered = source.lower()
    for forbidden in (
        "decimal(str(",
        "value: float",
        "private_key",
        "wallet",
        "account",
        "auth",
        "broker",
        "live trading",
        "submit_order",
        "cancel_order",
        "place_order",
        "investment advice",
        "trade instruction",
    ):
        assert forbidden not in lowered
