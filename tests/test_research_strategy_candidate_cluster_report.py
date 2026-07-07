from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_strategy_candidate_cluster_report as api
from polymarket_alpha_lab.research_strategy_candidate_cluster_report import (
    ResearchStrategyCandidateClusterConfig,
    ResearchStrategyCandidateClusterObservation,
    ResearchStrategyCandidateClusterPublicPayloadItem,
    ResearchStrategyCandidateClusterReport,
    build_research_strategy_candidate_cluster_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _observation(
    *,
    candidate_reference: str = "candidate_a",
    event_domain: str = "policy",
    settlement_window: str = "same_week",
    evidence_dependency_score: Decimal = Decimal("0.100000"),
    candidate_probability: Decimal = Decimal("0.520000"),
    research_probability: Decimal = Decimal("0.510000"),
    rule_risk_score: Decimal = Decimal("0.100000"),
    confidence_score: Decimal = Decimal("0.800000"),
) -> ResearchStrategyCandidateClusterObservation:
    return ResearchStrategyCandidateClusterObservation(
        candidate_reference=candidate_reference,
        event_domain=event_domain,
        settlement_window=settlement_window,
        observed_at=NOW,
        evidence_dependency_score=evidence_dependency_score,
        candidate_probability=candidate_probability,
        research_probability=research_probability,
        rule_risk_score=rule_risk_score,
        confidence_score=confidence_score,
    )


def _report(
    observations: tuple[ResearchStrategyCandidateClusterObservation, ...],
    *,
    config: ResearchStrategyCandidateClusterConfig | None = None,
    public_payload: tuple[ResearchStrategyCandidateClusterPublicPayloadItem, ...] = (),
) -> ResearchStrategyCandidateClusterReport:
    return build_research_strategy_candidate_cluster_report(
        observations,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_clusters_by_domain_settlement_dependency_gap_and_rule_risk() -> None:
    report = _report(
        (
            _observation(candidate_reference="candidate_pass"),
            _observation(
                candidate_reference="candidate_watch",
                event_domain="policy",
                settlement_window="same_week",
                evidence_dependency_score=Decimal("0.400000"),
                candidate_probability=Decimal("0.650000"),
                research_probability=Decimal("0.530000"),
                rule_risk_score=Decimal("0.300000"),
                confidence_score=Decimal("0.700000"),
            ),
            _observation(
                candidate_reference="candidate_block",
                event_domain="weather",
                settlement_window="same_day",
                evidence_dependency_score=Decimal("0.750000"),
                candidate_probability=Decimal("0.850000"),
                research_probability=Decimal("0.500000"),
                rule_risk_score=Decimal("0.850000"),
                confidence_score=Decimal("0.600000"),
            ),
        ),
    )

    assert report.cluster_status == "block"
    assert report.cluster_count == Decimal("3.000000")
    assert report.event_count == Decimal("3.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")

    rows_by_status = {row.cluster_status: row for row in report.rows}
    assert rows_by_status["pass"].event_domain == "policy"
    assert rows_by_status["pass"].settlement_window == "same_week"
    assert rows_by_status["pass"].dependency_band == "independent"
    assert rows_by_status["pass"].probability_gap_band == "aligned"
    assert rows_by_status["pass"].rule_risk_band == "low"
    assert "cluster_pass" in rows_by_status["pass"].reason_codes

    assert rows_by_status["watch"].dependency_band == "dependent_watch"
    assert rows_by_status["watch"].probability_gap_band == "divergent_watch"
    assert rows_by_status["watch"].rule_risk_band == "rule_watch"
    assert rows_by_status["watch"].cluster_status == "watch"
    assert "dependency_watch" in rows_by_status["watch"].reason_codes

    assert rows_by_status["block"].event_domain == "weather"
    assert rows_by_status["block"].settlement_window == "same_day"
    assert rows_by_status["block"].dependency_band == "dependent_block"
    assert rows_by_status["block"].probability_gap_band == "divergent_block"
    assert rows_by_status["block"].rule_risk_band == "rule_block"
    assert rows_by_status["block"].max_probability_gap == Decimal("0.350000")
    assert rows_by_status["block"].cluster_status == "block"
    assert "rule_risk_block" in rows_by_status["block"].reason_codes


def test_payload_serializes_decimals_and_excludes_raw_private_surfaces() -> None:
    report = _report(
        (
            _observation(candidate_reference="candidate_alpha"),
            _observation(candidate_reference="candidate_beta"),
        ),
        public_payload=(
            ResearchStrategyCandidateClusterPublicPayloadItem(
                "safe_summary",
                "cluster audit only",
            ),
        ),
    )

    payload = report.payload
    encoded = json.dumps(payload, sort_keys=True)
    assert payload["event_count"] == "2.000000"
    assert payload["rows"][0]["average_probability_gap"] == "0.010000"
    assert payload["rows"][0]["cluster_status"] == "pass"
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64

    assert "candidate_alpha" not in encoded
    assert "candidate_beta" not in encoded
    for unsafe in (
        "source",
        "market",
        "dsn",
        "table",
        "token",
        "buy",
        "sell",
        "position",
        "recommend",
    ):
        assert unsafe not in encoded.lower()
    _assert_no_non_decimal_public_numbers(report)
    _assert_no_decimal_objects(payload)


def test_strict_decimal_and_exact_type_validation() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        _observation(evidence_dependency_score=0.1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="datetime"):
        ResearchStrategyCandidateClusterObservation(
            candidate_reference="candidate_a",
            event_domain="policy",
            settlement_window="same_week",
            observed_at="2026-01-01",  # type: ignore[arg-type]
            evidence_dependency_score=Decimal("0.100000"),
            candidate_probability=Decimal("0.520000"),
            research_probability=Decimal("0.510000"),
            rule_risk_score=Decimal("0.100000"),
            confidence_score=Decimal("0.800000"),
        )

    with pytest.raises(ValueError, match="observations must be a sequence"):
        build_research_strategy_candidate_cluster_report(
            "not_observations",  # type: ignore[arg-type]
            generated_at=NOW,
        )

    with pytest.raises(ValueError, match="config"):
        build_research_strategy_candidate_cluster_report(
            (),
            generated_at=NOW,
            config=object(),  # type: ignore[arg-type]
        )


def test_dataclasses_are_frozen_and_reject_subclassing() -> None:
    report = _report((_observation(),))

    with pytest.raises(FrozenInstanceError):
        report.cluster_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchStrategyCandidateClusterConfig):
            pass


def test_hard_flags_and_digest_tampering_are_rejected() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        ResearchStrategyCandidateClusterConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        _observation().__class__(
            candidate_reference="candidate_a",
            event_domain="policy",
            settlement_window="same_week",
            observed_at=NOW,
            evidence_dependency_score=Decimal("0.100000"),
            candidate_probability=Decimal("0.520000"),
            research_probability=Decimal("0.510000"),
            rule_risk_score=Decimal("0.100000"),
            confidence_score=Decimal("0.800000"),
            report_only=False,
        )

    report = _report((_observation(),))
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            public_payload=(
                ResearchStrategyCandidateClusterPublicPayloadItem(
                    "safe_summary",
                    "changed",
                ),
            ),
        )


