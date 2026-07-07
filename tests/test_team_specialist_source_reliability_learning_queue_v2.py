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
    / "team_specialist_source_reliability_learning_queue_v2.py"
)


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_source_reliability_learning_queue_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def hidden_word(hex_value: str) -> str:
    return bytes.fromhex(hex_value).decode("ascii")


def input_row(
    *,
    team_id: str = "macro_rates",
    specialist_id: str = "inflation_researcher",
    source_id: str = "source-cpi-agency",
    source_family: str = "public_release",
    observed_at: datetime = GENERATED_AT - timedelta(days=1),
    reliability_last_reviewed_at: datetime = GENERATED_AT - timedelta(days=2),
    reliability_score: str = "0.950000",
    sample_count: str = "8",
    calibration_feedback_count: str = "0",
    public_source_refs: tuple[str, ...] = ("source:cpi-public-release",),
) -> Any:
    module = api()
    return module.TeamSpecialistSourceReliabilityLearningQueueInputV2(
        team_id=team_id,
        specialist_id=specialist_id,
        source_id=source_id,
        source_family=source_family,
        observed_at=observed_at,
        reliability_last_reviewed_at=reliability_last_reviewed_at,
        reliability_score=d(reliability_score),
        sample_count=d(sample_count),
        calibration_feedback_count=d(calibration_feedback_count),
        public_source_refs=public_source_refs,
    )


def build_report(*rows: Any, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_team_specialist_source_reliability_learning_queue_v2(
        rows,
        config=module.TeamSpecialistSourceReliabilityLearningQueueV2Config(),
        generated_at=generated_at,
    )


def test_exports_and_default_config_are_phase_1_readonly_contract() -> None:
    module = api()
    config = module.TeamSpecialistSourceReliabilityLearningQueueV2Config()

    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_SOURCE_RELIABILITY_LEARNING_QUEUE_V2_CONFIG_VERSION",
        "TEAM_SPECIALIST_SOURCE_RELIABILITY_LEARNING_QUEUE_V2_STATUSES",
        "TeamSpecialistSourceReliabilityLearningQueueV2Config",
        "TeamSpecialistSourceReliabilityLearningQueueInputV2",
        "TeamSpecialistSourceReliabilityLearningQueueItemV2",
        "TeamSpecialistSourceReliabilityLearningQueueReportV2",
        "build_team_specialist_source_reliability_learning_queue_v2",
        "team_specialist_source_reliability_learning_queue_v2_payload",
    )
    assert config.config_version == (
        "team-specialist-source-reliability-learning-queue-v2-phase-1"
    )
    assert config.low_reliability_weight == d("0.450000")
    assert config.stale_reliability_weight == d("0.250000")
    assert config.calibration_feedback_weight == d("0.200000")
    assert config.sample_size_weight == d("0.100000")
    assert config.stale_review_threshold_seconds == d("604800.000000")
    assert config.max_stale_review_seconds == d("2419200.000000")
    assert config.min_sample_count == d("5")
    assert config.calibration_feedback_boost_count == d("3")
    assert config.watch_priority_score == d("0.250000")
    assert config.critical_priority_score == d("0.650000")
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistSourceReliabilityLearningQueueV2Config(paper_only=False)


