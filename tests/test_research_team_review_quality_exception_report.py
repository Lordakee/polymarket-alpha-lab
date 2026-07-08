from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 14, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_review_quality_exception_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_review_quality_exception_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_TEAM_REVIEW_QUALITY_EXCEPTION_REPORT_CONFIG_VERSION
        ),
        "late_review_block_seconds": d("86400.000000"),
        "min_rationale_watch_score": d("0.700000"),
        "min_rationale_block_score": d("0.400000"),
        "memory_writeback_block_seconds": d("172800.000000"),
        "manual_escalation_watch_seconds": d("7200.000000"),
    }
    values.update(overrides)
    return module.ResearchTeamReviewQualityExceptionConfig(**values)


def snapshot(**overrides: object):
    module = api()
    values = {
        "review_reference": "review-alpha-private-market-source-id",
        "team_key": "macro_review",
        "review_due_at": GENERATED_AT - timedelta(hours=2),
        "reviewed_at": GENERATED_AT - timedelta(hours=1),
        "primary_outcome": "pass",
        "secondary_outcome": "pass",
        "rationale_score": d("0.900000"),
        "memory_writeback_completed": True,
        "manual_escalation_required": False,
        "manual_escalation_due_at": None,
    }
    values.update(overrides)
    return module.ResearchTeamReviewQualitySnapshot(**values)


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_review_quality_exception_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected numeric shortcut {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if isinstance(value, datetime):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def assert_payload_has_no_forbidden_surface(value: object) -> None:
    forbidden = (
        "raw",
        "event",
        "market",
        "source",
        "question",
        "slug",
        "url",
        "dsn",
        "table",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "sizing",
        "position",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lower_key = str(key).lower()
            assert not any(fragment in lower_key for fragment in forbidden), lower_key
            assert_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, str):
        lower_value = value.lower()
        assert not any(fragment in lower_value for fragment in forbidden), lower_value


def test_public_api_declares_report_only_exception_contract() -> None:
    module = api()

    assert module.DEFAULT_RESEARCH_TEAM_REVIEW_QUALITY_EXCEPTION_REPORT_CONFIG_VERSION == (
        "research-team-review-quality-exception-report-v0"
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_REVIEW_QUALITY_EXCEPTION_REPORT_CONFIG_VERSION",
        "ResearchTeamReviewQualityExceptionConfig",
        "ResearchTeamReviewQualityExceptionReasonCodeCount",
        "ResearchTeamReviewQualityExceptionReport",
        "ResearchTeamReviewQualityExceptionRow",
        "ResearchTeamReviewQualitySnapshot",
        "build_research_team_review_quality_exception_report",
        "research_team_review_quality_exception_report_digest",
        "research_team_review_quality_exception_report_payload",
    )

    for public_type in (
        module.ResearchTeamReviewQualityExceptionConfig,
        module.ResearchTeamReviewQualityExceptionReasonCodeCount,
        module.ResearchTeamReviewQualityExceptionReport,
        module.ResearchTeamReviewQualityExceptionRow,
        module.ResearchTeamReviewQualitySnapshot,
    ):
        assert is_dataclass(public_type)
        defaults = {field.name: field.default for field in fields(public_type)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True


def test_aggregates_late_rationale_conflict_memory_and_escalation_exceptions() -> None:
    result = report(
        snapshot(
            review_reference="pass-private-market-source-ref",
            team_key="macro_review",
        ),
        snapshot(
            review_reference="watch-private-market-source-ref",
            team_key="policy_review",
            review_due_at=GENERATED_AT - timedelta(hours=3),
            reviewed_at=GENERATED_AT - timedelta(hours=1),
            primary_outcome="watch",
            secondary_outcome="watch",
            rationale_score=d("0.600000"),
            memory_writeback_completed=False,
            manual_escalation_required=True,
            manual_escalation_due_at=GENERATED_AT + timedelta(hours=1),
        ),
        snapshot(
            review_reference="block-private-market-source-ref",
            team_key="sports_review",
            review_due_at=GENERATED_AT - timedelta(days=3),
            reviewed_at=None,
            primary_outcome="pass",
            secondary_outcome="block",
            rationale_score=d("0.300000"),
            memory_writeback_completed=False,
            manual_escalation_required=True,
            manual_escalation_due_at=GENERATED_AT - timedelta(hours=1),
        ),
    )

    assert result.generated_at == GENERATED_AT
    assert result.review_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.late_review_count == d("2.000000")
    assert result.missing_rationale_count == d("2.000000")
    assert result.conflicting_outcome_count == d("1.000000")
    assert result.memory_writeback_omission_count == d("2.000000")
    assert result.manual_escalation_urgent_count == d("2.000000")
    assert result.max_late_review_seconds == d("259200.000000")
    assert result.max_memory_writeback_age_seconds == d("259200.000000")
    assert result.max_manual_escalation_urgency_score == d("1.000000")
    assert result.status == "block"
    assert result.reason_codes == (
        "review_quality_exception_late_block",
        "review_quality_exception_rationale_block",
        "review_quality_exception_outcome_conflict_block",
        "review_quality_exception_memory_writeback_block",
        "review_quality_exception_manual_escalation_block",
        "review_quality_exception_late_watch",
        "review_quality_exception_rationale_watch",
        "review_quality_exception_memory_writeback_watch",
        "review_quality_exception_manual_escalation_watch",
    )

    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    blocked, watched, passed = result.rows

    assert blocked.team_key == "sports_review"
    assert blocked.late_review_seconds == d("259200.000000")
    assert blocked.rationale_score == d("0.300000")
    assert blocked.outcome_conflict_count == d("1.000000")
    assert blocked.memory_writeback_omission_count == d("1.000000")
    assert blocked.memory_writeback_age_seconds == d("259200.000000")
    assert blocked.manual_escalation_urgency_score == d("1.000000")
    assert blocked.reason_codes == (
        "review_quality_exception_late_block",
        "review_quality_exception_rationale_block",
        "review_quality_exception_outcome_conflict_block",
        "review_quality_exception_memory_writeback_block",
        "review_quality_exception_manual_escalation_block",
    )

    assert watched.team_key == "policy_review"
    assert watched.late_review_seconds == d("7200.000000")
    assert watched.memory_writeback_age_seconds == d("3600.000000")
    assert watched.manual_escalation_due_in_seconds == d("3600.000000")
    assert watched.manual_escalation_urgency_score == d("0.500000")
    assert watched.reason_codes == (
        "review_quality_exception_late_watch",
        "review_quality_exception_rationale_watch",
        "review_quality_exception_memory_writeback_watch",
        "review_quality_exception_manual_escalation_watch",
    )

    assert passed.status == "pass"
    assert passed.reason_codes == ("review_quality_exception_pass",)
    assert all(row.paper_only and row.report_only and row.readonly for row in result.rows)


def test_empty_input_is_report_only_pass_diagnostic() -> None:
    result = report()

    assert result.review_count == d("0.000000")
    assert result.pass_count == d("0.000000")
    assert result.watch_count == d("0.000000")
    assert result.block_count == d("0.000000")
    assert result.status == "pass"
    assert result.reason_codes == ("review_quality_exception_report_empty",)
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_payload_and_digest_are_deterministic_decimal_stringed_and_redacted() -> None:
    left = snapshot(review_reference="left-private-market-source", team_key="policy_review")
    right = snapshot(review_reference="right-private-market-source", team_key="macro_review")

    report_a = report(right, left)
    report_b = report(left, right)
    payload_a = report_a.payload
    payload_b = report_b.payload

    assert payload_a == payload_b
    assert report_a.public_digest == report_b.public_digest
    assert report_a.public_digest == payload_a["public_digest"]
    assert report_a.public_digest == api().research_team_review_quality_exception_report_digest(
        report_a,
    )
    assert payload_a["generated_at"] == "2026-07-08T14:00:00+00:00"
    assert payload_a["review_count"] == "2.000000"
    assert payload_a["rows"][0]["review_marker"].startswith("review_marker_")
    assert payload_a["rows"][0]["late_review_seconds"] == "3600.000000"
    assert_no_int_or_float_values(payload_a)
    json.dumps(payload_a, sort_keys=True)

    rendered = json.dumps(payload_a, sort_keys=True).lower()
    for forbidden in (
        "left-private",
        "right-private",
        "market",
        "source",
        "wallet",
        "auth",
        "order",
        "trade",
        "sizing",
        "recommendation",
    ):
        assert forbidden not in rendered
        assert forbidden not in repr(report_a).lower()
    assert_payload_has_no_forbidden_surface(payload_a)


def test_payload_rejects_digest_tampering_and_unsafe_public_fields() -> None:
    module = api()
    result = report(snapshot())

    tampered = dict(result.payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="public_digest must match payload fields"):
        module.research_team_review_quality_exception_report_payload(tampered)

    unsafe = dict(result.payload)
    unsafe["market_reference"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_team_review_quality_exception_report_payload(unsafe)

    with pytest.raises(ValueError, match="unsafe private reference"):
        snapshot(review_reference="https://example.com/private")


@pytest.mark.parametrize(
    ("factory", "message"),
    (
        (
            lambda: config(late_review_block_seconds=86400),
            "late_review_block_seconds must be exactly Decimal",
        ),
        (
            lambda: config(min_rationale_watch_score=_DecimalSubclass("0.700000")),
            "min_rationale_watch_score must be exactly Decimal",
        ),
        (
            lambda: config(min_rationale_block_score=d("0.700000")),
            "min_rationale_block_score must be less than min_rationale_watch_score",
        ),
        (
            lambda: snapshot(rationale_score=0.9),
            "rationale_score must be exactly Decimal",
        ),
        (
            lambda: snapshot(rationale_score=d("0.9000001")),
            "rationale_score must use six decimal places or fewer",
        ),
        (
            lambda: snapshot(reviewed_at=datetime(2026, 7, 8, 13, 0)),
            "reviewed_at must be timezone-aware",
        ),
        (
            lambda: snapshot(
                review_due_at=_DatetimeSubclass(2026, 7, 8, 11, 0, tzinfo=UTC),
            ),
            "review_due_at must be exactly datetime",
        ),
        (
            lambda: snapshot(
                manual_escalation_required=True,
                manual_escalation_due_at=None,
            ),
            "manual_escalation_due_at is required",
        ),
        (
            lambda: report(snapshot(), generated_at=datetime(2026, 7, 8, 14, 0)),
            "generated_at must be timezone-aware",
        ),
        (
            lambda: snapshot(memory_writeback_completed=1),
            "memory_writeback_completed must be a bool",
        ),
        (
            lambda: snapshot(primary_outcome="blocked"),
            "primary_outcome must be pass, watch, or block",
        ),
    ),
)
def test_strict_type_validation_rejects_numeric_time_and_status_shortcuts(
    factory: Any,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        factory()


def test_hard_flags_frozen_dataclasses_and_report_consistency() -> None:
    module = api()
    cfg = config()
    item = snapshot()
    result = report(item)
    row = result.rows[0]
    count = result.reason_code_counts[0]

    for value in (cfg, item, row, count, result):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        assert_public_numeric_values_are_decimal(value)

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.ResearchTeamReviewQualityExceptionConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(item, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="pass_count must match rows"):
        replace(result, pass_count=d("0.000000"))
    with pytest.raises(ValueError, match="rows must be sorted"):
        replace(result, rows=tuple(reversed(result.rows + result.rows)))


def test_module_stays_pure_report_only_without_io_or_execution_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_names: set[str] = set()
    call_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_names.add(node.module.split(".")[0])
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            if isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)

    assert imported_names.isdisjoint(
        {
            "httpx",
            "requests",
            "socket",
            "urllib",
            "psycopg",
            "psycopg2",
            "supabase",
            "sqlalchemy",
            "sqlite3",
            "web3",
            "py_clob_client",
        },
    )
    assert call_names.isdisjoint(
        {
            "connect",
            "request",
            "get",
            "post",
            "put",
            "patch",
            "delete",
            "execute",
            "executemany",
            "send",
            "submit",
            "insert",
            "upsert",
            "order",
            "trade",
            "buy",
            "sell",
        },
    )
