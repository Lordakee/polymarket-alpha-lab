from __future__ import annotations

import dataclasses
import importlib
import json
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_event_domain_coverage_gap_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object):
    module = api()
    return module.ResearchEventDomainCoverageGapConfig(**overrides)


def _observation(
    lane: str = "politics",
    domain_bucket: str = "politics-election-calendar",
    *,
    coverage_ratio: Decimal = d("0.900000"),
    memory_age_hours: Decimal = d("12.000000"),
    source_gap_count: Decimal = d("0"),
    review_load_ratio: Decimal = d("0.200000"),
    escalation_urgency_score: Decimal = d("0.100000"),
):
    module = api()
    return module.ResearchEventDomainCoverageGapObservation(
        lane=lane,
        domain_bucket=domain_bucket,
        coverage_ratio=coverage_ratio,
        memory_age_hours=memory_age_hours,
        source_gap_count=source_gap_count,
        review_load_ratio=review_load_ratio,
        escalation_urgency_score=escalation_urgency_score,
    )


def _report(
    observations: tuple[object, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    config=None,
):
    module = api()
    return module.build_research_event_domain_coverage_gap_report(
        observations,
        generated_at=generated_at,
        config=_config() if config is None else config,
    )


def test_domain_coverage_gap_report_rolls_up_gap_pressure_and_reasons() -> None:
    module = api()
    pass_row = _observation(
        "politics",
        "politics-election-calendar",
    )
    watch_row = _observation(
        "weather",
        "weather-hurricane-season",
        coverage_ratio=d("0.700000"),
        memory_age_hours=d("72.000000"),
        source_gap_count=d("1"),
        review_load_ratio=d("0.800000"),
        escalation_urgency_score=d("0.500000"),
    )
    block_row = _observation(
        "crypto",
        "crypto-stablecoin-policy",
        coverage_ratio=d("0.400000"),
        memory_age_hours=d("200.000000"),
        source_gap_count=d("4"),
        review_load_ratio=d("1.200000"),
        escalation_urgency_score=d("0.800000"),
    )

    report = _report((pass_row, watch_row, block_row))
    payload = module.research_event_domain_coverage_gap_report_payload(report)

    assert dataclasses.is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.lane_count == d("3")
    assert report.domain_bucket_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.average_gap_pressure_score == d("0.482222")
    assert report.max_gap_pressure_score == d("0.880000")
    assert report.min_coverage_ratio == d("0.400000")
    assert report.max_memory_age_hours == d("200.000000")
    assert report.total_source_gap_count == d("5")
    assert report.max_review_load_ratio == d("1.200000")
    assert report.max_escalation_urgency_score == d("0.800000")
    assert report.reason_code_counts == (
        ("coverage_scarcity_block", d("1")),
        ("stale_memory_block", d("1")),
        ("source_gap_block", d("1")),
        ("review_load_block", d("1")),
        ("escalation_urgency_block", d("1")),
        ("coverage_scarcity_watch", d("1")),
        ("stale_memory_watch", d("1")),
        ("source_gap_watch", d("1")),
        ("review_load_watch", d("1")),
        ("escalation_urgency_watch", d("1")),
        ("coverage_gap_clear", d("1")),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.lane, row.domain_bucket, row.status) for row in report.rows) == (
        ("crypto", "crypto-stablecoin-policy", "block"),
        ("weather", "weather-hurricane-season", "watch"),
        ("politics", "politics-election-calendar", "pass"),
    )

    blocked, watched, passed = report.rows
    assert blocked.coverage_scarcity_pressure == d("0.600000")
    assert blocked.stale_memory_pressure == d("1.000000")
    assert blocked.source_gap_pressure == d("1.000000")
    assert blocked.review_load_pressure == d("1.000000")
    assert blocked.gap_pressure_score == d("0.880000")
    assert blocked.reason_codes == (
        "coverage_scarcity_block",
        "stale_memory_block",
        "source_gap_block",
        "review_load_block",
        "escalation_urgency_block",
    )
    assert watched.gap_pressure_score == d("0.472381")
    assert watched.reason_codes == (
        "coverage_scarcity_watch",
        "stale_memory_watch",
        "source_gap_watch",
        "review_load_watch",
        "escalation_urgency_watch",
    )
    assert passed.gap_pressure_score == d("0.094286")
    assert passed.reason_codes == ("coverage_gap_clear",)

    assert payload["derived_payload_digest"] == report.derived_payload_digest
    assert payload["rows"][0]["gap_pressure_score"] == "0.880000"
    assert payload["reason_code_counts"][0][1] == "1"
    json.dumps(payload, sort_keys=True)


