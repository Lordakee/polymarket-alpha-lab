from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.research_team_calibration_feedback_loop_health_report as subject
from polymarket_alpha_lab.research_team_calibration_feedback_loop_health_report import (
    DEFAULT_RESEARCH_TEAM_CALIBRATION_FEEDBACK_LOOP_HEALTH_REPORT_CONFIG_VERSION,
    PUBLIC_STATUSES,
    ResearchTeamCalibrationFeedbackLoopHealthConfig,
    ResearchTeamCalibrationFeedbackLoopHealthObservation,
    ResearchTeamCalibrationFeedbackLoopHealthReport,
    build_research_team_calibration_feedback_loop_health_report,
    format_research_team_calibration_feedback_loop_health_digest,
    research_team_calibration_feedback_loop_health_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_team_calibration_feedback_loop_health_report.py",
)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    feedback_loop_id: str,
    team_id: str,
    *,
    resolved_outcome_follow_up_ratio: Decimal = d("0.950000"),
    correction_adoption_ratio: Decimal = d("0.900000"),
    stale_memory_reduction_ratio: Decimal = d("0.850000"),
    evidence_reuse_quality_ratio: Decimal = d("0.880000"),
    peer_review_coverage_ratio: Decimal = d("0.920000"),
    average_review_latency_seconds: Decimal = d("3600.000000"),
    reviewed_resolution_count: Decimal = d("10.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchTeamCalibrationFeedbackLoopHealthObservation:
    return ResearchTeamCalibrationFeedbackLoopHealthObservation(
        feedback_loop_id=feedback_loop_id,
        team_id=team_id,
        resolved_outcome_follow_up_ratio=resolved_outcome_follow_up_ratio,
        correction_adoption_ratio=correction_adoption_ratio,
        stale_memory_reduction_ratio=stale_memory_reduction_ratio,
        evidence_reuse_quality_ratio=evidence_reuse_quality_ratio,
        peer_review_coverage_ratio=peer_review_coverage_ratio,
        average_review_latency_seconds=average_review_latency_seconds,
        reviewed_resolution_count=reviewed_resolution_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build(
    rows: tuple[ResearchTeamCalibrationFeedbackLoopHealthObservation, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    config: ResearchTeamCalibrationFeedbackLoopHealthConfig | None = None,
) -> ResearchTeamCalibrationFeedbackLoopHealthReport:
    return build_research_team_calibration_feedback_loop_health_report(
        rows,
        generated_at=generated_at,
        config=config,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_values(item))
        return tuple(nested)
    return (value,)


def assert_decimal_numeric_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if field.name.endswith(("_count", "_ratio", "_score", "_seconds")):
            assert type(item) is Decimal


def test_calibration_feedback_loop_health_scores_all_feedback_dimensions() -> None:
    report = build(
        (
            observation("alpha_loop", "alpha_team"),
            observation(
                "beta_loop",
                "beta_team",
                resolved_outcome_follow_up_ratio=d("0.700000"),
                correction_adoption_ratio=d("0.620000"),
                stale_memory_reduction_ratio=d("0.650000"),
                evidence_reuse_quality_ratio=d("0.660000"),
                peer_review_coverage_ratio=d("0.600000"),
                average_review_latency_seconds=d("172800.000000"),
                reviewed_resolution_count=d("8.000000"),
            ),
            observation(
                "gamma_loop",
                "gamma_team",
                resolved_outcome_follow_up_ratio=d("0.400000"),
                correction_adoption_ratio=d("0.500000"),
                stale_memory_reduction_ratio=d("0.300000"),
                evidence_reuse_quality_ratio=d("0.550000"),
                peer_review_coverage_ratio=d("0.450000"),
                average_review_latency_seconds=d("345600.000000"),
                reviewed_resolution_count=d("4.000000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        DEFAULT_RESEARCH_TEAM_CALIBRATION_FEEDBACK_LOOP_HEALTH_REPORT_CONFIG_VERSION
    )
    assert report.health_status == "block"
    assert report.loop_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.total_reviewed_resolution_count == d("22.000000")
    assert report.min_health_score == d("0.375000")
    assert report.average_health_score == d("0.638812")
    assert report.average_review_latency_seconds == d("174000.000000")
    assert report.reason_codes == ("calibration_feedback_loop_health_report_block",)
    assert report.public_digest.startswith("sha256:")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    blocked, watched, passed = report.rows
    assert (blocked.feedback_loop_id, blocked.team_id, blocked.status) == (
        "gamma_loop",
        "gamma_team",
        "block",
    )
    assert blocked.review_latency_score == ZERO
    assert blocked.health_score == d("0.375000")
    assert blocked.reason_codes == (
        "calibration_feedback_loop_health_block",
        "resolved_outcome_follow_up_block",
            "correction_adoption_block",
            "stale_memory_reduction_block",
            "evidence_reuse_quality_watch",
            "peer_review_coverage_block",
            "review_latency_block",
        )
    assert (watched.feedback_loop_id, watched.status, watched.review_latency_score) == (
        "beta_loop",
        "watch",
        d("0.500000"),
    )
    assert watched.health_score == d("0.625500")
    assert (passed.feedback_loop_id, passed.status, passed.health_score) == (
        "alpha_loop",
        "pass",
        d("0.915937"),
    )

    for row in report.rows:
        assert row.paper_only is True
        assert row.report_only is True
        assert row.readonly is True
        assert_decimal_numeric_fields(row)
    assert_decimal_numeric_fields(report)

    digest = format_research_team_calibration_feedback_loop_health_digest(report)
    assert "status=block" in digest
    assert "loops=3.000000" in digest
    assert "average_score=0.638812" in digest
    assert "average_review_latency_seconds=174000.000000" in digest
    assert f"public_digest={report.public_digest}" in digest


def test_calibration_feedback_loop_payload_and_digest_are_deterministic() -> None:
    rows = (
        observation(
            "beta_loop",
            "beta_team",
            resolved_outcome_follow_up_ratio=d("0.700000"),
            correction_adoption_ratio=d("0.620000"),
            stale_memory_reduction_ratio=d("0.650000"),
            evidence_reuse_quality_ratio=d("0.660000"),
            peer_review_coverage_ratio=d("0.600000"),
            average_review_latency_seconds=d("172800.000000"),
            reviewed_resolution_count=d("8.000000"),
        ),
        observation("alpha_loop", "alpha_team"),
    )

    first = build(rows)
    second = build(tuple(reversed(rows)), generated_at=GENERATED_AT)

    assert first.public_digest == second.public_digest
    assert research_team_calibration_feedback_loop_health_payload(first) == (
        research_team_calibration_feedback_loop_health_payload(second)
    )

    payload = research_team_calibration_feedback_loop_health_payload(first)
    assert payload["public_digest"] == first.public_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "0.625500" in walk_values(payload)
    assert all(type(value) is not Decimal for value in walk_values(payload))
    assert research_team_calibration_feedback_loop_health_payload(payload) == payload

    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    assert "beta_loop" in encoded
    assert "raw_candidate" not in encoded
    tampered = dict(payload)
    tampered["average_health_score"] = "0.999999"
    with pytest.raises(ValueError, match="public_digest"):
        research_team_calibration_feedback_loop_health_payload(tampered)


def test_calibration_feedback_loop_statuses_are_exactly_pass_watch_block() -> None:
    assert PUBLIC_STATUSES == ("pass", "watch", "block")

    pass_report = build((observation("alpha_loop", "alpha_team"),))
    watch_report = build(
        (
            observation(
                "beta_loop",
                "beta_team",
                resolved_outcome_follow_up_ratio=d("0.700000"),
                correction_adoption_ratio=d("0.620000"),
                stale_memory_reduction_ratio=d("0.650000"),
                evidence_reuse_quality_ratio=d("0.660000"),
                peer_review_coverage_ratio=d("0.600000"),
                average_review_latency_seconds=d("172800.000000"),
            ),
        ),
    )
    block_report = build(
        (
            observation(
                "gamma_loop",
                "gamma_team",
                resolved_outcome_follow_up_ratio=d("0.400000"),
                correction_adoption_ratio=d("0.500000"),
                stale_memory_reduction_ratio=d("0.300000"),
                evidence_reuse_quality_ratio=d("0.550000"),
                peer_review_coverage_ratio=d("0.450000"),
                average_review_latency_seconds=d("345600.000000"),
            ),
        ),
    )

    assert pass_report.health_status == "pass"
    assert watch_report.health_status == "watch"
    assert block_report.health_status == "block"


def test_calibration_feedback_loop_requires_frozen_dataclasses_and_decimal_inputs() -> None:
    report = build((observation("alpha_loop", "alpha_team"),))

    with pytest.raises(FrozenInstanceError):
        report.health_status = "watch"  # type: ignore[misc]

    for value in (report, report.rows[0]):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
        assert_decimal_numeric_fields(value)

    with pytest.raises(ValueError, match="Decimal"):
        observation("alpha_loop", "alpha_team", correction_adoption_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        observation("alpha_loop", "alpha_team", reviewed_resolution_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        observation(
            "alpha_loop",
            "alpha_team",
            resolved_outcome_follow_up_ratio=_DecimalSubclass("0.950000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        observation("alpha_loop", "alpha_team", paper_only=False)


def test_calibration_feedback_loop_rejects_raw_identifiers_and_unsafe_payloads() -> None:
    unsafe_values = (
        "raw_candidate_42",
        "candidate42",
        "market42",
        "market_slug_alpha",
        "slug_alpha",
        "question_alpha",
        "will-this-market-resolve-yes",
        "https://example.test/ref",
        "postgresql://user:pass@localhost/db",
        "wallet_order_trade",
        "route_alpha",
        "execute_alpha",
        "place_alpha",
        "recommend_alpha",
        "size_alpha",
    )
    for value in unsafe_values:
        with pytest.raises(ValueError):
            observation(value, "alpha_team")

    report = build((observation("alpha_loop", "alpha_team"),))
    public_json = json.dumps(
        research_team_calibration_feedback_loop_health_payload(report),
    ).lower()
    for value in unsafe_values:
        assert value.lower() not in public_json
    for field_name in fields(ResearchTeamCalibrationFeedbackLoopHealthObservation):
        assert field_name.name not in {
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
            "order",
            "trade",
            "live",
        }

    tampered = research_team_calibration_feedback_loop_health_payload(report)
    tampered["rows"][0]["feedback_loop_id"] = "raw_candidate_42"  # type: ignore[index]
    with pytest.raises(ValueError):
        research_team_calibration_feedback_loop_health_payload(tampered)

    tampered_key = research_team_calibration_feedback_loop_health_payload(report)
    tampered_key["market_id"] = "public-looking"
    with pytest.raises(ValueError):
        research_team_calibration_feedback_loop_health_payload(tampered_key)

    tampered_nested_flag = research_team_calibration_feedback_loop_health_payload(report)
    tampered_nested_flag["rows"][0]["readonly"] = False  # type: ignore[index]
    tampered_nested_flag["public_digest"] = subject._public_digest(  # noqa: SLF001
        {key: value for key, value in tampered_nested_flag.items() if key != "public_digest"},
    )
    with pytest.raises(ValueError, match="readonly"):
        research_team_calibration_feedback_loop_health_payload(tampered_nested_flag)


def test_calibration_feedback_loop_rejects_decimal_overprecision() -> None:
    with pytest.raises(ValueError, match="correction_adoption_ratio"):
        observation(
            "alpha_loop",
            "alpha_team",
            correction_adoption_ratio=d("0.9000004"),
        )
    with pytest.raises(ValueError, match="pass_health_score_threshold"):
        ResearchTeamCalibrationFeedbackLoopHealthConfig(
            pass_health_score_threshold=d("0.8000004"),
        )


def test_calibration_feedback_loop_module_has_no_db_network_or_live_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    banned_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "web3",
        "subprocess",
    }
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert imports.isdisjoint(banned_import_roots)

    banned_call_names = {
        "connect",
        "execute",
        "executemany",
        "commit",
        "rollback",
        "send",
        "post",
        "put",
        "patch",
        "delete",
        "request",
        "place_order",
        "size_order",
        "recommend",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in banned_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in banned_call_names

    public_exports = set(getattr(subject, "__all__"))
    assert not any("order" in name or "wallet" in name or "trade" in name for name in public_exports)
    assert not any("recommend" in name or "sizing" in name or "live" in name for name in public_exports)


def test_calibration_feedback_loop_rejects_mismatched_public_digest() -> None:
    report = build((observation("alpha_loop", "alpha_team"),))
    values = {
        field.name: getattr(report, field.name)
        for field in fields(ResearchTeamCalibrationFeedbackLoopHealthReport)
    }
    values["public_digest"] = "sha256:" + ("0" * 64)

    with pytest.raises(ValueError, match="public_digest"):
        ResearchTeamCalibrationFeedbackLoopHealthReport(**values)
