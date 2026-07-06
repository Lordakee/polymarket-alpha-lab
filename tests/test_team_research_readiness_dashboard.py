from __future__ import annotations

import ast
import dataclasses
import inspect
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.team_memory_quality_gate import (
    TeamMemoryQualityGateConfig,
    TeamMemoryQualityGateMetrics,
    build_team_memory_quality_gate,
)
from polymarket_alpha_lab.team_research_calibration_snapshot import (
    TeamResearchCalibrationOutcome,
    TeamResearchCalibrationSnapshotConfig,
    build_team_research_calibration_snapshot,
)
from polymarket_alpha_lab.team_research_coverage_map import (
    TeamResearchCoverageMapConfig,
    TeamResearchCoverageMapObservation,
    build_team_research_coverage_map,
)
from polymarket_alpha_lab.team_research_handoff import (
    TeamResearchHandoffConfig,
    TeamResearchHandoffItem,
    build_team_research_handoff_summary,
)
from polymarket_alpha_lab.team_research_readiness_dashboard import (
    DEFAULT_TEAM_RESEARCH_READINESS_DASHBOARD_CONFIG_VERSION,
    TeamResearchReadinessDashboardConfig,
    TeamResearchReadinessDashboardReport,
    TeamResearchReadinessDashboardRow,
    build_team_research_readiness_dashboard,
    team_research_readiness_dashboard_payload,
)
from polymarket_alpha_lab.team_source_reliability import (
    TeamSourceReliabilityReport,
    TeamSourceReliabilityRow,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _IntSubclass(int):
    pass


class _DateTimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _quality_gate(**overrides: object):
    values = {
        "memory_id": "private-team-memory-id",
        "source_report_count": 2,
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
        "latest_quality_score": d("0.920000"),
        "duplicate_latest_digest_generated_at": False,
    }
    values.update(overrides)
    return build_team_memory_quality_gate(
        TeamMemoryQualityGateMetrics(**values),
        config=TeamMemoryQualityGateConfig(),
        generated_at=GENERATED_AT,
    )


def _source_row(
    *,
    team_id: str = "crypto_btc",
    source_id: str = "source-primary",
    status: str = "source_reliability_validated",
    reliability_grade: str = "A",
    reliability_score: Decimal = d("0.900000"),
) -> TeamSourceReliabilityRow:
    return TeamSourceReliabilityRow(
        team_id=team_id,
        source_id=source_id,
        evidence_count=2,
        settled_evidence_count=2,
        directionally_correct_count=2,
        profitable_after_cost_count=2,
        dispute_count=0,
        average_brier_score=d("0.050000"),
        hit_rate=d("1.000000"),
        profitable_rate=d("1.000000"),
        average_weight=d("0.500000"),
        average_confidence=d("0.800000"),
        latest_generated_at=GENERATED_AT - timedelta(minutes=10),
        status=status,
        freshness_age_seconds=600,
        freshness_score=d("0.900000"),
        corroboration_count=2,
        failure_streak=0,
        reliability_score=reliability_score,
        reliability_grade=reliability_grade,
    )


def _source_report(
    rows: tuple[TeamSourceReliabilityRow, ...],
) -> TeamSourceReliabilityReport:
    return TeamSourceReliabilityReport(
        generated_at=GENERATED_AT - timedelta(minutes=5),
        config_version="team-source-reliability-v0",
        evidence_count=sum(row.evidence_count for row in rows),
        outcome_count=sum(row.settled_evidence_count for row in rows),
        settled_evidence_count=sum(row.settled_evidence_count for row in rows),
        pending_evidence_count=0,
        missing_source_evidence_count=0,
        row_count=len(rows),
        rows=rows,
        reliability_grade_counts=tuple(
            (grade, sum(1 for row in rows if row.reliability_grade == grade))
            for grade in ("A", "B", "C", "D", "F")
            if any(row.reliability_grade == grade for row in rows)
        ),
    )


def _handoff_item(
    *,
    source_team_id: str = "crypto_btc",
    target_team_id: str = "macro_rates",
    handoff_status: str = "ready",
    blockers: tuple[str, ...] = (),
    missing_evidence: tuple[str, ...] = (),
    stale_sources: tuple[str, ...] = (),
    sensitive_fields: dict[str, object] | None = None,
) -> TeamResearchHandoffItem:
    return TeamResearchHandoffItem(
        source_team_id=source_team_id,
        target_team_id=target_team_id,
        handoff_status=handoff_status,
        updated_at=GENERATED_AT - timedelta(minutes=15),
        missing_evidence=missing_evidence,
        stale_sources=stale_sources,
        blockers=blockers,
        next_research_actions=("refresh_public_context",),
        public_notes="Public handoff summary only.",
        sensitive_fields=sensitive_fields
        if sensitive_fields is not None
        else {"operator_token": "secret-token"},
        reason_codes=("handoff_ready",),
    )


def _handoff_summary(*items: TeamResearchHandoffItem):
    return build_team_research_handoff_summary(
        items,
        config=TeamResearchHandoffConfig(),
        generated_at=GENERATED_AT - timedelta(minutes=4),
    )


def _calibration_snapshot():
    return build_team_research_calibration_snapshot(
        (
            TeamResearchCalibrationOutcome(
                outcome_id="resolved-yes",
                team_id="crypto_btc",
                outcome_status="resolved",
                observed_at=GENERATED_AT - timedelta(days=2),
                resolved_at=GENERATED_AT - timedelta(hours=2),
                actual_outcome="yes",
                predicted_yes_probability=d("0.800000"),
                confidence=d("0.900000"),
            ),
            TeamResearchCalibrationOutcome(
                outcome_id="pending-fresh",
                team_id="macro_rates",
                outcome_status="pending",
                observed_at=GENERATED_AT - timedelta(hours=2),
                confidence=d("0.600000"),
            ),
            TeamResearchCalibrationOutcome(
                outcome_id="pending-stale",
                team_id="politics",
                outcome_status="pending",
                observed_at=GENERATED_AT - timedelta(days=2),
                confidence=d("0.400000"),
            ),
        ),
        config=TeamResearchCalibrationSnapshotConfig(stale_after_seconds=86_400),
        generated_at=GENERATED_AT - timedelta(minutes=3),
    )


def _coverage_map():
    return build_team_research_coverage_map(
        (
            TeamResearchCoverageMapObservation(
                research_domain="finance",
                source_family="official_api",
                team_id="crypto_btc",
                evidence_status="covered",
                public_identifier="private-coverage-id-1",
            ),
            TeamResearchCoverageMapObservation(
                research_domain="finance",
                source_family="official_api",
                team_id="macro_rates",
                evidence_status="watch",
                public_identifier="private-coverage-id-2",
            ),
            TeamResearchCoverageMapObservation(
                research_domain="politics",
                source_family="resolution_rules",
                team_id="politics",
                evidence_status="gap",
                public_identifier="private-coverage-id-3",
            ),
        ),
        config=TeamResearchCoverageMapConfig(),
        generated_at=GENERATED_AT - timedelta(minutes=2),
    )


def test_dashboard_summarizes_all_phase_1_readiness_inputs_deterministically() -> None:
    report = build_team_research_readiness_dashboard(
        quality_gates=(
            _quality_gate(memory_id="watch-memory", digest_status="watch"),
            _quality_gate(memory_id="ready-memory"),
        ),
        source_reliability_report=_source_report(
            (
                _source_row(team_id="crypto_btc", source_id="source-z"),
                _source_row(
                    team_id="macro_rates",
                    source_id="source-a",
                    status="source_reliability_watch",
                    reliability_grade="C",
                    reliability_score=d("0.500000"),
                ),
            ),
        ),
        handoff_summary=_handoff_summary(
            _handoff_item(source_team_id="macro_rates", target_team_id="crypto_btc"),
            _handoff_item(
                source_team_id="politics",
                target_team_id="macro_rates",
                handoff_status="watch",
                missing_evidence=("public_polling_methodology",),
                stale_sources=("polling_average_snapshot",),
            ),
        ),
        calibration_snapshot=_calibration_snapshot(),
        coverage_map=_coverage_map(),
        config=TeamResearchReadinessDashboardConfig(),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert isinstance(report, TeamResearchReadinessDashboardReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == DEFAULT_TEAM_RESEARCH_READINESS_DASHBOARD_CONFIG_VERSION
    assert report.dashboard_status == "needs_review"
    assert report.component_count == 5
    assert report.research_ready_component_count == 0
    assert report.needs_review_component_count == 5
    assert report.blocked_component_count == 0
    assert report.readiness_ratio == d("0.000000")
    assert report.needs_review_ratio == d("1.000000")
    assert report.blocked_ratio == d("0.000000")
    assert report.source_reliability_watch_count == 1
    assert report.source_reliability_blocked_count == 0
    assert report.handoff_watch_count == 1
    assert report.handoff_blocked_count == 0
    assert report.calibration_stale_unresolved_count == 1
    assert report.coverage_gap_count == 1
    assert report.coverage_blocked_count == 0
    assert report.reason_codes == (
        "dashboard_memory_needs_review",
        "dashboard_source_reliability_needs_review",
        "dashboard_handoffs_need_review",
        "dashboard_calibration_stale_unresolved",
        "dashboard_coverage_gaps_present",
    )
    expected_non_quality_subjects = (
        ("calibration", "team-research-calibration"),
        ("coverage", "team-research-coverage"),
        ("handoff", "macro_rates>crypto_btc"),
        ("handoff", "politics>macro_rates"),
        ("source_reliability", "crypto_btc:source-z"),
        ("source_reliability", "macro_rates:source-a"),
    )
    non_quality_subjects = tuple(
        (row.component, row.subject_id)
        for row in report.rows
        if row.component != "quality_gate"
    )
    quality_gate_subjects = tuple(
        row.subject_id for row in report.rows if row.component == "quality_gate"
    )
    assert non_quality_subjects == expected_non_quality_subjects
    assert quality_gate_subjects == tuple(sorted(quality_gate_subjects))
    assert all(subject_id.startswith("memory:") for subject_id in quality_gate_subjects)
    assert not any("watch-memory" in subject_id for subject_id in quality_gate_subjects)
    assert not any("ready-memory" in subject_id for subject_id in quality_gate_subjects)
    assert all(row.paper_only and row.report_only and row.readonly for row in report.rows)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_dashboard_payload_redacts_sensitive_fields_and_decimal_values() -> None:
    report = build_team_research_readiness_dashboard(
        quality_gates=(_quality_gate(memory_id="raw-secret-memory"),),
        source_reliability_report=_source_report(
            (_source_row(source_id="source-redacted-alpha"),),
        ),
        handoff_summary=_handoff_summary(
            _handoff_item(
                sensitive_fields={
                    "api_key": "abc123",
                    "wallet": "0xdeadbeef",
                    "nested": {"private_token": "secret-token"},
                },
            ),
        ),
        calibration_snapshot=_calibration_snapshot(),
        coverage_map=_coverage_map(),
        config=TeamResearchReadinessDashboardConfig(),
        generated_at=GENERATED_AT,
    )

    payload = team_research_readiness_dashboard_payload(report)
    rendered_payload = repr(payload)
    rendered_report = repr(report)

    assert payload["readiness_ratio"] == "0.600000"
    assert payload["rows"][0]["component"] == "calibration"
    assert "raw-secret-memory" not in rendered_payload
    assert "raw-secret-memory" not in rendered_report
    assert "abc123" not in rendered_payload
    assert "0xdeadbeef" not in rendered_payload
    assert "secret-token" not in rendered_payload
    assert "<redacted>" in rendered_payload
    assert "private-coverage-id" not in rendered_payload
    assert all("public_identifier" not in str(key) for key in payload)


def test_dashboard_payload_exposes_tamper_evident_validation_digest() -> None:
    report = build_team_research_readiness_dashboard(
        quality_gates=(_quality_gate(memory_id="digest-memory"),),
        source_reliability_report=_source_report((_source_row(),)),
        handoff_summary=_handoff_summary(_handoff_item()),
        calibration_snapshot=_calibration_snapshot(),
        coverage_map=_coverage_map(),
        config=TeamResearchReadinessDashboardConfig(),
        generated_at=GENERATED_AT,
    )

    payload = team_research_readiness_dashboard_payload(report)

    assert len(report.validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.validation_digest)
    assert payload["validation_digest"] == report.validation_digest
    assert payload["rows"][0]["validation_digest"] == report.rows[0].validation_digest

    tampered_payload = dict(payload)
    tampered_payload["component_count"] = "999"
    with pytest.raises(ValueError, match="validation_digest"):
        team_research_readiness_dashboard_payload(tampered_payload)

    missing_digest_payload = dict(payload)
    missing_digest_payload.pop("validation_digest")
    with pytest.raises(ValueError, match="validation_digest"):
        team_research_readiness_dashboard_payload(missing_digest_payload)

    tampered_rows_payload = dict(payload)
    tampered_rows = [dict(row) for row in payload["rows"]]
    tampered_rows[0]["readiness_status"] = "blocked"
    tampered_rows_payload["rows"] = tampered_rows
    with pytest.raises(ValueError, match="validation_digest"):
        team_research_readiness_dashboard_payload(tampered_rows_payload)


def test_dashboard_payload_rejects_unsafe_dicts_and_exposes_decimal_strings() -> None:
    report = build_team_research_readiness_dashboard(
        quality_gates=(_quality_gate(),),
        source_reliability_report=_source_report((_source_row(),)),
        handoff_summary=_handoff_summary(_handoff_item()),
        calibration_snapshot=_calibration_snapshot(),
        coverage_map=_coverage_map(),
        config=TeamResearchReadinessDashboardConfig(),
        generated_at=GENERATED_AT,
    )
    payload = team_research_readiness_dashboard_payload(report)

    assert payload["component_count"] == "5"
    assert payload["rows"][0]["item_count"] == "3"
    assert payload["rows"][0]["readiness_score"] == "0.666667"

    raw_numeric_payload = dict(payload)
    raw_numeric_payload["component_count"] = 5
    with pytest.raises(ValueError, match="Decimal"):
        team_research_readiness_dashboard_payload(raw_numeric_payload)

    missing_flag_payload = dict(payload)
    missing_flag_payload.pop("readonly")
    with pytest.raises(ValueError, match="readonly"):
        team_research_readiness_dashboard_payload(missing_flag_payload)

    unsafe_payload = dict(payload)
    unsafe_payload["live_order_id"] = "paper-only"
    with pytest.raises(ValueError, match="unsafe live surface field"):
        team_research_readiness_dashboard_payload(unsafe_payload)


def test_blocked_dashboard_rolls_up_blocking_components_and_none_ratios_when_empty() -> None:
    empty = build_team_research_readiness_dashboard(
        quality_gates=(),
        source_reliability_report=None,
        handoff_summary=_handoff_summary(),
        calibration_snapshot=build_team_research_calibration_snapshot(
            (),
            config=TeamResearchCalibrationSnapshotConfig(),
            generated_at=GENERATED_AT,
        ),
        coverage_map=build_team_research_coverage_map(
            (),
            config=TeamResearchCoverageMapConfig(),
            generated_at=GENERATED_AT,
        ),
        config=TeamResearchReadinessDashboardConfig(),
        generated_at=GENERATED_AT,
    )

    assert empty.dashboard_status == "blocked"
    assert empty.component_count == 5
    assert empty.research_ready_component_count == 1
    assert empty.needs_review_component_count == 0
    assert empty.blocked_component_count == 4
    assert empty.readiness_ratio == d("0.200000")
    assert empty.blocked_ratio == d("0.800000")
    assert empty.reason_codes == (
        "dashboard_memory_empty",
        "dashboard_source_reliability_missing",
        "dashboard_handoffs_empty",
        "dashboard_coverage_blocked",
    )
    assert tuple((row.component, row.subject_id, row.readiness_status) for row in empty.rows) == (
        ("calibration", "team-research-calibration", "research_ready"),
        ("coverage", "team-research-coverage", "blocked"),
        ("handoff", "team-research-handoffs", "blocked"),
        ("quality_gate", "team-memory-quality-gates", "blocked"),
        ("source_reliability", "team-source-reliability", "blocked"),
    )

    manual_empty = TeamResearchReadinessDashboardReport(
        generated_at=GENERATED_AT,
        config_version=DEFAULT_TEAM_RESEARCH_READINESS_DASHBOARD_CONFIG_VERSION,
        dashboard_status="blocked",
        component_count=0,
        research_ready_component_count=0,
        needs_review_component_count=0,
        blocked_component_count=0,
        readiness_ratio=None,
        needs_review_ratio=None,
        blocked_ratio=None,
        memory_quality_gate_count=0,
        memory_quality_gate_research_ready_count=0,
        memory_quality_gate_needs_review_count=0,
        memory_quality_gate_blocked_count=0,
        source_reliability_row_count=0,
        source_reliability_watch_count=0,
        source_reliability_blocked_count=0,
        handoff_count=0,
        handoff_watch_count=0,
        handoff_blocked_count=0,
        calibration_outcome_count=0,
        calibration_stale_unresolved_count=0,
        coverage_observation_count=0,
        coverage_gap_count=0,
        coverage_blocked_count=0,
        rows=(),
        reason_codes=("dashboard_memory_empty", "dashboard_source_reliability_missing"),
    )
    assert manual_empty.readiness_ratio is None


def test_dashboard_rejects_bad_types_times_inconsistent_counts_and_false_flags() -> None:
    with pytest.raises(ValueError, match="config_version"):
        TeamResearchReadinessDashboardConfig(
            config_version=_StringSubclass(
                DEFAULT_TEAM_RESEARCH_READINESS_DASHBOARD_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_team_research_readiness_dashboard(
            quality_gates=(),
            source_reliability_report=None,
            handoff_summary=_handoff_summary(),
            calibration_snapshot=_calibration_snapshot(),
            coverage_map=_coverage_map(),
            config=TeamResearchReadinessDashboardConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        build_team_research_readiness_dashboard(
            quality_gates=(),
            source_reliability_report=None,
            handoff_summary=_handoff_summary(),
            calibration_snapshot=_calibration_snapshot(),
            coverage_map=_coverage_map(),
            config=TeamResearchReadinessDashboardConfig(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="quality_gates"):
        build_team_research_readiness_dashboard(
            quality_gates=(object(),),
            source_reliability_report=None,
            handoff_summary=_handoff_summary(),
            calibration_snapshot=_calibration_snapshot(),
            coverage_map=_coverage_map(),
            config=TeamResearchReadinessDashboardConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="source_reliability_report"):
        build_team_research_readiness_dashboard(
            quality_gates=(),
            source_reliability_report=object(),
            handoff_summary=_handoff_summary(),
            calibration_snapshot=_calibration_snapshot(),
            coverage_map=_coverage_map(),
            config=TeamResearchReadinessDashboardConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(TeamResearchReadinessDashboardConfig(), paper_only=False)
    with pytest.raises(ValueError, match="component_count"):
        TeamResearchReadinessDashboardReport(
            generated_at=GENERATED_AT,
            config_version=DEFAULT_TEAM_RESEARCH_READINESS_DASHBOARD_CONFIG_VERSION,
            dashboard_status="research_ready",
            component_count=_IntSubclass(1),
            research_ready_component_count=1,
            needs_review_component_count=0,
            blocked_component_count=0,
            readiness_ratio=d("1.000000"),
            needs_review_ratio=d("0.000000"),
            blocked_ratio=d("0.000000"),
            memory_quality_gate_count=0,
            memory_quality_gate_research_ready_count=0,
            memory_quality_gate_needs_review_count=0,
            memory_quality_gate_blocked_count=0,
            source_reliability_row_count=0,
            source_reliability_watch_count=0,
            source_reliability_blocked_count=0,
            handoff_count=0,
            handoff_watch_count=0,
            handoff_blocked_count=0,
            calibration_outcome_count=0,
            calibration_stale_unresolved_count=0,
            coverage_observation_count=0,
            coverage_gap_count=0,
            coverage_blocked_count=0,
            rows=(),
            reason_codes=("dashboard_memory_empty",),
        )


def test_dashboard_dataclasses_are_frozen_and_manual_rows_are_validated() -> None:
    row = TeamResearchReadinessDashboardRow(
        component="quality_gate",
        subject_id="memory:000001",
        readiness_status="research_ready",
        generated_at=GENERATED_AT,
        item_count=1,
        watch_count=0,
        blocked_count=0,
        readiness_score=d("1.000000"),
        redacted_refs=("memory:000001",),
        reason_codes=("team_memory_quality_gate_passed",),
    )

    with pytest.raises(FrozenInstanceError):
        row.item_count = 2
    with pytest.raises(ValueError, match="redacted_refs"):
        replace(row, redacted_refs=("raw-private-ref",))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(row, reason_codes=())


def test_dashboard_module_scope_has_no_trading_auth_network_or_ranking_surface() -> None:
    import polymarket_alpha_lab.team_research_readiness_dashboard as api

    source = inspect.getsource(api)
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert not imported_roots & {
        "aiohttp",
        "eth_account",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "urllib",
        "web3",
    }
    forbidden_fragments = (
        "auth",
        "wallet",
        "order",
        "recommendation",
        "execution_rank",
        "position_sizing",
        "strategy_weight",
        "tuning",
        "private_key",
    )
    assert all(fragment not in source.lower() for fragment in forbidden_fragments)
    assert api.__all__ == (
        "DEFAULT_TEAM_RESEARCH_READINESS_DASHBOARD_CONFIG_VERSION",
        "TeamResearchReadinessDashboardConfig",
        "TeamResearchReadinessDashboardReport",
        "TeamResearchReadinessDashboardRow",
        "build_team_research_readiness_dashboard",
        "team_research_readiness_dashboard_payload",
    )


def test_dashboard_exported_payload_shape_contains_no_raw_dataclasses_or_floats() -> None:
    report = build_team_research_readiness_dashboard(
        quality_gates=(_quality_gate(),),
        source_reliability_report=_source_report((_source_row(),)),
        handoff_summary=_handoff_summary(_handoff_item()),
        calibration_snapshot=_calibration_snapshot(),
        coverage_map=_coverage_map(),
        config=TeamResearchReadinessDashboardConfig(),
        generated_at=GENERATED_AT,
    )
    payload = team_research_readiness_dashboard_payload(report)

    assert dataclasses.is_dataclass(report)
    assert not dataclasses.is_dataclass(payload)
    assert isinstance(payload, dict)

    def assert_no_floats(value: object) -> None:
        if isinstance(value, dict):
            for item in value.values():
                assert_no_floats(item)
        elif isinstance(value, list):
            for item in value:
                assert_no_floats(item)
        else:
            assert type(value) is not float

    assert_no_floats(payload)
