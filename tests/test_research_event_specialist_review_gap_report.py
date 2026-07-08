from __future__ import annotations

import ast
import dataclasses
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_NAME = "polymarket_alpha_lab.research_event_specialist_review_gap_report"


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def config(**overrides: object):
    module = api()
    return module.ResearchEventSpecialistReviewGapConfig(**overrides)


def observation(
    event_bucket: str,
    *,
    completed_specialist_lanes: tuple[str, ...] = (
        "domain",
        "rules",
        "evidence",
        "probability",
        "resolution",
    ),
    reviewed_at: datetime = datetime(2026, 7, 8, 11, 0, tzinfo=UTC),
    dissenting_specialist_count: Decimal = d("0"),
    evidence_coverage_ratio: Decimal = d("0.950000"),
    manual_escalation_score: Decimal = d("0.100000"),
):
    module = api()
    return module.ResearchEventSpecialistReviewGapObservation(
        event_bucket=event_bucket,
        completed_specialist_lanes=completed_specialist_lanes,
        reviewed_at=reviewed_at,
        dissenting_specialist_count=dissenting_specialist_count,
        evidence_coverage_ratio=evidence_coverage_ratio,
        manual_escalation_score=manual_escalation_score,
    )


def build_report(
    *observations: object,
    cfg=None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_research_event_specialist_review_gap_report(
        observations,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_specialist_review_gap_report_aggregates_review_gaps_and_digest_payload() -> None:
    module = api()
    passed = observation("policy-catalyst-calendar")
    watched = observation(
        "weather-resolution-window",
        completed_specialist_lanes=("domain", "rules", "evidence", "probability"),
        reviewed_at=datetime(2026, 7, 7, 11, 0, tzinfo=UTC),
        dissenting_specialist_count=d("1"),
        evidence_coverage_ratio=d("0.700000"),
        manual_escalation_score=d("0.500000"),
    )
    blocked = observation(
        "crypto-resolution-rule",
        completed_specialist_lanes=("domain", "rules"),
        reviewed_at=datetime(2026, 7, 5, 12, 0, tzinfo=UTC),
        dissenting_specialist_count=d("3"),
        evidence_coverage_ratio=d("0.400000"),
        manual_escalation_score=d("0.800000"),
    )

    report = build_report(passed, watched, blocked)
    reversed_report = build_report(blocked, watched, passed)
    payload = module.research_event_specialist_review_gap_report_payload(report)

    assert dataclasses.is_dataclass(report)
    assert report.status == "block"
    assert report.event_bucket_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.missing_specialist_lane_count == d("4.000000")
    assert report.stale_review_count == d("2.000000")
    assert report.dissent_pressure_count == d("2.000000")
    assert report.evidence_coverage_gap_count == d("2.000000")
    assert report.manual_escalation_count == d("2.000000")
    assert report.max_review_age_seconds == d("259200.000000")
    assert report.total_dissenting_specialist_count == d("4.000000")
    assert report.min_evidence_coverage_ratio == d("0.400000")
    assert report.max_manual_escalation_score == d("0.800000")
    assert report.average_gap_pressure_score == d("0.448333")
    assert report.reason_code_counts == (
        ("specialist_lane_missing_block", d("1.000000")),
        ("review_age_block", d("1.000000")),
        ("dissent_pressure_block", d("1.000000")),
        ("evidence_coverage_block", d("1.000000")),
        ("manual_escalation_block", d("1.000000")),
        ("specialist_lane_missing_watch", d("1.000000")),
        ("review_age_watch", d("1.000000")),
        ("dissent_pressure_watch", d("1.000000")),
        ("evidence_coverage_watch", d("1.000000")),
        ("manual_escalation_watch", d("1.000000")),
        ("specialist_review_gap_clear", d("1.000000")),
    )

    assert tuple((row.event_bucket, row.status) for row in report.rows) == (
        ("crypto-resolution-rule", "block"),
        ("weather-resolution-window", "watch"),
        ("policy-catalyst-calendar", "pass"),
    )

    blocked_row, watched_row, passed_row = report.rows
    assert blocked_row.missing_specialist_lanes == (
        "evidence",
        "probability",
        "resolution",
    )
    assert blocked_row.review_age_seconds == d("259200.000000")
    assert blocked_row.missing_specialist_lane_count == d("3.000000")
    assert blocked_row.completed_specialist_lane_count == d("2.000000")
    assert blocked_row.manual_escalation_urgency == "block"
    assert blocked_row.gap_pressure_score == d("0.880000")
    assert blocked_row.reason_codes == (
        "specialist_lane_missing_block",
        "review_age_block",
        "dissent_pressure_block",
        "evidence_coverage_block",
        "manual_escalation_block",
    )
    assert watched_row.manual_escalation_urgency == "watch"
    assert watched_row.review_age_seconds == d("90000.000000")
    assert watched_row.gap_pressure_score == d("0.430833")
    assert watched_row.reason_codes == (
        "specialist_lane_missing_watch",
        "review_age_watch",
        "dissent_pressure_watch",
        "evidence_coverage_watch",
        "manual_escalation_watch",
    )
    assert passed_row.status == "pass"
    assert passed_row.reason_codes == ("specialist_review_gap_clear",)

    assert report.rows == reversed_report.rows
    assert report.derived_validation_digest == reversed_report.derived_validation_digest
    assert payload == module.research_event_specialist_review_gap_report_payload(
        reversed_report,
    )
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["rows"][0]["gap_pressure_score"] == "0.880000"
    assert payload["rows"][0]["missing_specialist_lanes"] == [
        "evidence",
        "probability",
        "resolution",
    ]
    assert _public_numeric_paths(payload) == ()
    assert module.validate_research_event_specialist_review_gap_report_payload(payload)


def test_specialist_review_gap_public_payload_is_deterministic_redacted_and_validated() -> None:
    module = api()
    observations = (
        observation("policy-catalyst-calendar"),
        observation(
            "rates-decision-window",
            completed_specialist_lanes=("domain", "rules", "evidence", "probability"),
            reviewed_at=datetime(2026, 7, 7, 10, 0, tzinfo=UTC),
            dissenting_specialist_count=d("1"),
            evidence_coverage_ratio=d("0.720000"),
            manual_escalation_score=d("0.450000"),
        ),
    )
    report = build_report(*observations)
    payload = module.research_event_specialist_review_gap_report_payload(report)

    assert module.STATUSES == ("pass", "watch", "block")
    assert module.SPECIALIST_REVIEW_LANES == (
        "domain",
        "rules",
        "evidence",
        "probability",
        "resolution",
    )
    assert module.research_event_specialist_review_gap_report_digest(report) == (
        payload["derived_validation_digest"]
    )
    assert module.research_event_specialist_review_gap_report_payload(payload) == payload

    rendered = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "source",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "position",
        "recommendation",
        "sizing",
        "auth",
        "private",
    ):
        assert forbidden not in rendered

    tampered = dict(payload)
    tampered["event_bucket_count"] = "3.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_event_specialist_review_gap_report_payload(tampered)
    with pytest.raises(ValueError, match="public payload"):
        module.research_event_specialist_review_gap_report_payload(
            {**payload, "raw_candidate_id": "candidate-123"},
        )
    with pytest.raises(ValueError, match="public payload"):
        module.research_event_specialist_review_gap_report_payload(
            {**payload, "event_bucket_count": d("2.000000")},
        )
    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_event_specialist_review_gap_report_payload(
            missing_digest,
        )


def test_specialist_review_gap_validates_frozen_flags_inputs_and_pure_scope() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_EVENT_SPECIALIST_REVIEW_GAP_CONFIG_VERSION",
        "SPECIALIST_REVIEW_LANES",
        "STATUSES",
        "ResearchEventSpecialistReviewGapConfig",
        "ResearchEventSpecialistReviewGapObservation",
        "ResearchEventSpecialistReviewGapReport",
        "ResearchEventSpecialistReviewGapRow",
        "build_research_event_specialist_review_gap_report",
        "research_event_specialist_review_gap_report_digest",
        "research_event_specialist_review_gap_report_payload",
        "validate_research_event_specialist_review_gap_report_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert dataclasses.is_dataclass(exported)
            assert exported.__dataclass_params__.frozen

    report = build_report(observation("policy-catalyst-calendar"))
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.rows[0].paper_only is True
    assert report.rows[0].report_only is True
    assert report.rows[0].readonly is True

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="manual_escalation_score must be a Decimal"):
        observation("float-score", manual_escalation_score=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="dissenting_specialist_count must be integral"):
        observation("fractional-dissent", dissenting_specialist_count=d("1.5"))
    with pytest.raises(ValueError, match="reviewed_at must be UTC-aware"):
        observation("naive-review", reviewed_at=datetime(2026, 7, 8, 10, 0))
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        build_report(
            observation("zone-generated"),
            generated_at=datetime(
                2026,
                7,
                8,
                8,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        )
    with pytest.raises(ValueError, match="reviewed_at must not exceed"):
        build_report(
            observation(
                "future-review",
                reviewed_at=datetime(2026, 7, 8, 13, 0, tzinfo=UTC),
            ),
        )
    with pytest.raises(ValueError, match="completed_specialist_lanes"):
        build_report(
            observation(
                "unknown-lane",
                completed_specialist_lanes=("domain", "unlisted"),
            ),
        )
    with pytest.raises(ValueError, match="public aggregate label"):
        observation("market-slug-question")
    with pytest.raises(ValueError, match="duplicate"):
        build_report(
            observation("policy-catalyst-calendar"),
            observation("policy-catalyst-calendar"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchEventSpecialistReviewGapObservation(
            event_bucket="bad-flags",
            completed_specialist_lanes=module.SPECIALIST_REVIEW_LANES,
            reviewed_at=datetime(2026, 7, 8, 11, 0, tzinfo=UTC),
            dissenting_specialist_count=d("0"),
            evidence_coverage_ratio=d("0.950000"),
            manual_escalation_score=d("0.100000"),
            paper_only=False,
        )

    empty = build_report()
    assert empty.status == "pass"
    assert empty.reason_code_counts == (("specialist_review_gap_empty", d("1.000000")),)
    assert empty.event_bucket_count == d("0.000000")
    assert empty.rows == ()

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    forbidden_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "private_key",
        "wallet",
        "auth",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "recommendation",
        "sizing",
    )
    for fragment in forbidden_fragments:
        assert fragment not in lowered

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
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "http",
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


def _public_numeric_paths(value: object, prefix: str = "") -> tuple[str, ...]:
    if type(value) in (int, float, Decimal):
        return (prefix or "<root>",)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, nested in value.items():
            child = str(key) if not prefix else f"{prefix}.{key}"
            paths.extend(_public_numeric_paths(nested, child))
        return tuple(paths)
    if isinstance(value, list | tuple):
        paths = []
        for index, nested in enumerate(value):
            child = str(index) if not prefix else f"{prefix}.{index}"
            paths.extend(_public_numeric_paths(nested, child))
        return tuple(paths)
    return ()