def test_source_reliability_learning_priority_orders_weakest_sources_first() -> None:
    report = build_report(
        input_row(
            source_id="source-cpi-agency",
            reliability_last_reviewed_at=GENERATED_AT - timedelta(days=35),
            reliability_score="0.200000",
            sample_count="2",
            calibration_feedback_count="3",
            public_source_refs=("source:cpi-public-release",),
        ),
        input_row(
            team_id="weather_energy",
            specialist_id="grid_forecaster",
            source_id="source-grid-load",
            source_family="system_report",
            reliability_last_reviewed_at=GENERATED_AT - timedelta(days=2),
            reliability_score="0.950000",
            sample_count="8",
            calibration_feedback_count="0",
            public_source_refs=("public:grid-load-summary",),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.team_count == d("2")
    assert report.specialist_team_count == d("2")
    assert report.source_count == d("2")
    assert report.observation_count == d("2")
    assert report.critical_count == d("1")
    assert report.watch_count == d("0")
    assert report.clear_count == d("1")
    assert report.average_priority_score == d("0.446250")
    assert report.status == "critical"
    assert report.reason_codes == (
        "source_reliability_learning_queue_critical",
        "low_source_reliability",
        "stale_source_reliability",
        "calibration_feedback_boost",
        "low_reliability_sample_size",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    assert tuple(item.source_id for item in report.queue_items) == (
        "source-cpi-agency",
        "source-grid-load",
    )
    first = report.queue_items[0]
    assert first.priority_score == d("0.870000")
    assert first.queue_status == "critical"
    assert first.low_reliability_component == d("0.800000")
    assert first.stale_reliability_component == d("1.000000")
    assert first.calibration_feedback_component == d("1.000000")
    assert first.sample_size_gap == d("0.600000")
    assert first.reason_codes == (
        "low_source_reliability",
        "stale_source_reliability",
        "calibration_feedback_boost",
        "low_reliability_sample_size",
    )
    assert len(first.derived_validation_digest) == 64

    second = report.queue_items[1]
    assert second.priority_score == d("0.022500")
    assert second.queue_status == "clear"
    assert second.reason_codes == ("source_reliability_learning_clear",)


def test_stale_reliability_review_penalty_lifts_priority() -> None:
    report = build_report(
        input_row(
            source_id="source-fresh-review",
            reliability_score="0.900000",
            reliability_last_reviewed_at=GENERATED_AT - timedelta(days=2),
            public_source_refs=("reliability:fresh-review",),
        ),
        input_row(
            source_id="source-stale-review",
            reliability_score="0.900000",
            reliability_last_reviewed_at=GENERATED_AT - timedelta(days=35),
            public_source_refs=("reliability:stale-review",),
        ),
    )

    stale, fresh = report.queue_items
    assert stale.source_id == "source-stale-review"
    assert stale.stale_reliability_component == d("1.000000")
    assert stale.priority_score == d("0.295000")
    assert stale.queue_status == "watch"
    assert "stale_source_reliability" in stale.reason_codes

    assert fresh.source_id == "source-fresh-review"
    assert fresh.stale_reliability_component == d("0.000000")
    assert fresh.priority_score == d("0.045000")
    assert fresh.queue_status == "clear"


def test_calibration_feedback_boost_lifts_priority() -> None:
    report = build_report(
        input_row(
            source_id="source-no-feedback",
            reliability_score="0.700000",
            calibration_feedback_count="0",
            public_source_refs=("calibration:no-feedback",),
        ),
        input_row(
            source_id="source-feedback",
            reliability_score="0.700000",
            calibration_feedback_count="3",
            public_source_refs=("calibration:feedback-review",),
        ),
    )

    boosted, baseline = report.queue_items
    assert boosted.source_id == "source-feedback"
    assert boosted.calibration_feedback_component == d("1.000000")
    assert boosted.priority_score == d("0.335000")
    assert boosted.queue_status == "watch"
    assert "calibration_feedback_boost" in boosted.reason_codes

    assert baseline.source_id == "source-no-feedback"
    assert baseline.calibration_feedback_component == d("0.000000")
    assert baseline.priority_score == d("0.135000")
    assert baseline.queue_status == "clear"


def test_serialization_uses_decimal_strings_and_tuple_collections() -> None:
    report = build_report(
        input_row(
            source_id="source-cpi-agency",
            reliability_score="0.200000",
            reliability_last_reviewed_at=GENERATED_AT - timedelta(days=35),
            sample_count="2",
            calibration_feedback_count="3",
        ),
    )

    payload = api().team_specialist_source_reliability_learning_queue_v2_payload(report)
    payload_text = repr(payload)

    assert payload["average_priority_score"] == "0.870000"
    assert payload["source_count"] == "1"
    assert payload["queue_items"][0]["priority_score"] == "0.870000"
    assert payload["queue_items"][0]["sample_size_gap"] == "0.600000"
    assert payload["queue_items"][0]["derived_validation_digest"] == (
        report.queue_items[0].derived_validation_digest
    )
    assert payload["queue_items"][0]["public_source_refs"] == ("source:cpi-public-release",)
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert "Decimal" not in payload_text
    json.dumps(payload)


def test_empty_report_is_watch_with_public_decimal_zero_values() -> None:
    report = build_report(generated_at=datetime(2026, 7, 6, 8, 0, tzinfo=EASTERN))

    assert report.generated_at == GENERATED_AT
    assert report.team_count == d("0")
    assert report.specialist_team_count == d("0")
    assert report.source_count == d("0")
    assert report.observation_count == d("0")
    assert report.critical_count == d("0")
    assert report.watch_count == d("0")
    assert report.clear_count == d("0")
    assert report.average_priority_score == d("0.000000")
    assert report.status == "watch"
    assert report.reason_codes == ("source_reliability_learning_queue_empty_sources",)
    assert report.queue_items == ()


def test_frozen_dataclasses_hard_flags_digest_tampering_and_decimal_validation() -> None:
    module = api()

    with pytest.raises(ValueError, match="reliability_score must be a Decimal"):
        module.TeamSpecialistSourceReliabilityLearningQueueInputV2(
            team_id="macro_rates",
            specialist_id="inflation_researcher",
            source_id="source-cpi-agency",
            source_family="public_release",
            observed_at=GENERATED_AT,
            reliability_last_reviewed_at=GENERATED_AT,
            reliability_score=0.5,
            sample_count=d("8"),
            calibration_feedback_count=d("0"),
            public_source_refs=("source:cpi-public-release",),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(input_row(), generated_at=datetime(2026, 7, 6, 12, 0))

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        input_row(observed_at=datetime(2026, 7, 6, 12, 0))

    with pytest.raises(ValueError, match="observed_at must be on or before generated_at"):
        build_report(input_row(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="reliability_last_reviewed_at must be on or before"):
        build_report(
            input_row(reliability_last_reviewed_at=GENERATED_AT + timedelta(seconds=1)),
        )

    with pytest.raises(ValueError, match="public_source_refs must not be empty"):
        input_row(public_source_refs=())

    with pytest.raises(ValueError, match="report_only must be True"):
        replace(input_row(), report_only=False)

    with pytest.raises(FrozenInstanceError):
        input_row().reliability_score = d("0.100000")  # type: ignore[misc]

    report = build_report(input_row())
    with pytest.raises(FrozenInstanceError):
        report.status = "clear"  # type: ignore[misc]

    with pytest.raises(ValueError, match="derived_validation_digest must match queue item fields"):
        replace(report.queue_items[0], priority_score=d("0.123456"))

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, average_priority_score=d("0.123456"))


def test_unsafe_public_values_and_keys_are_rejected() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public value"):
        input_row(team_id=f"macro_{hidden_word('77616c6c6574')}")

    with pytest.raises(ValueError, match="unsafe public value"):
        input_row(public_source_refs=(f"source:{hidden_word('7472616465')}-path",))

    with pytest.raises(ValueError, match="unsafe public key"):
        module._reject_public_payload(  # noqa: SLF001
            "test payload",
            {f"public_{hidden_word('6f72646572')}": "safe"},
        )

    with pytest.raises(ValueError, match="unsafe public value"):
        module._reject_public_payload(  # noqa: SLF001
            "test payload",
            {"safe": f"public-{hidden_word('61757468')}"},
        )


def test_source_scope_has_no_external_or_write_execution_surface() -> None:
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
    ):
        assert forbidden not in lowered
    for hidden in (
        "6c697665",
        "61757468",
        "77616c6c6574",
        "6f72646572",
        "6e6574776f726b",
        "6461746162617365",
        "70657273697374",
        "7369676e696e67",
        "6d75746174696f6e",
        "627579",
        "73656c6c",
        "7472616465",
    ):
        assert hidden_word(hidden) not in lowered
