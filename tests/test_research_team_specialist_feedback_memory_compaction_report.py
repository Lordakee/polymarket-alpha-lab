from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_team_specialist_feedback_memory_compaction_report.py",
)
SHA_A = "sha256:" + ("a" * 64)
SHA_B = "sha256:" + ("b" * 64)
SHA_C = "sha256:" + ("c" * 64)


class _DecimalSubclass(Decimal):
    pass


def api():
    return import_module(
        "polymarket_alpha_lab.research_team_specialist_feedback_memory_compaction_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "min_pass_feedback_absorption_ratio": d("0.800000"),
        "min_watch_feedback_absorption_ratio": d("0.500000"),
        "calibration_watch_age_seconds": d("604800.000000"),
        "calibration_block_age_seconds": d("2592000.000000"),
        "recurrence_watch_count": d("2"),
        "recurrence_block_count": d("5"),
        "recurrence_penalty_per_error": d("0.200000"),
        "min_pass_evidence_reuse_ratio": d("0.750000"),
        "min_watch_evidence_reuse_ratio": d("0.500000"),
        "review_latency_pass_seconds": d("86400.000000"),
        "review_latency_watch_seconds": d("172800.000000"),
        "review_latency_block_seconds": d("604800.000000"),
        "quality_pass_threshold": d("0.750000"),
        "quality_watch_threshold": d("0.500000"),
        "feedback_absorption_weight": d("0.250000"),
        "calibration_freshness_weight": d("0.200000"),
        "error_recurrence_weight": d("0.200000"),
        "evidence_reuse_weight": d("0.200000"),
        "review_latency_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchTeamSpecialistFeedbackMemoryCompactionConfig(**values)


def memory_item(
    team_ref: str,
    specialist_ref: str,
    feedback_memory_digest: str,
    **overrides: object,
):
    module = api()
    values = {
        "team_ref": team_ref,
        "specialist_ref": specialist_ref,
        "feedback_memory_digest": feedback_memory_digest,
        "feedback_absorption_ratio": d("0.950000"),
        "calibration_refreshed_at": GENERATED_AT - timedelta(days=1),
        "recurring_error_count": d("0"),
        "evidence_reuse_ratio": d("0.900000"),
        "feedback_received_at": GENERATED_AT - timedelta(hours=1),
        "review_completed_at": GENERATED_AT,
        "sanitized_feedback_confirmed": True,
    }
    values.update(overrides)
    return module.ResearchTeamSpecialistFeedbackMemoryCompactionInput(**values)


def build_report(
    *items: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_research_team_specialist_feedback_memory_compaction_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_decimal_only_numerics(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_decimal_only_numerics(getattr(value, field.name))
        return
    if type(value) is dict:
        for item in value.values():
            assert_decimal_only_numerics(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            assert_decimal_only_numerics(item)


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_float_values(item)
    if type(value) in (list, tuple):
        for item in value:
            assert_no_float_values(item)


def test_compacts_specialist_feedback_into_memory_quality_rows() -> None:
    module = api()
    passing = memory_item("team-alpha", "specialist-macro", SHA_A)
    watched = memory_item(
        "team-alpha",
        "specialist-rates",
        SHA_B,
        feedback_absorption_ratio=d("0.650000"),
        calibration_refreshed_at=GENERATED_AT - timedelta(days=14),
        recurring_error_count=d("2"),
        evidence_reuse_ratio=d("0.650000"),
        feedback_received_at=GENERATED_AT - timedelta(days=3),
    )
    blocked = memory_item(
        "team-beta",
        "specialist-weather",
        SHA_C,
        feedback_absorption_ratio=d("0.300000"),
        calibration_refreshed_at=GENERATED_AT - timedelta(days=45),
        recurring_error_count=d("5"),
        evidence_reuse_ratio=d("0.200000"),
        feedback_received_at=GENERATED_AT - timedelta(days=10),
    )

    report = build_report(watched, passing, blocked)

    assert type(report) is module.ResearchTeamSpecialistFeedbackMemoryCompactionReport
    assert is_dataclass(report)
    assert module.RESEARCH_TEAM_SPECIALIST_FEEDBACK_MEMORY_COMPACTION_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert report.status == "block"
    assert report.feedback_memory_count == d("3")
    assert report.row_count == d("3")
    assert report.specialist_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.absorption_gap_count == d("2")
    assert report.stale_calibration_count == d("2")
    assert report.recurrence_penalty_count == d("2")
    assert report.low_evidence_reuse_count == d("2")
    assert report.review_latency_breach_count == d("2")
    assert report.average_long_term_memory_quality_score == d("0.562460")
    assert report.reason_codes == (
        "feedback_absorption_block",
        "feedback_absorption_watch",
        "calibration_freshness_block",
        "calibration_freshness_watch",
        "error_recurrence_block",
        "error_recurrence_watch",
        "evidence_reuse_block",
        "evidence_reuse_watch",
        "review_latency_block",
        "review_latency_watch",
        "feedback_memory_compaction_block",
        "feedback_memory_compaction_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    blocked_row, watched_row, passing_row = report.rows
    assert (blocked_row.team_ref, blocked_row.specialist_ref) == (
        "team-beta",
        "specialist-weather",
    )
    assert blocked_row.calibration_age_seconds == d("3888000.000000")
    assert blocked_row.review_latency_seconds == d("864000.000000")
    assert blocked_row.calibration_freshness_score == d("0.000000")
    assert blocked_row.error_recurrence_score == d("0.000000")
    assert blocked_row.review_latency_score == d("0.000000")
    assert blocked_row.long_term_memory_quality_score == d("0.115000")
    assert blocked_row.row_status == "block"
    assert blocked_row.reason_codes == (
        "feedback_absorption_block",
        "calibration_freshness_block",
        "error_recurrence_block",
        "evidence_reuse_block",
        "review_latency_block",
        "feedback_memory_compaction_block",
    )

    assert watched_row.calibration_age_seconds == d("1209600.000000")
    assert watched_row.review_latency_seconds == d("259200.000000")
    assert watched_row.calibration_freshness_score == d("0.533333")
    assert watched_row.error_recurrence_score == d("0.600000")
    assert watched_row.review_latency_score == d("0.571429")
    assert watched_row.long_term_memory_quality_score == d("0.604881")
    assert watched_row.row_status == "watch"
    assert passing_row.long_term_memory_quality_score == d("0.967500")
    assert passing_row.row_status == "pass"
    assert_decimal_only_numerics(report)


def test_recurring_error_penalties_lower_status_independently() -> None:
    clean = build_report(memory_item("team-alpha", "specialist-clean", SHA_A)).rows[0]
    watched = build_report(
        memory_item(
            "team-alpha",
            "specialist-watch",
            SHA_B,
            recurring_error_count=d("2"),
        ),
    ).rows[0]
    blocked = build_report(
        memory_item(
            "team-alpha",
            "specialist-block",
            SHA_C,
            recurring_error_count=d("5"),
        ),
    ).rows[0]

    assert clean.error_recurrence_score == d("1.000000")
    assert clean.row_status == "pass"
    assert watched.error_recurrence_score == d("0.600000")
    assert watched.long_term_memory_quality_score == d("0.887500")
    assert watched.row_status == "watch"
    assert "error_recurrence_watch" in watched.reason_codes
    assert blocked.error_recurrence_score == d("0.000000")
    assert blocked.long_term_memory_quality_score == d("0.767500")
    assert blocked.row_status == "block"
    assert "error_recurrence_block" in blocked.reason_codes


def test_public_payload_digest_is_deterministic_and_tamper_evident() -> None:
    module = api()
    first = memory_item("team-alpha", "specialist-macro", SHA_A)
    second = memory_item("team-alpha", "specialist-rates", SHA_B)

    report_a = build_report(second, first)
    report_b = build_report(first, second)
    payload = module.research_team_specialist_feedback_memory_compaction_report_payload(
        report_a,
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert report_a.rows == report_b.rows
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert payload == report_a.public_payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["feedback_memory_count"] == "2"
    assert payload["rows"][0]["long_term_memory_quality_score"] == "0.967500"
    assert payload["rows"][0]["derived_validation_digest"] == (
        report_a.rows[0].derived_validation_digest
    )
    assert payload["derived_validation_digest"] == report_a.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)
    json.loads(encoded)

    tampered = json.loads(json.dumps(payload))
    tampered["rows"][0]["long_term_memory_quality_score"] = "0.000001"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_specialist_feedback_memory_compaction_report_payload(tampered)

    object.__setattr__(
        report_a.rows[0],
        "long_term_memory_quality_score",
        d("0.000001"),
    )
    with pytest.raises(ValueError, match="derived_validation_digest|tamper"):
        module.research_team_specialist_feedback_memory_compaction_report_payload(
            report_a,
        )


def test_public_payload_rejects_identifier_and_execution_leaks() -> None:
    module = api()
    report = build_report(memory_item("team-alpha", "specialist-macro", SHA_A))
    payload_text = json.dumps(report.public_payload, sort_keys=True).lower()

    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "postgres://",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "trading",
        "sizing",
        "recommend",
    ):
        assert forbidden not in payload_text

    with pytest.raises(ValueError, match="public-safe|unsafe public"):
        memory_item("candidate_id", "specialist-macro", SHA_A)
    with pytest.raises(ValueError, match="public-safe|unsafe public"):
        memory_item("team-alpha", "https://example.test/raw", SHA_A)
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_team_specialist_feedback_memory_compaction_report_payload(
            {
                "market_id": "raw",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )

    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "source_url",
        "source_text",
        "postgres://",
        "table_name",
        "private_token",
        "wallet",
        "order",
        "trade",
        "live trading",
        "sizing",
        "recommendation",
    ):
        assert forbidden not in source

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "send",
        "write",
        "write_text",
        "write_bytes",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls


def test_frozen_dataclasses_decimal_only_and_custom_config_validation() -> None:
    module = api()
    custom = config(
        review_latency_pass_seconds=d("43200.000000"),
        review_latency_watch_seconds=d("86400.000000"),
        review_latency_block_seconds=d("345600.000000"),
    )
    report = build_report(
        memory_item("team-alpha", "specialist-macro", SHA_A),
        cfg=custom,
    )

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_SPECIALIST_FEEDBACK_MEMORY_COMPACTION_REPORT_CONFIG_VERSION",
        "RESEARCH_TEAM_SPECIALIST_FEEDBACK_MEMORY_COMPACTION_STATUSES",
        "RESEARCH_TEAM_SPECIALIST_FEEDBACK_MEMORY_COMPACTION_REASON_CODES",
        "ResearchTeamSpecialistFeedbackMemoryCompactionConfig",
        "ResearchTeamSpecialistFeedbackMemoryCompactionInput",
        "ResearchTeamSpecialistFeedbackMemoryCompactionReport",
        "ResearchTeamSpecialistFeedbackMemoryCompactionRow",
        "build_research_team_specialist_feedback_memory_compaction_report",
        "research_team_specialist_feedback_memory_compaction_report_payload",
    )
    for item in (custom, report, report.rows[0]):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert_decimal_only_numerics(item)

    with pytest.raises(ValueError, match="feedback_absorption_weight"):
        config(feedback_absorption_weight=0.25)
    with pytest.raises(ValueError, match="calibration_freshness_weight"):
        config(calibration_freshness_weight=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="weights must sum"):
        config(review_latency_weight=d("0.140000"))
    with pytest.raises(ValueError, match="min_pass_feedback_absorption_ratio"):
        config(min_pass_feedback_absorption_ratio=d("0.500000"))
    with pytest.raises(ValueError, match="calibration_block_age_seconds"):
        config(calibration_block_age_seconds=d("604800.000000"))
    with pytest.raises(ValueError, match="review_latency_block_seconds"):
        config(review_latency_block_seconds=d("172800.000000"))
    with pytest.raises(ValueError, match="quality_pass_threshold"):
        config(quality_pass_threshold=d("0.500000"))
    with pytest.raises(ValueError, match="readonly"):
        replace(custom, readonly=False)
    with pytest.raises(ValueError, match="sanitized_feedback_confirmed"):
        memory_item(
            "team-alpha",
            "specialist-macro",
            SHA_A,
            sanitized_feedback_confirmed=False,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            memory_item(
                "team-alpha",
                "specialist-macro",
                SHA_A,
                review_completed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            memory_item("team-alpha", "specialist-macro", SHA_A),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
