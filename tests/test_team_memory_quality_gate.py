from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.team_memory_quality_gate import (
    DEFAULT_TEAM_MEMORY_QUALITY_GATE_CONFIG_VERSION,
    TeamMemoryQualityGateConfig,
    TeamMemoryQualityGateMetrics,
    TeamMemoryQualityGateResult,
    build_team_memory_quality_gate,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _IntSubclass(int):
    pass


class _DateTimeSubclass(datetime):
    pass


def test_all_clear_metrics_are_research_ready_with_redacted_public_fields() -> None:
    raw_memory_id = "crypto-btc-specialist-team-memory"

    result = build_team_memory_quality_gate(
        _metrics(memory_id=raw_memory_id),
        config=TeamMemoryQualityGateConfig(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(result, TeamMemoryQualityGateResult)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == DEFAULT_TEAM_MEMORY_QUALITY_GATE_CONFIG_VERSION
    assert result.gate_status == "research_ready"
    assert result.gate_next_step == "allow_specialist_team_memory_research_use"
    assert result.redacted_memory_id.startswith("memory:")
    assert len(result.redacted_memory_id) == len("memory:") + 12
    assert raw_memory_id not in result.redacted_memory_id
    assert result.source_report_count == 3
    assert result.team_count == 4
    assert result.complete_team_count == 4
    assert result.complete_team_ratio == Decimal("1.000000")
    assert result.watch_source_ratio == Decimal("0.000000")
    assert result.blocked_source_ratio == Decimal("0.000000")
    assert result.latest_quality_score == Decimal("0.920000")
    assert result.quality_score_floor == Decimal("0.800000")
    assert result.reviewable_quality_score_floor == Decimal("0.500000")
    assert result.reason_codes == ("team_memory_quality_gate_passed",)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64
    assert all(char in "0123456789abcdef" for char in result.derived_validation_digest)

    rendered = repr(asdict(result)).lower()
    assert raw_memory_id not in rendered
    assert "market_slug" not in rendered
    assert "question" not in rendered
    assert "recommend" not in rendered
    assert "rank" not in rendered
    assert "position" not in rendered
    assert "order" not in rendered

    payload = result.payload
    assert payload["latest_quality_score"] == "0.920000"
    assert payload["complete_team_ratio"] == "1.000000"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert raw_memory_id not in repr(payload)
    assert not any(isinstance(value, float) for value in payload.values())


def test_watch_metrics_need_review_with_deterministic_reason_order() -> None:
    result = build_team_memory_quality_gate(
        _metrics(
            digest_status="watch",
            freshness_status="watch",
            stale_source_count=2,
            current_watch_streak_count=1,
            watch_source_count=2,
            pass_source_count=2,
            latest_quality_score=Decimal("0.700000"),
        ),
        config=TeamMemoryQualityGateConfig(),
        generated_at=GENERATED_AT,
    )

    assert result.gate_status == "needs_review"
    assert result.gate_next_step == "review_specialist_team_memory_before_research_use"
    assert result.complete_team_ratio == Decimal("1.000000")
    assert result.watch_source_ratio == Decimal("0.500000")
    assert result.blocked_source_ratio == Decimal("0.000000")
    assert result.reason_codes == (
        "team_memory_quality_gate_digest_watch",
        "team_memory_quality_gate_freshness_watch",
        "team_memory_quality_gate_stale_sources_present",
        "team_memory_quality_gate_watch_streak_present",
        "team_memory_quality_gate_watch_sources_present",
        "team_memory_quality_gate_quality_score_below_ready_floor",
    )


def test_blocking_metrics_block_before_review_reasons() -> None:
    result = build_team_memory_quality_gate(
        _metrics(
            bundle_safety_status="unsafe",
            digest_status="blocked",
            completeness_status="blocked",
            freshness_status="watch",
            complete_team_count=2,
            blocked_source_count=1,
            pass_source_count=2,
            watch_source_count=1,
            research_gap_count=3,
            expired_source_count=1,
            unknown_source_age_count=1,
            hard_flag_violation_count=1,
            current_blocked_streak_count=2,
            latest_quality_score=Decimal("0.300000"),
            duplicate_latest_digest_generated_at=True,
        ),
        config=TeamMemoryQualityGateConfig(),
        generated_at=GENERATED_AT,
    )

    assert result.gate_status == "blocked"
    assert result.gate_next_step == "block_specialist_team_memory_research_use"
    assert result.complete_team_ratio == Decimal("0.500000")
    assert result.blocked_source_ratio == Decimal("0.250000")
    assert result.reason_codes == (
        "team_memory_quality_gate_hard_flag_violation",
        "team_memory_quality_gate_bundle_unsafe",
        "team_memory_quality_gate_duplicate_latest_digest",
        "team_memory_quality_gate_digest_blocked",
        "team_memory_quality_gate_blocked_streak_present",
        "team_memory_quality_gate_research_gaps_present",
        "team_memory_quality_gate_completeness_blocked",
        "team_memory_quality_gate_expired_sources_present",
        "team_memory_quality_gate_unknown_source_age_present",
        "team_memory_quality_gate_blocked_sources_present",
        "team_memory_quality_gate_quality_score_below_review_floor",
        "team_memory_quality_gate_freshness_watch",
        "team_memory_quality_gate_watch_sources_present",
        "team_memory_quality_gate_quality_score_below_ready_floor",
    )


def test_empty_metrics_block_without_ratios() -> None:
    result = build_team_memory_quality_gate(
        _metrics(
            source_report_count=0,
            team_count=0,
            complete_team_count=0,
            pass_source_count=0,
            latest_quality_score=Decimal("0.000000"),
            bundle_safety_status="empty",
            digest_status="blocked",
        ),
        config=TeamMemoryQualityGateConfig(),
        generated_at=GENERATED_AT,
    )

    assert result.gate_status == "blocked"
    assert result.reason_codes == (
        "team_memory_quality_gate_source_metrics_empty",
        "team_memory_quality_gate_bundle_empty",
        "team_memory_quality_gate_digest_blocked",
        "team_memory_quality_gate_quality_score_below_review_floor",
        "team_memory_quality_gate_quality_score_below_ready_floor",
    )
    assert result.complete_team_ratio is None
    assert result.watch_source_ratio is None
    assert result.blocked_source_ratio is None


def test_rejects_bad_types_inconsistent_counts_and_false_hard_flags() -> None:
    with pytest.raises(ValueError, match="config_version"):
        TeamMemoryQualityGateConfig(
            config_version=_StringSubclass(
                DEFAULT_TEAM_MEMORY_QUALITY_GATE_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="min_reviewable_quality_score"):
        TeamMemoryQualityGateConfig(
            min_research_ready_quality_score=Decimal("0.400000"),
            min_reviewable_quality_score=Decimal("0.500000"),
        )
    with pytest.raises(ValueError, match="latest_quality_score"):
        _metrics(latest_quality_score="0.900000")
    with pytest.raises(ValueError, match="source_report_count"):
        _metrics(source_report_count=_IntSubclass(3))
    with pytest.raises(ValueError, match="source counts"):
        _metrics(pass_source_count=3, watch_source_count=2, blocked_source_count=0)
    with pytest.raises(ValueError, match="complete_team_count"):
        _metrics(complete_team_count=5)
    with pytest.raises(ValueError, match="generated_at"):
        build_team_memory_quality_gate(
            _metrics(),
            config=TeamMemoryQualityGateConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_metrics(), paper_only=False)

    good_result = build_team_memory_quality_gate(
        _metrics(),
        config=TeamMemoryQualityGateConfig(),
        generated_at=GENERATED_AT,
    )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            good_result,
            reason_codes=(
                "team_memory_quality_gate_quality_score_below_ready_floor",
                "team_memory_quality_gate_digest_watch",
            ),
            gate_status="needs_review",
            gate_next_step="review_specialist_team_memory_before_research_use",
            latest_quality_score=Decimal("0.700000"),
        )
    with pytest.raises(ValueError, match="redacted_memory_id"):
        replace(good_result, redacted_memory_id="memory:raw-secret-memory-id")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(good_result, derived_validation_digest="0" * 64)


def test_payload_rejects_unsafe_public_surface_and_non_json_values() -> None:
    module = importlib.import_module("polymarket_alpha_lab.team_memory_quality_gate")

    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("test payload", {"wallet_address": "0xabc"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("test payload", {"notes": "place buy order"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("test payload", {"score": 0.1})


def test_dataclasses_are_frozen() -> None:
    values = (
        TeamMemoryQualityGateConfig(),
        _metrics(),
        build_team_memory_quality_gate(
            _metrics(),
            config=TeamMemoryQualityGateConfig(),
            generated_at=GENERATED_AT,
        ),
    )

    for value in values:
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False


def test_module_scope_excludes_market_advice_io_db_and_execution_surfaces() -> None:
    module = importlib.import_module("polymarket_alpha_lab.team_memory_quality_gate")
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    forbidden_literals = (
        "market_slug",
        "question",
        "investment",
        "rank",
        "buy",
        "sell",
        "trade",
        "wallet",
        "order",
        "position",
        "recommend",
        "strategy_weight",
    )
    lowered_source = source.lower()
    assert not any(token in lowered_source for token in forbidden_literals)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "supabase",
        "subprocess",
        "pathlib",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _metrics(**overrides: object) -> TeamMemoryQualityGateMetrics:
    values = {
        "memory_id": "default-specialist-team-memory",
        "source_report_count": 3,
        "team_count": 4,
        "complete_team_count": 4,
        "pass_source_count": 4,
        "watch_source_count": 0,
        "blocked_source_count": 0,
        "research_gap_count": 0,
        "stale_source_count": 0,
        "expired_source_count": 0,
        "unknown_source_age_count": 0,
        "hard_flag_violation_count": 0,
        "current_watch_streak_count": 0,
        "current_blocked_streak_count": 0,
        "bundle_safety_status": "safe",
        "digest_status": "pass",
        "completeness_status": "pass",
        "freshness_status": "pass",
        "blocked_streak_status": "observed",
        "latest_quality_score": Decimal("0.920000"),
        "duplicate_latest_digest_generated_at": False,
    }
    values.update(overrides)
    return TeamMemoryQualityGateMetrics(**values)
