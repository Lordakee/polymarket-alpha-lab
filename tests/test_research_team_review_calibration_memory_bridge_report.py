from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_review_calibration_memory_bridge_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    review_group: str = "review.cohort.alpha",
    *,
    domain_label: str = "macro.desk",
    reviewer_label: str = "peer.panel",
    observed_seconds_ago: int = 600,
    resolved_outcome_followup_score: Decimal = d("0.900000"),
    correction_adoption_score: Decimal = d("0.850000"),
    stale_memory_reduction_score: Decimal = d("0.800000"),
    evidence_reuse_quality_score: Decimal = d("0.900000"),
    peer_review_coverage_score: Decimal = d("0.800000"),
    review_latency_seconds: Decimal = d("900.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchTeamReviewCalibrationMemoryBridgeObservation(
        review_group=review_group,
        domain_label=domain_label,
        reviewer_label=reviewer_label,
        observed_at=GENERATED_AT - timedelta(seconds=observed_seconds_ago),
        resolved_outcome_followup_score=resolved_outcome_followup_score,
        correction_adoption_score=correction_adoption_score,
        stale_memory_reduction_score=stale_memory_reduction_score,
        evidence_reuse_quality_score=evidence_reuse_quality_score,
        peer_review_coverage_score=peer_review_coverage_score,
        review_latency_seconds=review_latency_seconds,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_team_review_calibration_memory_bridge_report(
        rows,
        config=cfg,
        generated_at=GENERATED_AT,
    )


def test_pass_row_bridges_review_feedback_calibration_and_memory() -> None:
    module = api()
    report = build_report(observation())

    assert type(report) is module.ResearchTeamReviewCalibrationMemoryBridgeReport
    assert is_dataclass(report)
    assert report.status == "pass"
    assert report.observation_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.reason_codes == (
        "review_calibration_memory_bridge_report_clear",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    row = report.rows[0]
    assert row.status == "pass"
    assert row.reason_codes == ("review_calibration_memory_bridge_clear",)
    assert row.observation_age_seconds == d("600.000000")
    assert row.review_latency_score == d("1.000000")
    assert row.calibration_memory_score == d("0.850000")
    assert row.review_quality_score == d("0.900000")
    assert row.bridge_score == d("0.875000")
    assert row.bridge_pressure_score == d("0.125000")
    assert report.average_calibration_memory_score == d("0.850000")
    assert report.average_review_quality_score == d("0.900000")
    assert report.average_bridge_score == d("0.875000")
    assert report.lowest_bridge_score == d("0.875000")
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    assert (
        report.derived_validation_digest
        == module.research_team_review_calibration_memory_bridge_report_digest(report)
    )
    module.validate_research_team_review_calibration_memory_bridge_report_digest(report)


def test_block_row_surfaces_all_review_calibration_memory_failures() -> None:
    report = build_report(
        observation(
            "review.cohort.beta",
            domain_label="sports.desk",
            reviewer_label="quality.panel",
            resolved_outcome_followup_score=d("0.300000"),
            correction_adoption_score=d("0.350000"),
            stale_memory_reduction_score=d("0.400000"),
            evidence_reuse_quality_score=d("0.300000"),
            peer_review_coverage_score=d("0.200000"),
            review_latency_seconds=d("9000.000000"),
        ),
    )

    assert report.status == "block"
    assert report.block_count == d("1.000000")
    assert report.outcome_followup_gap_count == d("1.000000")
    assert report.correction_adoption_gap_count == d("1.000000")
    assert report.stale_memory_reduction_gap_count == d("1.000000")
    assert report.evidence_reuse_quality_gap_count == d("1.000000")
    assert report.peer_review_coverage_gap_count == d("1.000000")
    assert report.review_latency_gap_count == d("1.000000")
    assert report.bridge_score_gap_count == d("1.000000")
    assert report.highest_review_latency_seconds == d("9000.000000")
    assert report.highest_bridge_pressure_score == d("0.741667")
    assert report.reason_codes == (
        "review_calibration_memory_bridge_block_present",
        "outcome_followup_gap_present",
        "correction_adoption_gap_present",
        "stale_memory_reduction_gap_present",
        "evidence_reuse_quality_gap_present",
        "peer_review_coverage_gap_present",
        "review_latency_gap_present",
        "bridge_score_gap_present",
    )

    row = report.rows[0]
    assert row.review_latency_score == d("0.000000")
    assert row.calibration_memory_score == d("0.350000")
    assert row.review_quality_score == d("0.166667")
    assert row.bridge_score == d("0.258333")
    assert row.bridge_pressure_score == d("0.741667")
    assert row.reason_codes == (
        "outcome_followup_block",
        "correction_adoption_block",
        "stale_memory_reduction_block",
        "evidence_reuse_quality_block",
        "peer_review_coverage_block",
        "review_latency_block",
        "bridge_score_block",
    )


def test_watch_thresholds_are_statused_without_blocking() -> None:
    report = build_report(
        observation(
            "review.cohort.gamma",
            resolved_outcome_followup_score=d("0.600000"),
            correction_adoption_score=d("0.600000"),
            stale_memory_reduction_score=d("0.600000"),
            evidence_reuse_quality_score=d("0.600000"),
            peer_review_coverage_score=d("0.600000"),
            review_latency_seconds=d("4500.000000"),
        ),
    )

    assert report.status == "watch"
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("0.000000")
    assert report.rows[0].status == "watch"
    assert report.rows[0].review_latency_score == d("0.500000")
    assert report.rows[0].bridge_score == d("0.583333")
    assert report.rows[0].reason_codes == (
        "outcome_followup_watch",
        "correction_adoption_watch",
        "stale_memory_reduction_watch",
        "evidence_reuse_quality_watch",
        "peer_review_coverage_watch",
        "review_latency_watch",
        "bridge_score_watch",
    )
    assert report.reason_codes == (
        "review_calibration_memory_bridge_watch_present",
        "outcome_followup_gap_present",
        "correction_adoption_gap_present",
        "stale_memory_reduction_gap_present",
        "evidence_reuse_quality_gap_present",
        "peer_review_coverage_gap_present",
        "review_latency_gap_present",
        "bridge_score_gap_present",
    )


def test_payload_digest_are_deterministic_json_ready_and_public_safe() -> None:
    module = api()
    report_a = build_report(
        observation("review.cohort.safe_a"),
        observation(
            "review.cohort.safe_b",
            domain_label="policy.desk",
            reviewer_label="audit.panel",
            resolved_outcome_followup_score=d("0.300000"),
            correction_adoption_score=d("0.350000"),
            stale_memory_reduction_score=d("0.400000"),
            evidence_reuse_quality_score=d("0.300000"),
            peer_review_coverage_score=d("0.200000"),
            review_latency_seconds=d("9000.000000"),
        ),
    )
    report_b = build_report(
        observation(
            "review.cohort.safe_b",
            domain_label="policy.desk",
            reviewer_label="audit.panel",
            resolved_outcome_followup_score=d("0.300000"),
            correction_adoption_score=d("0.350000"),
            stale_memory_reduction_score=d("0.400000"),
            evidence_reuse_quality_score=d("0.300000"),
            peer_review_coverage_score=d("0.200000"),
            review_latency_seconds=d("9000.000000"),
        ),
        observation("review.cohort.safe_a"),
    )

    payload_a = module.research_team_review_calibration_memory_bridge_report_payload(
        report_a,
    )
    payload_b = report_b.payload
    digest_a = module.research_team_review_calibration_memory_bridge_report_digest(
        report_a,
    )
    digest_b = module.research_team_review_calibration_memory_bridge_report_digest(
        report_b,
    )

    assert payload_a == payload_b
    assert digest_a == digest_b
    assert payload_a["derived_validation_digest"] == digest_a
    assert len(digest_a) == 64
    int(digest_a, 16)
    assert payload_a["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload_a["observation_count"] == "2.000000"
    assert payload_a["rows"][0]["bridge_pressure_score"] >= payload_a["rows"][1][
        "bridge_pressure_score"
    ]
    json.dumps(payload_a, sort_keys=True)
    assert_no_decimal_or_float_values(payload_a)
    assert_payload_has_no_leaked_values(payload_a)

    unsafe_keys = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "url",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "live_surface",
    }
    keys = {
        field.name
        for cls in (type(report_a), type(report_a.rows[0]))
        for field in fields(cls)
    }
    assert unsafe_keys.isdisjoint(keys)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)


def test_validation_rejects_non_decimal_dates_flags_statuses_and_unsafe_labels() -> None:
    module = api()

    with pytest.raises(ValueError, match="max_pass_review_latency_seconds must be a Decimal"):
        module.ResearchTeamReviewCalibrationMemoryBridgeConfig(
            max_pass_review_latency_seconds=_DecimalSubclass("1800.000000"),
        )
    with pytest.raises(ValueError, match="resolved_outcome_followup_score must be a Decimal"):
        observation(resolved_outcome_followup_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="review_latency_seconds must be a Decimal"):
        observation(review_latency_seconds=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="max_pass_review_latency_seconds must be positive"):
        module.ResearchTeamReviewCalibrationMemoryBridgeConfig(
            max_pass_review_latency_seconds=d("0.000000"),
        )
    with pytest.raises(ValueError, match="public label"):
        observation("https://unsafe.example/path")
    with pytest.raises(ValueError, match="contains unsafe text"):
        observation("candidate.alpha")
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_team_review_calibration_memory_bridge_report(
            (),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        module.ResearchTeamReviewCalibrationMemoryBridgeObservation(
            review_group="review.cohort.alpha",
            domain_label="macro.desk",
            reviewer_label="peer.panel",
            observed_at=datetime(2026, 7, 8, 11, 0),
            resolved_outcome_followup_score=d("0.900000"),
            correction_adoption_score=d("0.850000"),
            stale_memory_reduction_score=d("0.800000"),
            evidence_reuse_quality_score=d("0.900000"),
            peer_review_coverage_score=d("0.800000"),
            review_latency_seconds=d("900.000000"),
        )
    with pytest.raises(ValueError, match="observed_at must not be in the future"):
        build_report(observation(observed_seconds_ago=-1))
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        observation(readonly=False)

    report = build_report(observation())
    with pytest.raises(ValueError, match="status"):
        replace(report, status="ready")
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="clear")


def test_empty_report_exports_frozen_dataclasses_and_status_vocabulary() -> None:
    module = api()
    report = build_report()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_REVIEW_CALIBRATION_MEMORY_BRIDGE_REPORT_CONFIG_VERSION",
        "RESEARCH_TEAM_REVIEW_CALIBRATION_MEMORY_BRIDGE_STATUSES",
        "ResearchTeamReviewCalibrationMemoryBridgeConfig",
        "ResearchTeamReviewCalibrationMemoryBridgeObservation",
        "ResearchTeamReviewCalibrationMemoryBridgeReport",
        "ResearchTeamReviewCalibrationMemoryBridgeRow",
        "build_research_team_review_calibration_memory_bridge_report",
        "research_team_review_calibration_memory_bridge_report_digest",
        "research_team_review_calibration_memory_bridge_report_payload",
        "validate_research_team_review_calibration_memory_bridge_report_digest",
    )
    assert module.RESEARCH_TEAM_REVIEW_CALIBRATION_MEMORY_BRIDGE_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert report.status == "pass"
    assert report.observation_count == d("0.000000")
    assert report.reason_codes == (
        "review_calibration_memory_bridge_empty",
    )
    assert report.rows == ()
    assert (
        report.derived_validation_digest
        == module.research_team_review_calibration_memory_bridge_report_digest(report)
    )
    assert is_dataclass(module.ResearchTeamReviewCalibrationMemoryBridgeConfig())
    assert is_dataclass(observation())
    assert is_dataclass(report)

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        module.ResearchTeamReviewCalibrationMemoryBridgeConfig().max_pass_review_latency_seconds = d(
            "1.000000",
        )

    with pytest.raises(TypeError):

        class BadConfig(module.ResearchTeamReviewCalibrationMemoryBridgeConfig):
            pass


def test_module_scope_is_report_only_and_has_no_live_surface_imports_or_calls() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
                "send",
                "trade",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def assert_no_decimal_or_float_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_decimal_or_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_decimal_or_float_values(item)
    else:
        assert type(value) is not Decimal
        assert type(value) is not float


def assert_payload_has_no_leaked_values(value: object) -> None:
    forbidden_fragments = (
        "http://",
        "https://",
        "postgres://",
        "candidate-",
        "candidate",
        "market-",
        "market",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)