def test_unsafe_public_values_are_rejected_or_absent() -> None:
    for key in (
        "raw_id",
        "source_name",
        "market_slug",
        "dsn_value",
        "table_name",
        "token_value",
        "buy_signal",
        "sell_signal",
        "position_hint",
        "recommendation",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchStrategyCandidateClusterPublicPayloadItem(key, "safe value")

    for value in (
        "raw id abc",
        "source abc",
        "market abc",
        "postgres dsn",
        "table abc",
        "token abc",
        "buy abc",
        "sell abc",
        "position abc",
        "recommend abc",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchStrategyCandidateClusterPublicPayloadItem("safe_summary", value)

    with pytest.raises(ValueError, match="unsafe public"):
        _observation(candidate_reference="source_token_candidate")

    for public_name in api.__all__:
        lowered = public_name.lower()
        for unsafe in ("source", "market", "dsn", "table", "token"):
            assert unsafe not in lowered

    for cls in (
        ResearchStrategyCandidateClusterConfig,
        ResearchStrategyCandidateClusterObservation,
        ResearchStrategyCandidateClusterPublicPayloadItem,
        api.ResearchStrategyCandidateClusterRow,
        ResearchStrategyCandidateClusterReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            for unsafe in ("source", "market", "dsn", "table", "token"):
                assert unsafe not in lowered

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
