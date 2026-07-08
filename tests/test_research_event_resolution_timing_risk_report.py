from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)


def _api():
    return import_module(
        "polymarket_alpha_lab.research_event_resolution_timing_risk_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object):
    api = _api()
    values = {
        "config_version": "research-event-resolution-timing-risk-report-v0",
        "stale_evidence_age_seconds_threshold": d("14400"),
        "near_resolution_window_seconds_threshold": d("3600"),
        "source_refresh_lag_seconds_threshold": d("10800"),
        "watch_timing_risk_score_threshold": d("0.250000"),
        "block_timing_risk_score_threshold": d("0.650000"),
    }
    values.update(overrides)
    return api.ResearchEventResolutionTimingRiskConfig(**values)


def _snapshot(
    *,
    event_count: Decimal = d("5"),
    evidence_observed_at: datetime = GENERATED_AT - timedelta(hours=7),
    nearest_resolution_at: datetime = GENERATED_AT + timedelta(minutes=45),
    source_refreshed_at: datetime = GENERATED_AT - timedelta(hours=5),
    ambiguous_event_count: Decimal = d("4"),
    recheck_due_count: Decimal = d("5"),
):
    api = _api()
    return api.ResearchEventResolutionTimingRiskSnapshot(
        event_count=event_count,
        evidence_observed_at=evidence_observed_at,
        nearest_resolution_at=nearest_resolution_at,
        source_refreshed_at=source_refreshed_at,
        ambiguous_event_count=ambiguous_event_count,
        recheck_due_count=recheck_due_count,
    )


def _report(snapshots: tuple[object, ...], *, generated_at: datetime = GENERATED_AT):
    api = _api()
    return api.build_research_event_resolution_timing_risk_report(
        snapshots,
        config=_config(),
        generated_at=generated_at,
    )


def test_report_aggregates_resolution_timing_pressure_without_raw_event_surfaces():
    api = _api()
    report = _report(
        (
            _snapshot(),
            _snapshot(
                event_count=d("2"),
                evidence_observed_at=GENERATED_AT - timedelta(hours=1),
                nearest_resolution_at=GENERATED_AT + timedelta(hours=3),
                source_refreshed_at=GENERATED_AT - timedelta(hours=4),
                ambiguous_event_count=d("1"),
                recheck_due_count=d("0"),
            ),
            _snapshot(
                event_count=d("1"),
                evidence_observed_at=GENERATED_AT - timedelta(minutes=20),
                nearest_resolution_at=GENERATED_AT + timedelta(days=1),
                source_refreshed_at=GENERATED_AT - timedelta(minutes=10),
                ambiguous_event_count=d("0"),
                recheck_due_count=d("0"),
            ),
        ),
    )

    assert type(report) is api.ResearchEventResolutionTimingRiskReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "research-event-resolution-timing-risk-report-v0"
    assert report.snapshot_count == d("3")
    assert report.event_count == d("8")
    assert report.stale_evidence_event_count == d("5")
    assert report.near_resolution_event_count == d("5")
    assert report.source_refresh_lag_event_count == d("7")
    assert report.ambiguous_event_count == d("5")
    assert report.recheck_due_count == d("5")
    assert report.max_evidence_age_seconds == d("25200.000000")
    assert report.min_resolution_window_seconds == d("2700.000000")
    assert report.max_source_refresh_lag_seconds == d("18000.000000")
    assert report.stale_evidence_ratio == d("0.625000")
    assert report.resolution_window_pressure_ratio == d("0.625000")
    assert report.source_refresh_lag_ratio == d("0.875000")
    assert report.ambiguity_burden_ratio == d("0.625000")
    assert report.recheck_urgency_ratio == d("0.625000")
    assert report.timing_risk_score == d("0.675000")
    assert report.status == "block"
    assert report.reason_codes == (
        "stale_evidence_age_present",
        "resolution_window_pressure_present",
        "source_refresh_lag_present",
        "ambiguity_burden_present",
        "recheck_urgency_present",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = api.research_event_resolution_timing_risk_payload(report)
    _assert_no_floats(payload)
    _assert_no_raw_event_surfaces(payload)


def test_payload_digest_and_report_only_guards_are_deterministic():
    api = _api()
    clear = _report(
        (
            _snapshot(
                event_count=d("4"),
                evidence_observed_at=GENERATED_AT - timedelta(minutes=20),
                nearest_resolution_at=GENERATED_AT + timedelta(days=1),
                source_refreshed_at=GENERATED_AT - timedelta(minutes=10),
                ambiguous_event_count=d("0"),
                recheck_due_count=d("0"),
            ),
        ),
    )

    assert clear.status == "pass"
    assert clear.reason_codes == ("resolution_timing_risk_clear",)
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

    payload = api.research_event_resolution_timing_risk_payload(clear)
    assert payload["event_count"] == "4"
    assert payload["timing_risk_score"] == "0.000000"
    assert payload["source_snapshots"][0]["event_count"] == "4"
    assert payload["derived_validation_digest"] == clear.derived_validation_digest
    assert api.research_event_resolution_timing_risk_payload(payload) == payload

    with pytest.raises(ValueError, match="paper_only"):
        api.research_event_resolution_timing_risk_payload({**payload, "paper_only": False})
    with pytest.raises(ValueError, match="Decimal-derived"):
        api.research_event_resolution_timing_risk_payload({**payload, "event_count": 4})
    with pytest.raises(ValueError, match="float"):
        api.research_event_resolution_timing_risk_payload(
            {**payload, "timing_risk_score": 0.1},
        )
    with pytest.raises(ValueError, match="unsafe"):
        api.research_event_resolution_timing_risk_payload(
            {**payload, "market_slug": "raw-slug"},
        )

    raw_surface_fragments = (
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "raw_text",
        "url",
    )
    for cls in (
        api.ResearchEventResolutionTimingRiskConfig,
        api.ResearchEventResolutionTimingRiskSnapshot,
        api.ResearchEventResolutionTimingRiskReport,
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
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "raw_text",
        "url",
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