def test_payload_digest_is_deterministic_for_all_public_lanes() -> None:
    module = api()
    lanes = module.EVENT_DOMAIN_COVERAGE_GAP_LANES
    observations = tuple(
        _observation(
            lane,
            f"{lane}-aggregate-coverage",
            coverage_ratio=d("0.900000"),
            memory_age_hours=d("6.000000"),
            source_gap_count=d("0"),
            review_load_ratio=d("0.100000"),
            escalation_urgency_score=d("0.050000"),
        )
        for lane in lanes
    )

    generated_at = datetime(
        2026,
        7,
        8,
        8,
        0,
        tzinfo=timezone(timedelta(hours=-4)),
    )
    first = _report(observations, generated_at=generated_at)
    second = _report(tuple(reversed(observations)), generated_at=generated_at)
    payload = module.research_event_domain_coverage_gap_report_payload(first)

    assert lanes == (
        "politics",
        "macro",
        "crypto",
        "rates",
        "fx",
        "tech",
        "energy",
        "weather",
        "sports",
    )
    assert module.STATUSES == ("pass", "watch", "block")
    assert first.rows == second.rows
    assert first.derived_payload_digest == second.derived_payload_digest
    assert payload == module.research_event_domain_coverage_gap_report_payload(second)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["lane_count"] == "9"
    assert payload["domain_bucket_count"] == "9"
    assert payload["rows"][0]["coverage_ratio"] == "0.900000"
    assert len(first.derived_payload_digest) == 64
    int(first.derived_payload_digest, 16)
    assert not any(type(value) is int for value in _walk_values(payload))
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert not any(isinstance(value, Decimal) for value in _walk_values(payload))
    assert module.research_event_domain_coverage_gap_report_payload(payload) == payload

    tampered = dict(payload)
    tampered["domain_bucket_count"] = "10"
    with pytest.raises(ValueError, match="derived_payload_digest"):
        module.research_event_domain_coverage_gap_report_payload(tampered)


def test_validation_enforces_public_aggregate_labels_decimals_flags_and_statuses() -> None:
    module = api()
    report = _report((_observation(),))

    with pytest.raises(dataclasses.FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        dataclasses.replace(_config(), paper_only=False)
    with pytest.raises(ValueError, match="coverage_ratio must be a Decimal"):
        _observation(coverage_ratio=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="memory_age_hours must be a Decimal"):
        _observation(memory_age_hours=12)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_gap_count must be a Decimal"):
        _observation(source_gap_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="lane must be one of"):
        _observation("equities", "equities-earnings")
    with pytest.raises(ValueError, match="public aggregate label"):
        _observation("politics", "politics-market-slug-abc")
    with pytest.raises(ValueError, match="duplicate"):
        _report(
            (
                _observation("macro", "macro-calendar"),
                _observation("macro", "macro-calendar"),
            ),
        )
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        dataclasses.replace(report.rows[0], status="ready")


def test_report_only_payload_has_no_live_or_private_surfaces() -> None:
    module = api()
    report = _report(
        (
            _observation("rates", "rates-central-bank"),
            _observation("fx", "fx-policy-divergence"),
            _observation("tech", "tech-regulatory-calendar"),
            _observation("energy", "energy-supply-calendar"),
            _observation("sports", "sports-injury-roundup"),
        ),
    )
    payload = module.research_event_domain_coverage_gap_report_payload(report)
    rendered = json.dumps(payload, sort_keys=True).lower()

    assert set(module.__all__) == {
        "EVENT_DOMAIN_COVERAGE_GAP_LANES",
        "ResearchEventDomainCoverageGapConfig",
        "ResearchEventDomainCoverageGapObservation",
        "ResearchEventDomainCoverageGapReport",
        "ResearchEventDomainCoverageGapRow",
        "STATUSES",
        "build_research_event_domain_coverage_gap_report",
        "research_event_domain_coverage_gap_report_payload",
    }
    for forbidden in (
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "position",
        "network",
        "database",
        "auth",
        "token",
        "private_key",
        "event_id",
        "market_id",
        "condition_id",
        "slug",
    ):
        assert forbidden not in rendered
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert all(row["paper_only"] is True for row in payload["rows"])
    assert all(row["report_only"] is True for row in payload["rows"])
    assert all(row["readonly"] is True for row in payload["rows"])


def test_dict_payload_rejects_private_leak_surfaces_even_with_valid_digest() -> None:
    module = api()
    report = _report((_observation(),))
    base_payload = module.research_event_domain_coverage_gap_report_payload(report)

    unsafe_extras = (
        {"candidate_id": "candidate-123"},
        {"market_question": "will this market resolve yes"},
        {"source_url": "https://example.com/source"},
        {"source_text": "public source transcript"},
        {"dsn": "postgresql://user:pass@example.test/db"},
        {"table_name": "research_events"},
    )

    for extra in unsafe_extras:
        payload = _payload_with_valid_digest({**base_payload, **extra})
        with pytest.raises(ValueError, match="unsafe public surface"):
            module.research_event_domain_coverage_gap_report_payload(payload)


def _payload_with_valid_digest(payload: dict[str, object]) -> dict[str, object]:
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_payload_digest", None)
    rendered = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        **payload_without_digest,
        "derived_payload_digest": sha256(rendered.encode("utf-8")).hexdigest(),
    }


def _walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        values: list[object] = []
        for item in value.values():
            values.extend(_walk_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_walk_values(item))
        return tuple(values)
    return (value,)
