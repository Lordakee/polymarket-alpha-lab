from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_event_conflict_resolution_backlog as api
from polymarket_alpha_lab.research_event_conflict_resolution_backlog import (
    ResearchEventConflictResolutionBacklogConfig,
    ResearchEventConflictResolutionBacklogPublicPayloadItem,
    ResearchEventConflictResolutionBacklogReport,
    ResearchEventConflictResolutionBacklogRow,
    ResearchEventConflictResolutionBacklogSignal,
    build_research_event_conflict_resolution_backlog_report,
    research_event_conflict_resolution_backlog_payload,
)


NOW = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def _signal(
    *,
    review_key: str = "review_alpha",
    conflict_type: str = "evidence_conflict",
    conflict_count: Decimal = Decimal("1.000000"),
    severity_score: Decimal = Decimal("0.300000"),
    observed_at: datetime = NOW,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchEventConflictResolutionBacklogSignal:
    return ResearchEventConflictResolutionBacklogSignal(
        review_key=review_key,
        conflict_type=conflict_type,
        conflict_count=conflict_count,
        severity_score=severity_score,
        observed_at=observed_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    signals: tuple[ResearchEventConflictResolutionBacklogSignal, ...],
    *,
    config: ResearchEventConflictResolutionBacklogConfig | None = None,
    public_payload: tuple[ResearchEventConflictResolutionBacklogPublicPayloadItem, ...] = (),
) -> ResearchEventConflictResolutionBacklogReport:
    return build_research_event_conflict_resolution_backlog_report(
        signals,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_builds_pass_watch_and_block_public_statuses() -> None:
    report = _report(
        (
            _signal(
                review_key="review_pass",
                conflict_count=Decimal("0.000000"),
                severity_score=Decimal("0.000000"),
            ),
            _signal(review_key="review_watch", severity_score=Decimal("0.400000")),
            _signal(
                review_key="review_block",
                conflict_type="rule_ambiguity",
                conflict_count=Decimal("3.000000"),
                severity_score=Decimal("0.900000"),
            ),
        ),
    )

    rows = {row.review_key: row for row in report.rows}
    assert report.public_status == "block"
    assert report.review_count == Decimal("3.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert rows["review_pass"].public_status == "pass"
    assert rows["review_pass"].reason_codes == ("no_conflict_backlog",)
    assert rows["review_watch"].public_status == "watch"
    assert rows["review_watch"].reason_codes == (
        "evidence_conflict",
        "conflict_count_watch",
        "severity_watch",
    )
    assert rows["review_block"].public_status == "block"
    assert rows["review_block"].reason_codes == (
        "rule_ambiguity",
        "conflict_count_block",
        "severity_block",
    )
    for row in report.rows:
        assert row.paper_only is True
        assert row.report_only is True
        assert row.readonly is True


def test_rejects_non_decimal_numeric_inputs_and_bad_types() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        _signal(conflict_count=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Decimal"):
        _signal(severity_score=0.5)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="datetime"):
        _signal(observed_at="2026-07-08")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="known conflict type"):
        _signal(conflict_type="outcome_action")

    with pytest.raises(ValueError, match="sequence"):
        build_research_event_conflict_resolution_backlog_report(
            object(),  # type: ignore[arg-type]
            generated_at=NOW,
        )

    with pytest.raises(ValueError, match="after generated_at"):
        build_research_event_conflict_resolution_backlog_report(
            (
                _signal(
                    observed_at=NOW + timedelta(minutes=1),
                ),
            ),
            generated_at=NOW,
        )


def test_public_leak_terms_are_rejected_everywhere() -> None:
    unsafe_values = (
        "raw candidate id",
        "market id",
        "market_slug",
        "source url",
        "source text",
        "dsn token",
        "wallet field",
        "order field",
        "trade field",
        "position field",
        "buy signal",
        "sell signal",
        "recommendation",
        "settlement action",
        "live auth",
    )
    for value in unsafe_values:
        with pytest.raises(ValueError, match="unsafe public"):
            _signal(review_key=value.replace(" ", "_"))
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchEventConflictResolutionBacklogPublicPayloadItem("safe_key", value)

    for key in (
        "candidate_key",
        "market_key",
        "source_ref",
        "dsn_key",
        "table_key",
        "token_key",
        "wallet_key",
        "order_key",
        "trade_key",
        "position_key",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchEventConflictResolutionBacklogPublicPayloadItem(key, "safe value")


def test_hard_flags_are_enforced_and_dataclasses_are_frozen() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        ResearchEventConflictResolutionBacklogConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        _signal(conflict_count=Decimal("1.000000"), report_only=False)

    report = _report((_signal(),))
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    with pytest.raises(FrozenInstanceError):
        report.public_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadRow(ResearchEventConflictResolutionBacklogRow):
            pass

    assert api.__all__ == (
        "DEFAULT_RESEARCH_EVENT_CONFLICT_RESOLUTION_BACKLOG_CONFIG_VERSION",
        "ResearchEventConflictResolutionBacklogConfig",
        "ResearchEventConflictResolutionBacklogPublicPayloadItem",
        "ResearchEventConflictResolutionBacklogReport",
        "ResearchEventConflictResolutionBacklogRow",
        "ResearchEventConflictResolutionBacklogSignal",
        "build_research_event_conflict_resolution_backlog_report",
        "research_event_conflict_resolution_backlog_payload",
    )


def test_payload_and_digest_are_deterministic_and_json_ready() -> None:
    signal_a = _signal(
        review_key="review_beta",
        conflict_type="team_disagreement",
        conflict_count=Decimal("1.000000"),
        severity_score=Decimal("0.400000"),
    )
    signal_b = _signal(
        review_key="review_alpha",
        conflict_type="evidence_conflict",
        conflict_count=Decimal("2.000000"),
        severity_score=Decimal("0.700000"),
    )
    public_payload = (
        ResearchEventConflictResolutionBacklogPublicPayloadItem("summary", "manual review"),
        ResearchEventConflictResolutionBacklogPublicPayloadItem("owner", "research"),
    )

    report_a = _report((signal_a, signal_b), public_payload=public_payload)
    report_b = _report((signal_b, signal_a), public_payload=tuple(reversed(public_payload)))

    assert report_a.payload == report_b.payload
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert report_a.payload["rows"][0]["review_key"] == "review_alpha"
    assert report_a.payload["public_payload"][0]["key"] == "owner"
    assert report_a.payload["total_conflict_count"] == "3.000000"
    assert report_a.payload["max_severity_score"] == "0.700000"
    assert report_a.payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    json.dumps(report_a.payload, sort_keys=True)
    _assert_no_decimal_objects(report_a.payload)
    _assert_no_non_decimal_public_numbers(report_a)


def test_report_digest_rejects_tampering_and_payload_helper_matches() -> None:
    report = _report((_signal(),))

    assert research_event_conflict_resolution_backlog_payload(report) == report.payload
    assert len(report.derived_validation_digest) == 64

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="review_count"):
        replace(report, review_count=Decimal("2.000000"))

    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=())

    with pytest.raises(ValueError, match="report"):
        research_event_conflict_resolution_backlog_payload(object())  # type: ignore[arg-type]


def test_no_unsafe_public_surfaces_or_write_capabilities() -> None:
    unsafe_terms = (
        "candidate",
        "market",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        ResearchEventConflictResolutionBacklogConfig,
        ResearchEventConflictResolutionBacklogPublicPayloadItem,
        ResearchEventConflictResolutionBacklogReport,
        ResearchEventConflictResolutionBacklogRow,
        ResearchEventConflictResolutionBacklogSignal,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_terms)

    source = Path(api.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "request",
        "post",
        "put",
        "delete",
        "submit",
        "execute",
        "commit",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name):
                assert target.id not in forbidden_call_names
            if isinstance(target, ast.Attribute):
                assert target.attr not in forbidden_call_names


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
