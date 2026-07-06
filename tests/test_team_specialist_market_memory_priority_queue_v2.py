from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
EASTERN = timezone(timedelta(hours=-4))
MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_market_memory_priority_queue_v2.py"
)


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_market_memory_priority_queue_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def hidden_word(hex_value: str) -> str:
    return bytes.fromhex(hex_value).decode("ascii")


def input_row(
    *,
    team_id: str = "macro_rates",
    specialist_id: str = "inflation_researcher",
    market_key: str = "cpi-path",
    memory_key: str = "memory-cpi-surprise",
    observed_at: datetime = GENERATED_AT - timedelta(days=1),
    lesson_last_validated_at: datetime = GENERATED_AT - timedelta(days=5),
    market_memory_score: str = "0.800000",
    confidence_score: str = "0.750000",
    feedback_impact_score: str = "0.300000",
    public_evidence_refs: tuple[str, ...] = ("public:macro-learning-note",),
) -> Any:
    module = api()
    return module.TeamSpecialistMarketMemoryPriorityQueueV2Input(
        team_id=team_id,
        specialist_id=specialist_id,
        market_key=market_key,
        memory_key=memory_key,
        observed_at=observed_at,
        lesson_last_validated_at=lesson_last_validated_at,
        market_memory_score=d(market_memory_score),
        confidence_score=d(confidence_score),
        feedback_impact_score=d(feedback_impact_score),
        public_evidence_refs=public_evidence_refs,
    )


def build_report(*rows: Any, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_team_specialist_market_memory_priority_queue_v2(
        rows,
        config=module.TeamSpecialistMarketMemoryPriorityQueueV2Config(),
        generated_at=generated_at,
    )


def test_exports_and_hard_phase_1_flags() -> None:
    module = api()
    config = module.TeamSpecialistMarketMemoryPriorityQueueV2Config()

    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_MARKET_MEMORY_PRIORITY_QUEUE_V2_CONFIG_VERSION",
        "QUEUE_STATUSES",
        "TeamSpecialistMarketMemoryPriorityQueueV2Config",
        "TeamSpecialistMarketMemoryPriorityQueueV2Input",
        "TeamSpecialistMarketMemoryPriorityQueueV2Row",
        "TeamSpecialistMarketMemoryPriorityQueueV2Report",
        "build_team_specialist_market_memory_priority_queue_v2",
        "team_specialist_market_memory_priority_queue_v2_payload",
    )
    assert config.config_version == "team-specialist-market-memory-priority-queue-v2-phase-1"
    assert config.market_memory_weight == d("0.400000")
    assert config.confidence_weight == d("0.200000")
    assert config.feedback_impact_weight == d("0.300000")
    assert config.freshness_weight == d("0.100000")
    assert config.stale_lesson_penalty_weight == d("0.200000")
    assert config.max_lesson_age_days == d("30.000000")
    assert config.watch_priority_score == d("0.300000")
    assert config.urgent_priority_score == d("0.700000")
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistMarketMemoryPriorityQueueV2Config(paper_only=False)


