from __future__ import annotations

import ast
import hashlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_event_resolution_timeline_confidence_ladder_report import (
    DEFAULT_RESEARCH_EVENT_RESOLUTION_TIMELINE_CONFIDENCE_LADDER_REPORT_CONFIG_VERSION,
    ResearchEventResolutionTimelineConfidenceLadderConfig,
    ResearchEventResolutionTimelineConfidenceLadderReport,
    ResearchEventResolutionTimelineInput,
    build_research_event_resolution_timeline_confidence_ladder_report,
    research_event_resolution_timeline_confidence_ladder_report_to_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def _checkpoint(
    checkpoint_alias: str,
    *,
    event_alias: str = "event_alpha",
    confirmation_count: Decimal = d("2.000000"),
    independent_evidence_count: Decimal = d("3.000000"),
    unresolved_dependency_count: Decimal = d("0.000000"),
    contradiction_count: Decimal = d("0.000000"),
    timeline_updated_at: datetime = GENERATED_AT - timedelta(minutes=30),
    expected_resolution_at: datetime = GENERATED_AT + timedelta(hours=8),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchEventResolutionTimelineInput:
    return ResearchEventResolutionTimelineInput(
        event_alias=event_alias,
        checkpoint_alias=checkpoint_alias,
        confirmation_count=confirmation_count,
        independent_evidence_count=independent_evidence_count,
        unresolved_dependency_count=unresolved_dependency_count,
        contradiction_count=contradiction_count,
        timeline_updated_at=timeline_updated_at,
        expected_resolution_at=expected_resolution_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _config(**overrides: object) -> ResearchEventResolutionTimelineConfidenceLadderConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_EVENT_RESOLUTION_TIMELINE_CONFIDENCE_LADDER_REPORT_CONFIG_VERSION
        ),
        "pass_threshold": d("0.700000"),
        "watch_threshold": d("0.400000"),
        "required_confirmation_count": d("2.000000"),
        "required_independent_evidence_count": d("3.000000"),
        "blocked_unresolved_dependency_count": d("3.000000"),
        "blocked_contradiction_count": d("2.000000"),
        "fresh_timeline_seconds": d("3600.000000"),
        "stale_timeline_seconds": d("21600.000000"),
        "deadline_pressure_window_seconds": d("7200.000000"),
        "confirmation_weight": d("0.250000"),
        "independent_evidence_weight": d("0.250000"),
        "recency_weight": d("0.200000"),
        "dependency_penalty_weight": d("0.200000"),
        "contradiction_penalty_weight": d("0.250000"),
        "overdue_penalty_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchEventResolutionTimelineConfidenceLadderConfig(**values)


def _report(
    *checkpoints: ResearchEventResolutionTimelineInput,
    config: ResearchEventResolutionTimelineConfidenceLadderConfig | None = None,
) -> ResearchEventResolutionTimelineConfidenceLadderReport:
    return build_research_event_resolution_timeline_confidence_ladder_report(
        checkpoints,
        config=config or _config(),
        generated_at=GENERATED_AT,
    )


def test_timeline_confidence_ladder_ranks_pass_watch_and_block_rows() -> None:
    report = _report(
        _checkpoint(
            "block_checkpoint",
            confirmation_count=d("1.000000"),
            independent_evidence_count=d("1.000000"),
            unresolved_dependency_count=d("3.000000"),
            contradiction_count=d("2.000000"),
            timeline_updated_at=GENERATED_AT - timedelta(hours=8),
            expected_resolution_at=GENERATED_AT - timedelta(minutes=15),
        ),
        _checkpoint(
            "watch_checkpoint",
            confirmation_count=d("2.000000"),
            independent_evidence_count=d("2.000000"),
            contradiction_count=d("1.000000"),
            expected_resolution_at=GENERATED_AT + timedelta(minutes=45),
        ),
        _checkpoint("pass_checkpoint"),
    )

    assert report.ladder_status == "block"
    assert report.checkpoint_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_confidence_score == d("0.422222")
    assert report.max_dependency_penalty == d("0.200000")
    assert report.max_contradiction_penalty == d("0.250000")
    assert report.min_seconds_until_expected_resolution == d("-900.000000")
    assert tuple(row.checkpoint_alias for row in report.rows) == (
        "block_checkpoint",
        "watch_checkpoint",
        "pass_checkpoint",
    )

    blocked, watched, passed = report.rows
    assert blocked.ladder_status == "block"
    assert blocked.confidence_score == d("0.000000")
    assert blocked.dependency_penalty == d("0.200000")
    assert blocked.contradiction_penalty == d("0.250000")
    assert blocked.overdue_penalty == d("0.150000")
    assert blocked.reason_codes == (
        "timeline_confidence_blocked_dependency_pressure",
        "timeline_confidence_blocked_contradiction_pressure",
        "timeline_confidence_confirmation_quorum_shortfall",
        "timeline_confidence_evidence_quorum_shortfall",
        "timeline_confidence_stale_update",
        "timeline_confidence_overdue_resolution",
    )

    assert watched.ladder_status == "watch"
    assert watched.confidence_score == d("0.566667")
    assert watched.reason_codes == (
        "timeline_confidence_watch_threshold",
        "timeline_confidence_evidence_quorum_shortfall",
        "timeline_confidence_deadline_pressure",
        "timeline_confidence_contradiction_pressure",
    )

    assert passed.ladder_status == "pass"
    assert passed.confidence_score == d("0.700000")
    assert passed.reason_codes == ("timeline_confidence_pass_threshold",)
    assert report.reason_codes == (
        "timeline_confidence_blocked_dependency_pressure",
        "timeline_confidence_blocked_contradiction_pressure",
        "timeline_confidence_watch_threshold",
        "timeline_confidence_pass_threshold",
        "timeline_confidence_confirmation_quorum_shortfall",
        "timeline_confidence_evidence_quorum_shortfall",
        "timeline_confidence_stale_update",
        "timeline_confidence_deadline_pressure",
        "timeline_confidence_overdue_resolution",
        "timeline_confidence_contradiction_pressure",
        "timeline_confidence_block_present",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_quorum_and_staleness_downgrade_otherwise_supported_checkpoint() -> None:
    report = _report(
        _checkpoint(
            "thin_checkpoint",
            confirmation_count=d("1.000000"),
            independent_evidence_count=d("2.000000"),
            timeline_updated_at=GENERATED_AT - timedelta(hours=3),
        ),
    )

    row = report.rows[0]
    assert row.ladder_status == "watch"
    assert row.confirmation_score == d("0.125000")
    assert row.independent_evidence_score == d("0.166667")
    assert row.recency_score == d("0.133333")
    assert row.confidence_score == d("0.425000")
    assert row.reason_codes == (
        "timeline_confidence_watch_threshold",
        "timeline_confidence_confirmation_quorum_shortfall",
        "timeline_confidence_evidence_quorum_shortfall",
    )
    assert report.ladder_status == "watch"


def test_public_payload_and_digest_are_deterministic_and_validated() -> None:
    forward = _report(
        _checkpoint("pass_checkpoint"),
        _checkpoint(
            "watch_checkpoint",
            independent_evidence_count=d("2.000000"),
            contradiction_count=d("1.000000"),
            expected_resolution_at=GENERATED_AT + timedelta(minutes=45),
        ),
    )
    reverse = _report(
        _checkpoint(
            "watch_checkpoint",
            independent_evidence_count=d("2.000000"),
            contradiction_count=d("1.000000"),
            expected_resolution_at=GENERATED_AT + timedelta(minutes=45),
        ),
        _checkpoint("pass_checkpoint"),
    )

    assert forward == reverse
    assert forward.derived_validation_digest == reverse.derived_validation_digest
    payload = research_event_resolution_timeline_confidence_ladder_report_to_payload(
        forward,
    )
    assert payload == forward.public_payload
    assert payload["derived_validation_digest"] == forward.derived_validation_digest
    assert payload["rows"][0]["confidence_score"] == "0.566667"

    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    canonical = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert hashlib.sha256(canonical.encode("utf-8")).hexdigest() == (
        forward.derived_validation_digest
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(forward, derived_validation_digest="0" * 64)

    with pytest.raises(FrozenInstanceError):
        forward.rows[0].confidence_score = d("0.000000")  # type: ignore[misc]


def test_public_payload_prevents_raw_identifier_and_sensitive_surface_leaks() -> None:
    report = _report(_checkpoint("pass_checkpoint", event_alias="safe_event_alias"))
    payload = report.public_payload
    rendered = repr(payload).lower()
    forbidden_terms = (
        _join_parts("candidate", "_", "id"),
        _join_parts("market", "_", "id"),
        _join_parts("market", "_", "slug"),
        _join_parts("que", "stion"),
        _join_parts("source", "_", "url"),
        _join_parts("source", "_", "text"),
        "dsn",
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
    )
    for term in forbidden_terms:
        assert term not in rendered

    for unsafe_value in (
        _join_parts("market", "_", "slug"),
        "https://example.invalid/evidence",
        _join_parts("source", "_", "text"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("to", "ken"),
    ):
        with pytest.raises(ValueError, match="unsafe public value"):
            _checkpoint("unsafe_value", event_alias=unsafe_value)

    with pytest.raises(ValueError, match="paper_only"):
        _checkpoint("unsafe_flags", paper_only=False)


def test_custom_config_validation_and_decimal_only_metrics() -> None:
    lenient = _config(pass_threshold=d("0.700000"), watch_threshold=d("0.400000"))
    lenient_report = _report(_checkpoint("passes_at_boundary"), config=lenient)

    assert lenient_report.ladder_status == "pass"
    assert lenient_report.rows[0].ladder_status == "pass"
    assert lenient_report.rows[0].confidence_score == d("0.700000")

    with pytest.raises(ValueError, match="pass_threshold"):
        _config(pass_threshold=d("0.400000"), watch_threshold=d("0.500000"))
    with pytest.raises(ValueError, match="required_confirmation_count"):
        _config(required_confirmation_count=2)
    with pytest.raises(ValueError, match="stale_timeline_seconds"):
        _config(fresh_timeline_seconds=d("3600.000000"), stale_timeline_seconds=d("3600.000000"))
    with pytest.raises(ValueError, match="readonly"):
        _config(readonly=False)

    report_metric_names = (
        "checkpoint_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_confidence_score",
        "max_dependency_penalty",
        "max_contradiction_penalty",
        "min_seconds_until_expected_resolution",
    )
    for name in report_metric_names:
        value = getattr(lenient_report, name)
        if value is not None:
            assert type(value) is Decimal

    row_metric_names = (
        "confirmation_score",
        "independent_evidence_score",
        "recency_score",
        "dependency_penalty",
        "contradiction_penalty",
        "overdue_penalty",
        "seconds_since_timeline_update",
        "seconds_until_expected_resolution",
        "confidence_score",
    )
    for name in row_metric_names:
        value = getattr(lenient_report.rows[0], name)
        assert type(value) is Decimal


def test_module_has_no_external_action_or_sensitive_surfaces() -> None:
    import polymarket_alpha_lab.research_event_resolution_timeline_confidence_ladder_report as api

    source = inspect.getsource(api).lower()
    tree = ast.parse(source)

    assert "float(" not in source
    assert ".total_seconds(" not in source
    for token in (
        _join_parts("data", "base"),
        _join_parts("net", "work"),
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("siz", "ing"),
        _join_parts("recomm", "end"),
    ):
        assert token not in source

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
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
                "delete",
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

    exposed_names = {field.name for field in fields(ResearchEventResolutionTimelineConfidenceLadderReport)}
    assert _join_parts("candidate", "_", "id") not in exposed_names
    assert _join_parts("market", "_", "id") not in exposed_names
    assert _join_parts("market", "_", "slug") not in exposed_names
    assert _join_parts("que", "stion") not in exposed_names
