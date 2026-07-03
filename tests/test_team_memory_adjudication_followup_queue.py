from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timezone
from decimal import Decimal
from importlib import import_module
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 2, 20, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return import_module("polymarket_alpha_lab.team_memory_adjudication_followup_queue")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": module.DEFAULT_TEAM_MEMORY_ADJUDICATION_FOLLOWUP_QUEUE_CONFIG_VERSION,
        "stale_reviewer_proof_after_seconds": d("86400.000000"),
        "repeated_unresolved_family_threshold": d("2"),
    }
    values.update(overrides)
    return module.TeamMemoryAdjudicationFollowupQueueConfig(**values)


def followup_row(
    team_id: str,
    category_id: str,
    family_id: str,
    **overrides: object,
):
    module = api()
    values = {
        "team_id": team_id,
        "category_id": category_id,
        "disagreement_family_id": family_id,
        "unresolved_disagreement_count": d("0"),
        "latest_adjudicated_at": GENERATED_AT,
        "latest_reviewer_proof_at": GENERATED_AT,
        "latest_response_status": "responded",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.TeamMemoryAdjudicationFollowupRow(**values)


def report(*rows: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_team_memory_adjudication_followup_queue_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_followup_queue_summarizes_missing_stale_repeated_and_response_status() -> None:
    module = api()
    queue = report(
        followup_row(
            "politics",
            "politics",
            "family-election-rules",
            unresolved_disagreement_count=d("2"),
            latest_adjudicated_at=None,
            latest_reviewer_proof_at=None,
            latest_response_status="missing",
        ),
        followup_row(
            "crypto_btc",
            "finance.crypto.btc",
            "family-etf-flow",
            unresolved_disagreement_count=d("2"),
            latest_reviewer_proof_at=datetime(2026, 6, 30, 18, 0, tzinfo=timezone.utc),
            latest_response_status="pending",
        ),
        followup_row(
            "crypto_eth",
            "finance.crypto.eth",
            "family-etf-flow",
            unresolved_disagreement_count=d("1"),
            latest_reviewer_proof_at=datetime(2026, 7, 2, 19, 0, tzinfo=UTC),
            latest_response_status="responded",
        ),
        followup_row("sports_soccer", "sports.soccer", "family-lineups"),
    )

    assert type(queue) is module.TeamMemoryAdjudicationFollowupQueueReport
    assert is_dataclass(queue)
    assert queue.generated_at == GENERATED_AT
    assert queue.config_version == "team-memory-adjudication-followup-queue-v0"
    assert queue.response_status == "blocked"
    assert queue.source_row_count == d("4")
    assert queue.row_count == d("4")
    assert queue.missing_followup_count == d("1")
    assert queue.stale_reviewer_proof_count == d("1")
    assert queue.repeated_unresolved_family_count == d("2")
    assert queue.pending_response_count == d("1")
    assert queue.missing_response_count == d("1")
    assert queue.normal_count == d("1")
    assert queue.total_unresolved_disagreement_count == d("5")
    assert queue.missing_followup_ratio == d("0.250000")
    assert queue.stale_reviewer_proof_ratio == d("0.250000")
    assert queue.repeated_unresolved_family_ratio == d("0.500000")
    assert queue.max_reviewer_proof_age_seconds == d("180000.000000")
    assert queue.reason_codes == (
        "missing_adjudication_followup_present",
        "stale_reviewer_proof_present",
        "repeated_unresolved_disagreement_family_present",
        "pending_adjudication_response",
        "missing_adjudication_response",
        "normal_adjudication_followup_observed",
    )
    assert queue.paper_only is True
    assert queue.report_only is True
    assert queue.readonly is True

    assert tuple(row.response_status for row in queue.rows) == (
        "missing_adjudication_followup",
        "stale_reviewer_proof",
        "repeated_unresolved_disagreement_family",
        "normal_adjudication_followup",
    )
    assert queue.rows[0] == module.TeamMemoryAdjudicationFollowupQueueRow(
        team_id="politics",
        category_id="politics",
        disagreement_family_id="family-election-rules",
        response_status="missing_adjudication_followup",
        unresolved_disagreement_count=d("2"),
        latest_adjudicated_at=None,
        latest_reviewer_proof_at=None,
        reviewer_proof_age_seconds=None,
        latest_response_status="missing",
        repeated_unresolved_family_count=d("1"),
        reason_codes=(
            "missing_adjudication_followup_present",
            "missing_adjudication_response",
        ),
    )


def test_followup_queue_accepts_mapping_rows_and_reports_empty_and_normal_states() -> None:
    empty = report()
    mapped = report(
        {
            "team_id": "macro_rates",
            "category_id": "finance.macro.rates",
            "disagreement_family_id": "family-cpi-surprise",
            "unresolved_disagreement_count": d("0"),
            "latest_adjudicated_at": GENERATED_AT,
            "latest_reviewer_proof_at": GENERATED_AT,
            "latest_response_status": "responded",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )

    assert empty.response_status == "pass"
    assert empty.source_row_count == d("0")
    assert empty.rows == ()
    assert empty.reason_codes == ("no_team_memory_adjudication_followup_rows_supplied",)
    assert empty.max_reviewer_proof_age_seconds is None
    assert mapped.response_status == "pass"
    assert mapped.reason_codes == ("normal_adjudication_followup_observed",)
    assert mapped.rows[0].response_status == "normal_adjudication_followup"
    assert mapped.rows[0].reviewer_proof_age_seconds == d("0.000000")


def test_followup_queue_computes_reviewer_proof_age_from_decimal_microseconds() -> None:
    generated_at = datetime(2026, 7, 2, 20, 0, 1, 234567, tzinfo=UTC)
    queue = report(
        followup_row(
            "macro_rates",
            "finance.macro.rates",
            "family-cpi-surprise",
            latest_reviewer_proof_at=datetime(2026, 7, 2, 20, 0, 0, 1, tzinfo=UTC),
        ),
        generated_at=generated_at,
    )

    assert queue.rows[0].reviewer_proof_age_seconds == d("1.234566")
    assert queue.max_reviewer_proof_age_seconds == d("1.234566")


def test_payload_is_json_ready_and_has_no_execution_surface_language() -> None:
    payload = api().team_memory_adjudication_followup_queue_payload(
        report(
            followup_row(
                "politics",
                "politics",
                "family-election-rules",
                unresolved_disagreement_count=d("1"),
                latest_adjudicated_at=None,
                latest_reviewer_proof_at=None,
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
        "broker",
    ):
        assert forbidden not in payload_text
    assert payload["source_row_count"] == "1"
    assert payload["rows"][0]["team_id"] == "politics"
    assert payload["rows"][0]["response_status"] == "missing_adjudication_followup"
    assert payload["rows"][0]["latest_adjudicated_at"] is None


def test_followup_queue_dataclasses_are_frozen_strict_and_consistent() -> None:
    module = api()
    queue = report(
        followup_row(
            "politics",
            "politics",
            "family-election-rules",
            unresolved_disagreement_count=d("1"),
            latest_adjudicated_at=None,
            latest_reviewer_proof_at=None,
            latest_response_status="missing",
        ),
    )

    assert module.__all__ == (
        "DEFAULT_TEAM_MEMORY_ADJUDICATION_FOLLOWUP_QUEUE_CONFIG_VERSION",
        "TeamMemoryAdjudicationFollowupQueueConfig",
        "TeamMemoryAdjudicationFollowupQueueReport",
        "TeamMemoryAdjudicationFollowupQueueRow",
        "TeamMemoryAdjudicationFollowupRow",
        "build_team_memory_adjudication_followup_queue_report",
        "team_memory_adjudication_followup_queue_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    with pytest.raises(FrozenInstanceError):
        queue.response_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("team-memory-adjudication-followup-queue-v0"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=_DatetimeSubclass(2026, 7, 2, 20, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="Decimal"):
        replace(queue.rows[0], unresolved_disagreement_count=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="team_id"):
        followup_row(_StringSubclass("politics"), "politics", "family-election-rules")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(queue.rows[0], reason_codes=("normal_adjudication_followup_observed",))
    with pytest.raises(ValueError, match="row_count"):
        replace(queue, row_count=d("2"))


def test_followup_queue_rejects_wrong_inputs_duplicates_future_times_and_invalid_values() -> None:
    module = api()
    row = followup_row("politics", "politics", "family-election-rules")

    with pytest.raises(ValueError, match="TeamMemoryAdjudicationFollowupQueueConfig"):
        module.build_team_memory_adjudication_followup_queue_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="rows must be a list or tuple"):
        module.build_team_memory_adjudication_followup_queue_report(
            object(),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="TeamMemoryAdjudicationFollowupRow"):
        report(object())
    with pytest.raises(ValueError, match="unique"):
        report(row, row)
    with pytest.raises(ValueError, match="category_id"):
        followup_row("politics", "finance.crypto.btc", "family-election-rules")
    with pytest.raises(ValueError, match="disagreement_family_id"):
        followup_row("politics", "politics", " family-election-rules")
    with pytest.raises(ValueError, match="whole number"):
        followup_row(
            "politics",
            "politics",
            "family-election-rules",
            unresolved_disagreement_count=d("1.500000"),
        )
    with pytest.raises(ValueError, match="future"):
        report(
            followup_row(
                "politics",
                "politics",
                "family-election-rules",
                latest_adjudicated_at=datetime(2026, 7, 3, tzinfo=UTC),
            ),
        )
    with pytest.raises(ValueError, match="future"):
        report(
            followup_row(
                "politics",
                "politics",
                "family-election-rules",
                latest_reviewer_proof_at=datetime(2026, 7, 3, tzinfo=UTC),
            ),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        report(generated_at=datetime(2026, 7, 2, 20, 0))
    with pytest.raises(ValueError, match="datetime"):
        report(generated_at="2026-07-02T20:00:00Z")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="latest_reviewer_proof_at"):
        followup_row(
            "politics",
            "politics",
            "family-election-rules",
            latest_adjudicated_at=None,
            latest_reviewer_proof_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="report"):
        module.team_memory_adjudication_followup_queue_payload(object())


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
