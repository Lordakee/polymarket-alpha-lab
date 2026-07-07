from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_signal_source_diversity_report as api
from polymarket_alpha_lab.research_signal_source_diversity_report import (
    ResearchSignalSourceDiversityConfig,
    ResearchSignalSourceDiversityObservation,
    ResearchSignalSourceDiversityPublicPayloadItem,
    ResearchSignalSourceDiversityReport,
    ResearchSignalSourceDiversityRow,
    build_research_signal_source_diversity_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _observation(
    *,
    signal_key: str = "signal_alpha",
    observation_key: str = "obs_a",
    source_family: str = "official",
    source_cluster: str = "cluster_a",
    stance: str = "supports",
    confidence_score: Decimal = Decimal("0.800000"),
) -> ResearchSignalSourceDiversityObservation:
    return ResearchSignalSourceDiversityObservation(
        signal_key=signal_key,
        observation_key=observation_key,
        source_family=source_family,
        source_cluster=source_cluster,
        stance=stance,
        observed_at=NOW,
        confidence_score=confidence_score,
    )


def _report(
    observations: tuple[ResearchSignalSourceDiversityObservation, ...],
    *,
    config: ResearchSignalSourceDiversityConfig | None = None,
    public_payload: tuple[ResearchSignalSourceDiversityPublicPayloadItem, ...] = (),
) -> ResearchSignalSourceDiversityReport:
    return build_research_signal_source_diversity_report(
        observations,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_diverse_independent_sources_with_counterevidence_pass() -> None:
    report = _report(
        (
            _observation(observation_key="obs_c", source_family="expert", source_cluster="cluster_c"),
            _observation(observation_key="obs_a", source_family="official", source_cluster="cluster_a"),
            _observation(observation_key="obs_d", source_family="media", source_cluster="cluster_d", stance="counters"),
            _observation(observation_key="obs_b", source_family="primary", source_cluster="cluster_b"),
        ),
    )

    row = report.rows[0]
    assert report.status == "pass"
    assert report.signal_count == Decimal("1.000000")
    assert report.pass_count == Decimal("1.000000")
    assert row.observation_count == Decimal("4.000000")
    assert row.supporting_observation_count == Decimal("3.000000")
    assert row.counter_observation_count == Decimal("1.000000")
    assert row.source_family_count == Decimal("4.000000")
    assert row.independent_source_count == Decimal("4.000000")
    assert row.source_concentration_ratio == Decimal("0.250000")
    assert row.counterevidence_coverage_ratio == Decimal("0.250000")
    assert row.diversity_score == Decimal("1.000000")
    assert row.status == "pass"
    assert row.reason_codes == ("source_diversity_pass",)


def test_concentrated_single_family_signal_blocks() -> None:
    report = _report(
        (
            _observation(observation_key="obs_a", source_family="official", source_cluster="cluster_a"),
            _observation(observation_key="obs_b", source_family="official", source_cluster="cluster_a"),
            _observation(observation_key="obs_c", source_family="official", source_cluster="cluster_a"),
        ),
    )

    row = report.rows[0]
    assert report.status == "block"
    assert report.block_count == Decimal("1.000000")
    assert row.source_family_count == Decimal("1.000000")
    assert row.independent_source_count == Decimal("1.000000")
    assert row.source_concentration_ratio == Decimal("1.000000")
    assert row.status == "block"
    assert "single_source_family_block" in row.reason_codes
    assert "single_independent_source_block" in row.reason_codes
    assert "source_concentration_block" in row.reason_codes


def test_missing_counterevidence_yields_watch_not_pass() -> None:
    report = _report(
        (
            _observation(observation_key="obs_a", source_family="official", source_cluster="cluster_a"),
            _observation(observation_key="obs_b", source_family="primary", source_cluster="cluster_b"),
            _observation(observation_key="obs_c", source_family="expert", source_cluster="cluster_c"),
        ),
    )

    row = report.rows[0]
    assert report.status == "watch"
    assert row.counter_observation_count == Decimal("0.000000")
    assert row.counterevidence_coverage_ratio == Decimal("0.000000")
    assert row.status == "watch"
    assert row.reason_codes == ("counterevidence_coverage_watch",)


def test_rows_and_public_payload_are_deterministically_sorted_and_json_ready() -> None:
    report = _report(
        (
            _observation(signal_key="signal_b", observation_key="obs_b1", source_family="official", source_cluster="cluster_b1"),
            _observation(signal_key="signal_a", observation_key="obs_a2", source_family="primary", source_cluster="cluster_a2"),
            _observation(signal_key="signal_a", observation_key="obs_a1", source_family="official", source_cluster="cluster_a1", stance="counters"),
        ),
        public_payload=(
            ResearchSignalSourceDiversityPublicPayloadItem("z_summary", "safe summary"),
            ResearchSignalSourceDiversityPublicPayloadItem("a_summary", "safe note"),
        ),
    )

    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert [row.signal_key for row in report.rows] == ["signal_a", "signal_b"]
    assert [item.key for item in report.public_payload] == ["a_summary", "z_summary"]
    assert payload["signal_count"] == "2.000000"
    assert payload["rows"][0]["observation_count"] == "2.000000"
    assert payload["rows"][0]["source_concentration_ratio"] == "0.500000"
    assert payload["public_payload"][0]["key"] == "a_summary"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_non_decimal_public_numbers(report)
    _assert_no_decimal_objects(payload)
    _assert_payload_has_no_forbidden_public_surface(payload)


def test_decimal_only_and_strict_type_validation() -> None:
    with pytest.raises(ValueError, match="confidence_score"):
        _observation(confidence_score=0.8)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="observations must be a sequence"):
        build_research_signal_source_diversity_report(
            "not-a-sequence",  # type: ignore[arg-type]
            generated_at=NOW,
        )

    with pytest.raises(ValueError, match="observations items"):
        build_research_signal_source_diversity_report(
            (object(),),
            generated_at=NOW,
        )

    with pytest.raises(ValueError, match="source_family"):
        _observation(source_family="https://example.invalid/source")

    with pytest.raises(ValueError, match="signal_key"):
        _observation(signal_key="raw_market_123")


def test_dataclasses_are_frozen_and_reject_subclassing_and_flag_tampering() -> None:
    report = _report(
        (
            _observation(observation_key="obs_a", source_family="official", source_cluster="cluster_a"),
            _observation(observation_key="obs_b", source_family="primary", source_cluster="cluster_b", stance="counters"),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchSignalSourceDiversityConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        ResearchSignalSourceDiversityConfig(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_digest_rejects_report_tampering() -> None:
    report = _report(
        (
            _observation(observation_key="obs_a", source_family="official", source_cluster="cluster_a"),
            _observation(observation_key="obs_b", source_family="primary", source_cluster="cluster_b", stance="counters"),
        ),
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            public_payload=(
                ResearchSignalSourceDiversityPublicPayloadItem(
                    "safe_summary",
                    "changed summary",
                ),
            ),
        )


def test_no_forbidden_public_surfaces_or_io_capabilities_are_exposed() -> None:
    forbidden_terms = (
        "url",
        "ref",
        "text",
        "table",
        "dsn",
        "token",
        "market_id",
        "candidate_id",
        "raw_market",
        "raw_candidate",
        "auth",
        "wallet",
        "trade",
        "order",
        "buy",
        "sell",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in forbidden_terms)

    for cls in (
        ResearchSignalSourceDiversityConfig,
        ResearchSignalSourceDiversityObservation,
        ResearchSignalSourceDiversityPublicPayloadItem,
        ResearchSignalSourceDiversityRow,
        ResearchSignalSourceDiversityReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in forbidden_terms)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)

    report = _report(
        (
            _observation(observation_key="obs_a", source_family="official", source_cluster="cluster_a"),
            _observation(observation_key="obs_b", source_family="primary", source_cluster="cluster_b", stance="counters"),
        ),
    )
    _assert_payload_has_no_forbidden_public_surface(report.payload)


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


def _assert_payload_has_no_forbidden_public_surface(value: object) -> None:
    forbidden = (
        "source_url",
        "source_ref",
        "source_text",
        "source_table",
        "dsn",
        "token",
        "market_id",
        "candidate_id",
        "raw_market",
        "raw_candidate",
        "http://",
        "https://",
    )
    rendered = json.dumps(value, sort_keys=True).lower()
    assert not any(term in rendered for term in forbidden)
