from __future__ import annotations

import importlib
import json
from hashlib import sha256
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
DIGEST_FIELD = "derived_validation_digest"
MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_memory_outcome_learning_readiness_report.py"
)


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_memory_outcome_learning_readiness_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def hidden_word(hex_value: str) -> str:
    return bytes.fromhex(hex_value).decode("ascii")


def public_digest(payload: object) -> str:
    def strip_digests(value: object) -> object:
        if isinstance(value, dict):
            return {
                key: strip_digests(item)
                for key, item in value.items()
                if key != DIGEST_FIELD
            }
        if isinstance(value, list):
            return [strip_digests(item) for item in value]
        return value

    encoded = json.dumps(
        strip_digests(payload),
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def refresh_payload_digests(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            refresh_payload_digests(item)
        if DIGEST_FIELD in value:
            value[DIGEST_FIELD] = public_digest(value)
        return
    if isinstance(value, list):
        for item in value:
            refresh_payload_digests(item)


def memory_scope(
    *,
    team_label: str = "macro_rates",
    memory_scope_label: str = "inflation_resolution_playbook",
    resolved_outcome_count: str = "4",
    attribution_note_count: str = "1",
    correction_action_count: str = "0",
    fresh_outcome_count: str = "0",
    latest_outcome_age_hours: str = "400.000000",
) -> Any:
    module = api()
    return module.ResearchTeamMemoryOutcomeLearningReadinessInput(
        team_label=team_label,
        memory_scope_label=memory_scope_label,
        resolved_outcome_count=d(resolved_outcome_count),
        attribution_note_count=d(attribution_note_count),
        correction_action_count=d(correction_action_count),
        fresh_outcome_count=d(fresh_outcome_count),
        latest_outcome_age_hours=d(latest_outcome_age_hours),
    )


def build_report(*rows: Any) -> Any:
    module = api()
    return module.build_research_team_memory_outcome_learning_readiness_report(
        rows,
        config=module.ResearchTeamMemoryOutcomeLearningReadinessConfig(),
        generated_at=GENERATED_AT,
    )


def test_exports_config_statuses_and_hard_report_only_flags() -> None:
    module = api()
    config = module.ResearchTeamMemoryOutcomeLearningReadinessConfig()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_MEMORY_OUTCOME_LEARNING_READINESS_CONFIG_VERSION",
        "RESEARCH_TEAM_MEMORY_OUTCOME_LEARNING_READINESS_STATUSES",
        "ResearchTeamMemoryOutcomeLearningReadinessConfig",
        "ResearchTeamMemoryOutcomeLearningReadinessInput",
        "ResearchTeamMemoryOutcomeLearningReadinessRow",
        "ResearchTeamMemoryOutcomeLearningReadinessReport",
        "build_research_team_memory_outcome_learning_readiness_report",
        "research_team_memory_outcome_learning_readiness_report_payload",
        "validate_research_team_memory_outcome_learning_readiness_report_payload",
    )
    assert module.RESEARCH_TEAM_MEMORY_OUTCOME_LEARNING_READINESS_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert config.config_version == "research-team-memory-outcome-learning-readiness-v0"
    assert config.min_pass_resolved_outcome_count == d("20")
    assert config.min_watch_resolved_outcome_count == d("10")
    assert config.min_pass_attribution_note_ratio == d("0.900000")
    assert config.min_watch_attribution_note_ratio == d("0.700000")
    assert config.min_pass_correction_action_ratio == d("0.800000")
    assert config.min_watch_correction_action_ratio == d("0.600000")
    assert config.min_pass_fresh_outcome_ratio == d("0.750000")
    assert config.min_watch_fresh_outcome_ratio == d("0.500000")
    assert config.max_pass_latest_outcome_age_hours == d("168.000000")
    assert config.max_watch_latest_outcome_age_hours == d("336.000000")
    assert config.min_pass_readiness_score == d("0.800000")
    assert config.min_watch_readiness_score == d("0.600000")
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True
    assert len(config.derived_validation_digest) == 64

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.ResearchTeamMemoryOutcomeLearningReadinessConfig(paper_only=False)

    with pytest.raises(ValueError, match="resolved_outcome_weight must be a Decimal"):
        module.ResearchTeamMemoryOutcomeLearningReadinessConfig(
            resolved_outcome_weight=0.25,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="status statuses must be pass, watch, or block"):
        module.ResearchTeamMemoryOutcomeLearningReadinessRow(
            team_label="macro_rates",
            memory_scope_label="inflation_resolution_playbook",
            resolved_outcome_count=d("20"),
            attribution_note_count=d("18"),
            correction_action_count=d("16"),
            fresh_outcome_count=d("15"),
            latest_outcome_age_hours=d("48.000000"),
            attribution_note_ratio=d("0.900000"),
            correction_action_ratio=d("0.800000"),
            fresh_outcome_ratio=d("0.750000"),
            freshness_score=d("0.875000"),
            readiness_score=d("0.893750"),
            status="clear",
            reason_codes=("memory_outcome_learning_readiness_pass",),
            derived_validation_digest="0" * 64,
        )


def test_report_scores_pass_watch_and_block_memory_learning_readiness() -> None:
    report = build_report(
        memory_scope(),
        memory_scope(
            team_label="weather_energy",
            memory_scope_label="load_forecast_settlement_review",
            resolved_outcome_count="12",
            attribution_note_count="9",
            correction_action_count="8",
            fresh_outcome_count="7",
            latest_outcome_age_hours="240.000000",
        ),
        memory_scope(
            team_label="sports_specials",
            memory_scope_label="injury_news_repricing_review",
            resolved_outcome_count="20",
            attribution_note_count="18",
            correction_action_count="16",
            fresh_outcome_count="15",
            latest_outcome_age_hours="48.000000",
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "research-team-memory-outcome-learning-readiness-v0"
    assert report.team_count == d("3")
    assert report.memory_scope_count == d("3")
    assert report.resolved_outcome_count == d("36")
    assert report.attribution_note_count == d("28")
    assert report.correction_action_count == d("24")
    assert report.fresh_outcome_count == d("22")
    assert report.block_count == d("1")
    assert report.watch_count == d("1")
    assert report.pass_count == d("1")
    assert report.average_readiness_score == d("0.551587")
    assert report.min_readiness_score == d("0.112500")
    assert report.status == "block"
    assert report.reason_codes == (
        "memory_outcome_learning_readiness_block",
        "resolved_outcome_sample_gap",
        "attribution_note_gap",
        "correction_action_gap",
        "freshness_gap",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    assert tuple(row.team_label for row in report.readiness_rows) == (
        "macro_rates",
        "weather_energy",
        "sports_specials",
    )
    assert report.readiness_rows[0].status == "block"
    assert report.readiness_rows[0].readiness_score == d("0.112500")
    assert report.readiness_rows[0].reason_codes == (
        "resolved_outcome_sample_gap",
        "attribution_note_gap",
        "correction_action_gap",
        "freshness_gap",
    )
    assert report.readiness_rows[1].status == "watch"
    assert report.readiness_rows[1].attribution_note_ratio == d("0.750000")
    assert report.readiness_rows[1].correction_action_ratio == d("0.666667")
    assert report.readiness_rows[1].fresh_outcome_ratio == d("0.583333")
    assert report.readiness_rows[1].freshness_score == d("0.577381")
    assert report.readiness_rows[1].readiness_score == d("0.648512")
    assert report.readiness_rows[2].status == "pass"
    assert report.readiness_rows[2].reason_codes == (
        "memory_outcome_learning_readiness_pass",
    )

    payload = api().research_team_memory_outcome_learning_readiness_report_payload(report)
    assert payload["average_readiness_score"] == "0.551587"
    assert payload["readiness_rows"][1]["freshness_score"] == "0.577381"
    assert payload["readiness_rows"][1]["derived_validation_digest"] == (
        report.readiness_rows[1].derived_validation_digest
    )
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert api().validate_research_team_memory_outcome_learning_readiness_report_payload(payload)
    json.dumps(payload, sort_keys=True)


def test_payload_digest_is_deterministic_and_public_safe() -> None:
    first = build_report(
        memory_scope(),
        memory_scope(
            team_label="sports_specials",
            memory_scope_label="injury_news_repricing_review",
            resolved_outcome_count="20",
            attribution_note_count="18",
            correction_action_count="16",
            fresh_outcome_count="15",
            latest_outcome_age_hours="48.000000",
        ),
    )
    second = build_report(
        memory_scope(
            team_label="sports_specials",
            memory_scope_label="injury_news_repricing_review",
            resolved_outcome_count="20",
            attribution_note_count="18",
            correction_action_count="16",
            fresh_outcome_count="15",
            latest_outcome_age_hours="48.000000",
        ),
        memory_scope(),
    )

    first_payload = api().research_team_memory_outcome_learning_readiness_report_payload(first)
    second_payload = api().research_team_memory_outcome_learning_readiness_report_payload(second)
    payload_text = json.dumps(first_payload, sort_keys=True).lower()

    assert first.derived_validation_digest == second.derived_validation_digest
    assert first_payload == second_payload
    assert "decimal" not in repr(first_payload).lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "live",
        "auth",
    ):
        assert forbidden not in payload_text


def test_payload_validation_rejects_recomputed_integer_numerics() -> None:
    module = api()
    payload = module.research_team_memory_outcome_learning_readiness_report_payload(
        build_report(memory_scope()),
    )
    payload["resolved_outcome_count"] = 4
    refresh_payload_digests(payload)

    with pytest.raises(ValueError, match="Decimal-derived strings"):
        module.validate_research_team_memory_outcome_learning_readiness_report_payload(payload)


def test_payload_validation_requires_recomputed_hard_flags() -> None:
    module = api()
    payload = module.research_team_memory_outcome_learning_readiness_report_payload(
        build_report(memory_scope()),
    )
    payload["readiness_rows"][0].pop("readonly")
    refresh_payload_digests(payload)

    with pytest.raises(ValueError, match="readonly must be True"):
        module.validate_research_team_memory_outcome_learning_readiness_report_payload(payload)


def test_payload_validation_rejects_recomputed_unknown_status() -> None:
    module = api()
    payload = module.research_team_memory_outcome_learning_readiness_report_payload(
        build_report(memory_scope()),
    )
    payload["status"] = "clear"
    refresh_payload_digests(payload)

    with pytest.raises(ValueError, match="status statuses must be pass, watch, or block"):
        module.validate_research_team_memory_outcome_learning_readiness_report_payload(payload)


def test_payload_validation_rejects_recomputed_live_execution_surfaces() -> None:
    module = api()
    payload = module.research_team_memory_outcome_learning_readiness_report_payload(
        build_report(memory_scope()),
    )
    payload["diagnostic_link"] = "https://example.invalid/run"
    refresh_payload_digests(payload)

    with pytest.raises(ValueError, match="unsafe public value"):
        module.validate_research_team_memory_outcome_learning_readiness_report_payload(payload)

    payload = module.research_team_memory_outcome_learning_readiness_report_payload(
        build_report(memory_scope()),
    )
    payload["execution_hint"] = "paper review only"
    refresh_payload_digests(payload)

    with pytest.raises(ValueError, match="unsafe public value"):
        module.validate_research_team_memory_outcome_learning_readiness_report_payload(payload)


def test_empty_report_validation_frozen_and_tamper_failures_are_safe() -> None:
    module = api()

    empty = build_report()
    assert empty.status == "pass"
    assert empty.team_count == d("0")
    assert empty.memory_scope_count == d("0")
    assert empty.resolved_outcome_count == d("0")
    assert empty.average_readiness_score == d("0.000000")
    assert empty.min_readiness_score == d("0.000000")
    assert empty.reason_codes == ("memory_outcome_learning_readiness_pass",)
    assert empty.readiness_rows == ()

    with pytest.raises(ValueError, match="resolved_outcome_count must be a Decimal"):
        module.ResearchTeamMemoryOutcomeLearningReadinessInput(
            team_label="macro_rates",
            memory_scope_label="inflation_resolution_playbook",
            resolved_outcome_count=4,  # type: ignore[arg-type]
            attribution_note_count=d("1"),
            correction_action_count=d("0"),
            fresh_outcome_count=d("0"),
            latest_outcome_age_hours=d("400.000000"),
        )

    with pytest.raises(ValueError, match="resolved_outcome_count must be a whole Decimal"):
        memory_scope(resolved_outcome_count="1.500000")

    with pytest.raises(ValueError, match="attribution_note_count must not exceed"):
        memory_scope(resolved_outcome_count="2", attribution_note_count="3")

    with pytest.raises(ValueError, match="unsafe public value"):
        memory_scope(team_label=f"macro_{hidden_word('6d61726b6574')}")

    with pytest.raises(ValueError, match="unsafe public value"):
        memory_scope(memory_scope_label=f"review_{hidden_word('736f75726365')}")

    with pytest.raises(ValueError, match="duplicate memory readiness key"):
        build_report(memory_scope(), memory_scope())

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(memory_scope(), paper_only=False)

    with pytest.raises(FrozenInstanceError):
        memory_scope().resolved_outcome_count = d("1")  # type: ignore[misc]

    report = build_report(memory_scope())
    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]

    with pytest.raises(ValueError, match="derived_validation_digest payload mismatch"):
        replace(report.readiness_rows[0], readiness_score=d("0.123456"))

    with pytest.raises(ValueError, match="derived_validation_digest payload mismatch"):
        replace(report, average_readiness_score=d("0.123456"))

    payload = module.research_team_memory_outcome_learning_readiness_report_payload(report)
    payload["readiness_rows"][0]["readiness_score"] = "0.123456"
    with pytest.raises(ValueError, match="derived_validation_digest payload mismatch"):
        module.validate_research_team_memory_outcome_learning_readiness_report_payload(payload)


def test_module_source_is_report_only_and_side_effect_free() -> None:
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
    for forbidden in (
        "wallet",
        "order",
        "trade",
        "sizing",
        "auth",
        "token",
        "dsn",
    ):
        assert forbidden not in lowered
