from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_strategy_model_market_divergence_report as api
from polymarket_alpha_lab.research_strategy_model_market_divergence_report import (
    ResearchStrategyModelMarketDivergenceConfig,
    ResearchStrategyModelMarketDivergenceObservation,
    ResearchStrategyModelMarketDivergencePublicPayloadItem,
    ResearchStrategyModelMarketDivergenceReport,
    ResearchStrategyModelMarketDivergenceRow,
    build_research_strategy_model_market_divergence_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _observation(
    *,
    analysis_key: str = "analysis_a",
    candidate_reference: str = "candidate_raw_a",
    market_reference: str = "market_raw_a",
    model_input_observed_at: datetime | None = None,
    market_observed_at: datetime | None = None,
    model_implied_probability: Decimal = Decimal("0.700000"),
    observed_market_probability: Decimal = Decimal("0.550000"),
    evidence_explanation_score: Decimal = Decimal("0.700000"),
    cost_explanation_score: Decimal = Decimal("0.100000"),
    liquidity_explanation_score: Decimal = Decimal("0.100000"),
) -> ResearchStrategyModelMarketDivergenceObservation:
    return ResearchStrategyModelMarketDivergenceObservation(
        analysis_key=analysis_key,
        candidate_reference=candidate_reference,
        market_reference=market_reference,
        model_input_observed_at=model_input_observed_at
        or NOW - timedelta(minutes=30),
        market_observed_at=market_observed_at or NOW - timedelta(minutes=10),
        model_implied_probability=model_implied_probability,
        observed_market_probability=observed_market_probability,
        evidence_explanation_score=evidence_explanation_score,
        cost_explanation_score=cost_explanation_score,
        liquidity_explanation_score=liquidity_explanation_score,
    )


def _report(
    observations: tuple[ResearchStrategyModelMarketDivergenceObservation, ...],
    *,
    config: ResearchStrategyModelMarketDivergenceConfig | None = None,
    public_payload: tuple[ResearchStrategyModelMarketDivergencePublicPayloadItem, ...] = (),
) -> ResearchStrategyModelMarketDivergenceReport:
    return build_research_strategy_model_market_divergence_report(
        observations,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_evidence_explained_divergence_passes_without_recommendation_surface() -> None:
    report = _report((_observation(),))

    row = report.rows[0]
    assert report.divergence_status == "pass"
    assert report.row_count == Decimal("1.000000")
    assert report.pass_count == Decimal("1.000000")
    assert row.divergence_magnitude == Decimal("0.150000")
    assert row.divergence_direction == "model_above_market"
    assert row.explanation_score == Decimal("0.700000")
    assert row.unexplained_divergence == Decimal("0.045000")
    assert row.dominant_explanation == "evidence"
    assert row.divergence_status == "pass"
    assert "evidence_explains_divergence" in row.reason_codes
    assert "model_above_market" in row.reason_codes
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert "recommendation" not in lowered
        assert "wallet" not in lowered
        assert "order" not in lowered
        assert "trade" not in lowered


def test_unexplained_material_divergence_blocks() -> None:
    report = _report(
        (
            _observation(
                model_implied_probability=Decimal("0.820000"),
                observed_market_probability=Decimal("0.500000"),
                evidence_explanation_score=Decimal("0.000000"),
                cost_explanation_score=Decimal("0.000000"),
                liquidity_explanation_score=Decimal("0.000000"),
            ),
        ),
    )

    row = report.rows[0]
    assert report.divergence_status == "block"
    assert report.block_count == Decimal("1.000000")
    assert row.divergence_magnitude == Decimal("0.320000")
    assert row.explanation_score == Decimal("0.000000")
    assert row.unexplained_divergence == Decimal("0.320000")
    assert row.divergence_status == "block"
    assert "material_unexplained_divergence" in row.reason_codes
    assert "block_unexplained_divergence" in row.reason_codes


def test_cost_liquidity_and_stale_inputs_can_explain_divergence() -> None:
    report = _report(
        (
            _observation(
                analysis_key="analysis_cost",
                candidate_reference="candidate_cost",
                market_reference="market_cost",
                model_implied_probability=Decimal("0.610000"),
                observed_market_probability=Decimal("0.490000"),
                evidence_explanation_score=Decimal("0.100000"),
                cost_explanation_score=Decimal("0.650000"),
                liquidity_explanation_score=Decimal("0.200000"),
            ),
            _observation(
                analysis_key="analysis_liquidity",
                candidate_reference="candidate_liquidity",
                market_reference="market_liquidity",
                model_implied_probability=Decimal("0.300000"),
                observed_market_probability=Decimal("0.430000"),
                evidence_explanation_score=Decimal("0.100000"),
                cost_explanation_score=Decimal("0.100000"),
                liquidity_explanation_score=Decimal("0.750000"),
            ),
            _observation(
                analysis_key="analysis_stale",
                candidate_reference="candidate_stale",
                market_reference="market_stale",
                model_input_observed_at=NOW - timedelta(days=2),
                model_implied_probability=Decimal("0.740000"),
                observed_market_probability=Decimal("0.600000"),
                evidence_explanation_score=Decimal("0.100000"),
                cost_explanation_score=Decimal("0.100000"),
                liquidity_explanation_score=Decimal("0.100000"),
            ),
        ),
    )

    rows = {row.analysis_key: row for row in report.rows}
    assert report.divergence_status == "pass"
    assert rows["analysis_cost"].dominant_explanation == "costs"
    assert rows["analysis_cost"].explanation_score == Decimal("0.650000")
    assert "costs_explain_divergence" in rows["analysis_cost"].reason_codes
    assert rows["analysis_liquidity"].dominant_explanation == "liquidity"
    assert rows["analysis_liquidity"].divergence_direction == "market_above_model"
    assert "liquidity_explains_divergence" in rows["analysis_liquidity"].reason_codes
    assert rows["analysis_stale"].dominant_explanation == "stale_inputs"
    assert rows["analysis_stale"].stale_input_explanation_score == Decimal("1.000000")
    assert "stale_inputs_explain_divergence" in rows["analysis_stale"].reason_codes


def test_payload_serializes_decimals_and_redacts_raw_references() -> None:
    raw_candidate = "candidate_raw_123"
    raw_market = "https://example.invalid/markets/raw-slug?question=hidden"
    report = _report(
        (
            _observation(
                candidate_reference=raw_candidate,
                market_reference=raw_market,
            ),
        ),
        public_payload=(
            ResearchStrategyModelMarketDivergencePublicPayloadItem(
                "safe_key",
                "safe value",
            ),
        ),
    )

    payload = report.payload
    payload_json = json.dumps(payload, sort_keys=True)
    assert payload["row_count"] == "1.000000"
    assert payload["average_divergence_magnitude"] == "0.150000"
    assert payload["rows"][0]["divergence_magnitude"] == "0.150000"
    assert payload["rows"][0]["candidate_reference_digest"].startswith("sha256:")
    assert payload["rows"][0]["market_reference_digest"].startswith("sha256:")
    assert raw_candidate not in payload_json
    assert raw_market not in payload_json
    assert "raw-slug" not in payload_json
    assert "question=hidden" not in payload_json
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_non_decimal_public_numbers(report)
    _assert_no_decimal_objects(payload)


def test_digest_is_deterministic_for_reordered_inputs_and_payload_items() -> None:
    observation_a = _observation(
        analysis_key="analysis_a",
        candidate_reference="candidate_a",
        market_reference="market_a",
    )
    observation_b = _observation(
        analysis_key="analysis_b",
        candidate_reference="candidate_b",
        market_reference="market_b",
    )
    payload_a = ResearchStrategyModelMarketDivergencePublicPayloadItem("alpha", "first")
    payload_b = ResearchStrategyModelMarketDivergencePublicPayloadItem("beta", "second")

    report_a = _report((observation_b, observation_a), public_payload=(payload_b, payload_a))
    report_b = _report((observation_a, observation_b), public_payload=(payload_a, payload_b))

    assert report_a.payload == report_b.payload
    assert report_a.derived_validation_digest == report_b.derived_validation_digest


def test_dataclasses_are_frozen_and_reject_subclassing() -> None:
    report = _report((_observation(),))

    with pytest.raises(FrozenInstanceError):
        report.divergence_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchStrategyModelMarketDivergenceConfig):
            pass


def test_hard_flags_are_enforced() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        ResearchStrategyModelMarketDivergenceConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        _observation().__class__(
            analysis_key="analysis_a",
            candidate_reference="candidate_a",
            market_reference="market_a",
            model_input_observed_at=NOW,
            market_observed_at=NOW,
            model_implied_probability=Decimal("0.600000"),
            observed_market_probability=Decimal("0.500000"),
            evidence_explanation_score=Decimal("0.700000"),
            cost_explanation_score=Decimal("0.100000"),
            liquidity_explanation_score=Decimal("0.100000"),
            report_only=False,
        )

    report = _report((_observation(),))
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = _report((_observation(),))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            public_payload=(
                ResearchStrategyModelMarketDivergencePublicPayloadItem(
                    "safe_key",
                    "changed value",
                ),
            ),
        )


def test_unsafe_public_payload_keys_and_values_are_rejected() -> None:
    for key in (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchStrategyModelMarketDivergencePublicPayloadItem(key, "safe value")

    for value in (
        "candidate_id abc",
        "market_id abc",
        "market_slug abc",
        "market_question abc",
        "source_url http://example.invalid",
        "source_text hidden",
        "dsn hidden",
        "table_name hidden",
        "token hidden",
        "wallet hidden",
        "order hidden",
        "trade hidden",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchStrategyModelMarketDivergencePublicPayloadItem("safe_key", value)


def test_no_live_execution_or_sensitive_public_surfaces_are_exposed() -> None:
    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )
    sensitive_public_terms = (
        "candidate_id",
        "market_id",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        ResearchStrategyModelMarketDivergenceConfig,
        ResearchStrategyModelMarketDivergencePublicPayloadItem,
        ResearchStrategyModelMarketDivergenceRow,
        ResearchStrategyModelMarketDivergenceReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_terms)
            assert not any(term in lowered for term in sensitive_public_terms)

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