def test_market_memory_priority_orders_highest_priority_first() -> None:
    report = build_report(
        input_row(
            team_id="macro_rates",
            specialist_id="inflation_researcher",
            market_key="cpi-path",
            memory_key="memory-cpi-surprise",
            lesson_last_validated_at=GENERATED_AT - timedelta(days=3),
            market_memory_score="0.900000",
            confidence_score="0.850000",
            feedback_impact_score="0.800000",
            public_evidence_refs=("public:macro-learning-note",),
        ),
        input_row(
            team_id="weather_energy",
            specialist_id="grid_forecaster",
            market_key="grid-load",
            memory_key="memory-heat-load",
            lesson_last_validated_at=GENERATED_AT - timedelta(days=5),
            market_memory_score="0.600000",
            confidence_score="0.600000",
            feedback_impact_score="0.300000",
            public_evidence_refs=("memory:grid-load-review",),
        ),
        input_row(
            team_id="macro_rates",
            specialist_id="labor_researcher",
            market_key="jobs-path",
            memory_key="memory-jobs-revision",
            lesson_last_validated_at=GENERATED_AT - timedelta(days=20),
            market_memory_score="0.500000",
            confidence_score="0.500000",
            feedback_impact_score="0.100000",
            public_evidence_refs=("lesson:jobs-revision-retro",),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.item_count == d("3")
    assert report.urgent_count == d("1")
    assert report.watch_count == d("1")
    assert report.clear_count == d("1")
    assert report.average_priority_score == d("0.523333")
    assert report.top_priority_score == d("0.840000")
    assert report.status == "urgent"
    assert report.reason_codes == (
        "market_memory_priority_urgent",
        "feedback_impact_boost",
        "stale_lesson_penalty",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    assert tuple(row.memory_key for row in report.priority_rows) == (
        "memory-cpi-surprise",
        "memory-heat-load",
        "memory-jobs-revision",
    )
    assert tuple(row.queue_rank for row in report.priority_rows) == (
        d("1"),
        d("2"),
        d("3"),
    )
    assert report.priority_rows[0].priority_score == d("0.840000")
    assert report.priority_rows[0].queue_status == "urgent"
    assert report.priority_rows[0].freshness_score == d("0.900000")
    assert report.priority_rows[0].stale_lesson_penalty == d("0.100000")
    assert report.priority_rows[0].reason_codes == (
        "market_memory_priority_urgent",
        "memory_signal_strong",
        "confidence_signal_strong",
        "feedback_impact_boost",
    )
    assert report.priority_rows[2].priority_score == d("0.230000")
    assert report.priority_rows[2].queue_status == "clear"
    assert "stale_lesson_penalty" in report.priority_rows[2].reason_codes


def test_stale_lesson_penalty_lowers_priority_for_equal_memory() -> None:
    report = build_report(
        input_row(
            team_id="macro_rates",
            specialist_id="fresh_specialist",
            market_key="fresh-market",
            memory_key="memory-fresh",
            lesson_last_validated_at=GENERATED_AT - timedelta(days=1),
            market_memory_score="0.700000",
            confidence_score="0.700000",
            feedback_impact_score="0.400000",
        ),
        input_row(
            team_id="macro_rates",
            specialist_id="stale_specialist",
            market_key="stale-market",
            memory_key="memory-stale",
            lesson_last_validated_at=GENERATED_AT - timedelta(days=45),
            market_memory_score="0.700000",
            confidence_score="0.700000",
            feedback_impact_score="0.400000",
            public_evidence_refs=("public:stale-memory-note",),
        ),
    )

    fresh, stale = report.priority_rows
    assert fresh.memory_key == "memory-fresh"
    assert stale.memory_key == "memory-stale"
    assert fresh.stale_lesson_penalty == d("0.033333")
    assert stale.stale_lesson_penalty == d("1.000000")
    assert fresh.priority_score == d("0.630000")
    assert stale.priority_score == d("0.340000")
    assert fresh.priority_score > stale.priority_score


def test_high_impact_feedback_boosts_priority_for_equal_memory() -> None:
    report = build_report(
        input_row(
            team_id="macro_rates",
            specialist_id="boosted_specialist",
            market_key="boosted-market",
            memory_key="memory-boosted",
            market_memory_score="0.500000",
            confidence_score="0.500000",
            feedback_impact_score="0.900000",
            public_evidence_refs=("public:boosted-feedback",),
        ),
        input_row(
            team_id="macro_rates",
            specialist_id="quiet_specialist",
            market_key="quiet-market",
            memory_key="memory-quiet",
            market_memory_score="0.500000",
            confidence_score="0.500000",
            feedback_impact_score="0.100000",
            public_evidence_refs=("public:quiet-feedback",),
        ),
    )

    boosted, quiet = report.priority_rows
    assert boosted.memory_key == "memory-boosted"
    assert quiet.memory_key == "memory-quiet"
    assert boosted.feedback_impact_score == d("0.900000")
    assert quiet.feedback_impact_score == d("0.100000")
    assert boosted.priority_score == d("0.620000")
    assert quiet.priority_score == d("0.380000")
    assert boosted.priority_score > quiet.priority_score
    assert "feedback_impact_boost" in boosted.reason_codes
    assert "feedback_impact_boost" not in quiet.reason_codes


def test_payload_serializes_decimal_values_as_strings() -> None:
    module = api()
    report = build_report(input_row(), generated_at=datetime(2026, 7, 6, 8, 0, tzinfo=EASTERN))

    payload = module.team_specialist_market_memory_priority_queue_v2_payload(report)
    payload_text = repr(payload).lower()

    assert report.generated_at == GENERATED_AT
    assert payload["item_count"] == "1"
    assert payload["average_priority_score"] == "0.610000"
    assert payload["priority_rows"][0]["queue_rank"] == "1"
    assert payload["priority_rows"][0]["priority_score"] == "0.610000"
    assert payload["priority_rows"][0]["lesson_age_days"] == "5.000000"
    assert payload["priority_rows"][0]["derived_validation_digest"] == (
        report.priority_rows[0].derived_validation_digest
    )
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert "decimal" not in payload_text
    json.dumps(payload)
    assert report.payload == payload


def test_empty_report_uses_decimal_zeroes_and_hard_flags() -> None:
    report = build_report()

    assert report.item_count == d("0")
    assert report.urgent_count == d("0")
    assert report.watch_count == d("0")
    assert report.clear_count == d("0")
    assert report.average_priority_score == d("0.000000")
    assert report.top_priority_score == d("0.000000")
    assert report.status == "clear"
    assert report.reason_codes == ("market_memory_priority_empty",)
    assert report.priority_rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_decimal_datetime_frozen_and_digest_tamper_validations() -> None:
    module = api()

    with pytest.raises(ValueError, match="market_memory_score must be a Decimal"):
        module.TeamSpecialistMarketMemoryPriorityQueueV2Input(
            team_id="macro_rates",
            specialist_id="inflation_researcher",
            market_key="cpi-path",
            memory_key="memory-cpi-surprise",
            observed_at=GENERATED_AT,
            lesson_last_validated_at=GENERATED_AT,
            market_memory_score=0.5,
            confidence_score=d("0.750000"),
            feedback_impact_score=d("0.300000"),
            public_evidence_refs=("public:macro-learning-note",),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(input_row(), generated_at=datetime(2026, 7, 6, 12, 0))

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        input_row(observed_at=datetime(2026, 7, 6, 12, 0))

    with pytest.raises(ValueError, match="observed_at must be on or before generated_at"):
        build_report(input_row(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="lesson_last_validated_at must be on or before generated_at"):
        build_report(input_row(lesson_last_validated_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="public_evidence_refs must not be empty"):
        input_row(public_evidence_refs=())

    with pytest.raises(FrozenInstanceError):
        input_row().market_memory_score = d("0.100000")  # type: ignore[misc]

    report = build_report(input_row())
    with pytest.raises(FrozenInstanceError):
        report.status = "clear"  # type: ignore[misc]

    with pytest.raises(ValueError, match="derived_validation_digest must match row fields"):
        replace(report.priority_rows[0], priority_score=d("0.123456"))

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, average_priority_score=d("0.123456"))


def test_unsafe_public_key_and_value_payload_rejection() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public value"):
        input_row(team_id=f"macro_{hidden_word('77616c6c6574')}")

    with pytest.raises(ValueError, match="unsafe public value"):
        input_row(public_evidence_refs=(f"public:{hidden_word('627579')}-path",))

    report = build_report(input_row())
    payload = module.team_specialist_market_memory_priority_queue_v2_payload(report)
    payload[f"public_{hidden_word('61757468')}"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_public_payload("external payload", payload)

    payload = module.team_specialist_market_memory_priority_queue_v2_payload(report)
    payload["public_marker"] = f"contains-{hidden_word('7472616465')}"
    with pytest.raises(ValueError, match="unsafe public value"):
        module._reject_public_payload("external payload", payload)


def test_source_scope_has_no_unsafe_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
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
        "send",
        "post(",
        "put(",
        "delete(",
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    ):
        assert forbidden not in lowered
