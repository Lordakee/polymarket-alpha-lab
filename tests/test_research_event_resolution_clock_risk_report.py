from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)


def _api():
    return import_module(
        "polymarket_alpha_lab.research_event_resolution_clock_risk_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object):
    api = _api()
    values = {
        "config_version": "research-event-resolution-clock-risk-report-v0",
        "near_deadline_window_seconds_threshold": d("3600.000000"),
        "stale_evidence_age_seconds_threshold": d("14400.000000"),
        "watch_clock_risk_score_threshold": d("0.250000"),
        "block_clock_risk_score_threshold": d("0.600000"),
    }
    values.update(overrides)
    return api.ResearchEventResolutionClockRiskConfig(**values)


def _snapshot(
    *,
    event_count: Decimal = d("5"),
    resolution_deadline_at: datetime = GENERATED_AT + timedelta(minutes=30),
    evidence_observed_at: datetime = GENERATED_AT - timedelta(hours=7),
    rule_ambiguity_score: Decimal = d("0.800000"),
    pending_source_count: Decimal = d("4"),
):
    api = _api()
    return api.ResearchEventResolutionClockRiskSnapshot(
        event_count=event_count,
        resolution_deadline_at=resolution_deadline_at,
        evidence_observed_at=evidence_observed_at,
        rule_ambiguity_score=rule_ambiguity_score,
        pending_source_count=pending_source_count,
    )


def _report(snapshots: tuple[object, ...], *, generated_at: datetime = GENERATED_AT):
    api = _api()
    return api.build_research_event_resolution_clock_risk_report(
        snapshots,
        config=_config(),
        generated_at=generated_at,
    )


def test_report_aggregates_resolution_clock_risk_without_raw_event_surfaces():
    api = _api()
    report = _report(
        (
            _snapshot(),
            _snapshot(
                event_count=d("2"),
                resolution_deadline_at=GENERATED_AT + timedelta(hours=3),
                evidence_observed_at=GENERATED_AT - timedelta(hours=1),
                rule_ambiguity_score=d("0.200000"),
                pending_source_count=d("1"),
            ),
            _snapshot(
                event_count=d("1"),
                resolution_deadline_at=GENERATED_AT + timedelta(days=1),
                evidence_observed_at=GENERATED_AT - timedelta(minutes=10),
                rule_ambiguity_score=d("0.000000"),
                pending_source_count=d("0"),
            ),
        ),
    )

    assert type(report) is api.ResearchEventResolutionClockRiskReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "research-event-resolution-clock-risk-report-v0"
    assert report.snapshot_count == d("3")
    assert report.event_count == d("8")
    assert report.near_deadline_event_count == d("5")
    assert report.stale_evidence_event_count == d("5")
    assert report.pending_source_count == d("5")
    assert report.min_deadline_window_seconds == d("1800.000000")
    assert report.max_evidence_age_seconds == d("25200.000000")
    assert report.max_rule_ambiguity_score == d("0.800000")
    assert report.deadline_proximity_ratio == d("0.625000")
    assert report.evidence_staleness_ratio == d("0.625000")
    assert report.rule_ambiguity_ratio == d("0.550000")
    assert report.pending_source_pressure_ratio == d("0.625000")
    assert report.clock_risk_score == d("0.606250")
    assert report.status == "block"
    assert report.reason_codes == (
        "resolution_deadline_pressure_present",
        "evidence_freshness_gap_present",
        "rule_ambiguity_present",
        "pending_source_pressure_present",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = api.research_event_resolution_clock_risk_payload(report)
    serialized = api.serialize_research_event_resolution_clock_risk_payload(report)
    assert serialized == json.dumps(payload, sort_keys=True, separators=(",", ":"))
    assert api.research_event_resolution_clock_risk_payload_digest(payload) == (
        report.derived_validation_digest
    )
    _assert_no_floats(payload)
    _assert_no_raw_event_surfaces(payload)


def test_payload_digest_and_report_only_guards_are_deterministic():
    api = _api()
    clear = _report(
        (
            _snapshot(
                event_count=d("4"),
                resolution_deadline_at=GENERATED_AT + timedelta(days=1),
                evidence_observed_at=GENERATED_AT - timedelta(minutes=20),
                rule_ambiguity_score=d("0.000000"),
                pending_source_count=d("0"),
            ),
        ),
    )

    assert clear.status == "pass"
    assert clear.reason_codes == ("resolution_clock_risk_clear",)
    assert type(clear.derived_validation_digest) is str
    assert len(clear.derived_validation_digest) == 64
    assert int(clear.derived_validation_digest, 16) >= 0
    assert _report(clear.source_snapshots).derived_validation_digest == (
        clear.derived_validation_digest
    )

    with pytest.raises(FrozenInstanceError):
        clear.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(clear, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="paper_only"):
        replace(_config(), paper_only=False)
    with pytest.raises(ValueError, match="Decimal"):
        _snapshot(event_count=4)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="timezone-aware"):
        _snapshot(evidence_observed_at=datetime(2026, 7, 8, 17, 0))
    with pytest.raises(ValueError, match="after generated_at"):
        _report(
            (
                _snapshot(
                    evidence_observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="pending_source_count"):
        _snapshot(event_count=d("1"), pending_source_count=d("2"))

    payload = api.research_event_resolution_clock_risk_payload(clear)
    assert payload["event_count"] == "4"
    assert payload["clock_risk_score"] == "0.000000"
    assert payload["source_snapshots"][0]["event_count"] == "4"
    assert payload["derived_validation_digest"] == clear.derived_validation_digest
    assert api.research_event_resolution_clock_risk_payload(payload) == payload
    assert api.serialize_research_event_resolution_clock_risk_payload(payload) == (
        json.dumps(payload, sort_keys=True, separators=(",", ":"))
    )

    with pytest.raises(ValueError, match="paper_only"):
        api.research_event_resolution_clock_risk_payload(
            {**payload, "paper_only": False},
        )
    with pytest.raises(ValueError, match="Decimal-derived"):
        api.research_event_resolution_clock_risk_payload({**payload, "event_count": 4})
    with pytest.raises(ValueError, match="float"):
        api.research_event_resolution_clock_risk_payload(
            {**payload, "clock_risk_score": 0.1},
        )
    with pytest.raises(ValueError, match="unsafe"):
        api.research_event_resolution_clock_risk_payload(
            {**payload, "market_slug": "raw-slug"},
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.research_event_resolution_clock_risk_payload(
            {**payload, "status": "watch"},
        )

    raw_surface_fragments = (
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "raw_text",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "size",
        "recommend",
    )
    for cls in (
        api.ResearchEventResolutionClockRiskConfig,
        api.ResearchEventResolutionClockRiskSnapshot,
        api.ResearchEventResolutionClockRiskReport,
    ):
        for field in fields(cls):
            assert not any(fragment in field.name for fragment in raw_surface_fragments)

    tree = ast.parse(Path(api.__file__).read_text())
    imported_modules = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_modules.update(
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    assert not (
        imported_modules
        & {
            "ccxt",
            "httpx",
            "psycopg",
            "requests",
            "socket",
            "sqlite3",
            "sqlalchemy",
            "web3",
        }
    )


def _assert_no_floats(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"float leaked into payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_floats(item)


def _assert_no_raw_event_surfaces(payload: dict[str, Any]) -> None:
    raw_surface_fragments = (
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "raw_text",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "size",
        "recommend",
    )

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                assert not any(fragment in key.lower() for fragment in raw_surface_fragments)
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, str):
            assert not any(
                fragment in value.lower() for fragment in raw_surface_fragments
            )

    visit(payload)
