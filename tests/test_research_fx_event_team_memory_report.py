from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_fx_event_team_memory_report import (
    ResearchFxEventTeamMemoryConfig,
    ResearchFxEventTeamMemoryObservation,
    ResearchFxEventTeamMemoryReport,
    build_research_fx_event_team_memory_report,
    research_fx_event_team_memory_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchFxEventTeamMemoryConfig:
    values = {
        "config_version": "research-fx-event-team-memory-report-v0",
        "source_fresh_seconds": d("7200"),
        "source_stale_seconds": d("86400"),
        "min_calibration_sample_count": d("20"),
        "pass_readiness_score": d("0.750000"),
        "watch_readiness_score": d("0.500000"),
        "source_freshness_weight": d("0.250000"),
        "evidence_reuse_weight": d("0.250000"),
        "macro_linkage_weight": d("0.250000"),
        "calibration_readiness_weight": d("0.250000"),
    }
    values.update(overrides)
    return ResearchFxEventTeamMemoryConfig(**values)


def observation(
    index: int,
    *,
    event_bucket: str,
    source_observed_at: datetime,
    evidence_reuse_ratio: Decimal,
    macro_linkage_score: Decimal,
    calibration_sample_count: Decimal,
    calibration_error: Decimal,
    specialist_label: str = "fx-event-specialist",
    source_family_label: str = "official-macro",
) -> ResearchFxEventTeamMemoryObservation:
    return ResearchFxEventTeamMemoryObservation(
        specialist_label=specialist_label,
        event_bucket=event_bucket,
        source_family_label=f"{source_family_label}-{index}",
        source_observed_at=source_observed_at,
        evidence_reuse_ratio=evidence_reuse_ratio,
        macro_linkage_score=macro_linkage_score,
        calibration_sample_count=calibration_sample_count,
        calibration_error=calibration_error,
    )


def test_fx_event_memory_report_scores_specialist_readiness_with_deterministic_payload() -> None:
    memory_report = build_research_fx_event_team_memory_report(
        (
            observation(
                3,
                event_bucket="em-cross-commodity",
                source_observed_at=GENERATED_AT - timedelta(hours=50),
                evidence_reuse_ratio=d("0.200000"),
                macro_linkage_score=d("0.350000"),
                calibration_sample_count=d("4"),
                calibration_error=d("0.550000"),
            ),
            observation(
                1,
                event_bucket="g10-central-bank",
                source_observed_at=GENERATED_AT - timedelta(minutes=30),
                evidence_reuse_ratio=d("0.900000"),
                macro_linkage_score=d("0.850000"),
                calibration_sample_count=d("30"),
                calibration_error=d("0.050000"),
            ),
            observation(
                2,
                event_bucket="g10-inflation-print",
                source_observed_at=GENERATED_AT - timedelta(hours=8),
                evidence_reuse_ratio=d("0.550000"),
                macro_linkage_score=d("0.650000"),
                calibration_sample_count=d("12"),
                calibration_error=d("0.200000"),
            ),
        ),
        config=config(),
        generated_at=GENERATED_AT,
    )
    payload = research_fx_event_team_memory_report_payload(memory_report)
    unsigned_payload = dict(payload)
    digest = unsigned_payload.pop("derived_validation_digest")
    expected_digest = hashlib.sha256(
        json.dumps(unsigned_payload, sort_keys=True, separators=(",", ":")).encode(),
    ).hexdigest()

    assert type(memory_report) is ResearchFxEventTeamMemoryReport
    assert memory_report.status == "block"
    assert memory_report.event_bucket_count == d("3")
    assert memory_report.pass_count == d("1")
    assert memory_report.watch_count == d("1")
    assert memory_report.block_count == d("1")
    assert memory_report.average_readiness_score == d("0.557222")
    assert tuple(row.event_bucket for row in memory_report.rows) == (
        "em-cross-commodity",
        "g10-inflation-print",
        "g10-central-bank",
    )
    assert tuple(row.status for row in memory_report.rows) == ("block", "watch", "pass")
    assert memory_report.rows[0].readiness_score == d("0.160000")
    assert memory_report.rows[1].source_freshness_score == d("0.666667")
    assert memory_report.rows[1].calibration_readiness_score == d("0.480000")
    assert memory_report.rows[2].readiness_score == d("0.925000")
    assert memory_report.reason_codes == (
        "fx_event_memory_calibration_ready",
        "fx_event_memory_calibration_underpowered",
        "fx_event_memory_evidence_reuse_low",
        "fx_event_memory_evidence_reuse_ready",
        "fx_event_memory_macro_linkage_ready",
        "fx_event_memory_macro_linkage_weak",
        "fx_event_memory_report_block",
        "fx_event_memory_source_fresh",
        "fx_event_memory_source_stale",
        "fx_event_memory_source_watch",
    )
    assert memory_report.paper_only is True
    assert memory_report.report_only is True
    assert memory_report.readonly is True
    assert payload == research_fx_event_team_memory_report_payload(memory_report)
    assert digest == expected_digest
    assert payload["derived_validation_digest"] == memory_report.derived_validation_digest
    assert payload["rows"][0]["event_bucket"] == "em-cross-commodity"
    assert payload["rows"][0]["readiness_score"] == "0.160000"
    assert not any(type(value) in (float, int) for value in _walk_payload_values(payload))


def test_fx_event_memory_report_rejects_unsafe_inputs_and_has_no_side_effect_surface() -> None:
    safe_observation = observation(
        1,
        event_bucket="g10-central-bank",
        source_observed_at=GENERATED_AT - timedelta(minutes=30),
        evidence_reuse_ratio=d("0.900000"),
        macro_linkage_score=d("0.850000"),
        calibration_sample_count=d("30"),
        calibration_error=d("0.050000"),
    )

    with pytest.raises(FrozenInstanceError):
        safe_observation.event_bucket = "g10-inflation-print"  # type: ignore[misc]
    with pytest.raises(ValueError, match="source_fresh_seconds"):
        config(source_fresh_seconds=d("90000"))
    with pytest.raises(ValueError, match="pass_readiness_score"):
        config(pass_readiness_score=d("0.500000"))
    with pytest.raises(ValueError, match="source_freshness_weight"):
        config(source_freshness_weight=0.25)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_reuse_ratio"):
        observation(
            1,
            event_bucket="g10-central-bank",
            source_observed_at=GENERATED_AT - timedelta(minutes=30),
            evidence_reuse_ratio=_DecimalSubclass("0.900000"),
            macro_linkage_score=d("0.850000"),
            calibration_sample_count=d("30"),
            calibration_error=d("0.050000"),
        )
    with pytest.raises(ValueError, match="source_observed_at"):
        observation(
            1,
            event_bucket="g10-central-bank",
            source_observed_at=_DatetimeSubclass(2026, 7, 8, 11, 30, tzinfo=UTC),
            evidence_reuse_ratio=d("0.900000"),
            macro_linkage_score=d("0.850000"),
            calibration_sample_count=d("30"),
            calibration_error=d("0.050000"),
        )
    with pytest.raises(ValueError, match="event_bucket"):
        observation(
            1,
            event_bucket="https://example.invalid/fx-event",
            source_observed_at=GENERATED_AT - timedelta(minutes=30),
            evidence_reuse_ratio=d("0.900000"),
            macro_linkage_score=d("0.850000"),
            calibration_sample_count=d("30"),
            calibration_error=d("0.050000"),
        )
    with pytest.raises(ValueError, match="source_family_label"):
        observation(
            1,
            event_bucket="g10-central-bank",
            source_family_label="source-text",
            source_observed_at=GENERATED_AT - timedelta(minutes=30),
            evidence_reuse_ratio=d("0.900000"),
            macro_linkage_score=d("0.850000"),
            calibration_sample_count=d("30"),
            calibration_error=d("0.050000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(safe_observation, paper_only=False)
    with pytest.raises(ValueError, match="generated_at"):
        build_research_fx_event_team_memory_report(
            (safe_observation,),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="source_observed_at"):
        build_research_fx_event_team_memory_report(
            (
                replace(
                    safe_observation,
                    source_observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            config=config(),
            generated_at=GENERATED_AT,
        )

    empty_report = build_research_fx_event_team_memory_report(
        (),
        config=config(),
        generated_at=GENERATED_AT,
    )
    assert empty_report.status == "block"
    assert empty_report.reason_codes == ("fx_event_memory_no_observations",)
    assert empty_report.rows == ()

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_fx_event_team_memory_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "sqlite",
        "wallet",
        "order",
        "live",
        "trade",
    )

    assert all(term not in source for term in forbidden_terms)


@pytest.mark.parametrize(
    ("field_name", "unsafe_value"),
    (
        ("specialist_label", "candidate-alpha"),
        ("event_bucket", "market-id-alpha"),
        ("event_bucket", "market-slug-alpha"),
        ("event_bucket", "market-question-alpha"),
        ("source_family_label", "dsn-prod"),
        ("source_family_label", "table-prod"),
        ("source_family_label", "token-prod"),
        ("source_family_label", "private-key-prod"),
        ("source_family_label", "auth-prod"),
        ("event_bucket", "wallet-alpha"),
        ("event_bucket", "order-alpha"),
        ("event_bucket", "trade-alpha"),
        ("event_bucket", "live-trading-alpha"),
        ("event_bucket", "sizing-alpha"),
        ("event_bucket", "recommendation-alpha"),
    ),
)
def test_fx_event_memory_report_rejects_public_payload_leak_labels(
    field_name: str,
    unsafe_value: str,
) -> None:
    values = {
        "index": 1,
        "event_bucket": "g10-central-bank",
        "source_family_label": "official-macro",
        "source_observed_at": GENERATED_AT - timedelta(minutes=30),
        "evidence_reuse_ratio": d("0.900000"),
        "macro_linkage_score": d("0.850000"),
        "calibration_sample_count": d("30"),
        "calibration_error": d("0.050000"),
        "specialist_label": "fx-event-specialist",
    }
    values[field_name] = unsafe_value

    with pytest.raises(ValueError, match=field_name):
        observation(**values)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
