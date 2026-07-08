from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_domain_specialist_score_normalization_report as api
from polymarket_alpha_lab.research_domain_specialist_score_normalization_report import (
    ResearchDomainSpecialistScoreInput,
    ResearchDomainSpecialistScoreNormalizationConfig,
    ResearchDomainSpecialistScoreNormalizationReport,
    build_research_domain_specialist_score_normalization_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _input(
    *,
    domain: str = "politics",
    team_label: str = "politics_alpha",
    observed_at: datetime = NOW,
    raw_research_score: Decimal = Decimal("0.900000"),
    aggregate_calibration_score: Decimal = Decimal("0.900000"),
    evidence_quality_score: Decimal = Decimal("0.850000"),
    capacity_score: Decimal = Decimal("0.800000"),
) -> ResearchDomainSpecialistScoreInput:
    return ResearchDomainSpecialistScoreInput(
        domain=domain,
        team_label=team_label,
        observed_at=observed_at,
        raw_research_score=raw_research_score,
        aggregate_calibration_score=aggregate_calibration_score,
        evidence_quality_score=evidence_quality_score,
        capacity_score=capacity_score,
    )


def _report(
    rows: tuple[ResearchDomainSpecialistScoreInput, ...],
    *,
    config: ResearchDomainSpecialistScoreNormalizationConfig | None = None,
) -> ResearchDomainSpecialistScoreNormalizationReport:
    return build_research_domain_specialist_score_normalization_report(
        rows,
        generated_at=NOW,
        config=config,
    )


def test_normalizes_specialist_scores_across_supported_domains() -> None:
    report = _report(
        (
            _input(
                domain="other",
                team_label="other_alpha",
                observed_at=NOW - timedelta(days=2),
                aggregate_calibration_score=Decimal("0.200000"),
                evidence_quality_score=Decimal("0.200000"),
                capacity_score=Decimal("0.200000"),
            ),
            _input(
                domain="basketball",
                team_label="basketball_alpha",
                raw_research_score=Decimal("0.880000"),
                aggregate_calibration_score=Decimal("0.820000"),
                evidence_quality_score=Decimal("0.780000"),
                capacity_score=Decimal("0.760000"),
            ),
            _input(
                domain="soccer",
                team_label="soccer_alpha",
                raw_research_score=Decimal("0.950000"),
                aggregate_calibration_score=Decimal("0.750000"),
                evidence_quality_score=Decimal("0.800000"),
                capacity_score=Decimal("0.900000"),
            ),
            _input(
                domain="gold",
                team_label="gold_alpha",
                raw_research_score=Decimal("0.750000"),
                aggregate_calibration_score=Decimal("0.850000"),
                evidence_quality_score=Decimal("0.850000"),
                capacity_score=Decimal("0.850000"),
            ),
            _input(
                domain="equities",
                team_label="equities_alpha",
                raw_research_score=Decimal("0.800000"),
                aggregate_calibration_score=Decimal("0.800000"),
                evidence_quality_score=Decimal("0.750000"),
                capacity_score=Decimal("0.900000"),
            ),
            _input(
                domain="crypto",
                team_label="crypto_alpha",
                observed_at=NOW - timedelta(hours=12),
                raw_research_score=Decimal("0.800000"),
                aggregate_calibration_score=Decimal("0.400000"),
                evidence_quality_score=Decimal("0.700000"),
                capacity_score=Decimal("0.700000"),
            ),
            _input(domain="politics", team_label="politics_alpha"),
        ),
    )

    assert tuple(row.domain for row in report.rows) == (
        "politics",
        "crypto",
        "equities",
        "gold",
        "soccer",
        "basketball",
        "other",
    )
    assert report.report_status == "block"
    assert report.domain_count == Decimal("7.000000")
    assert report.team_count == Decimal("7.000000")
    assert report.pass_count == Decimal("5.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert report.average_normalized_score == Decimal("0.603839")

    politics = report.rows[0]
    crypto = report.rows[1]
    other = report.rows[-1]
    assert politics.normalized_score == Decimal("0.794250")
    assert politics.score_status == "pass"
    assert politics.reason_codes == ("normalization_pass",)
    assert crypto.normalized_score == Decimal("0.452000")
    assert crypto.freshness_score == Decimal("0.500000")
    assert crypto.score_status == "watch"
    assert "aggregate_calibration_watch" in crypto.reason_codes
    assert "normalized_score_watch" in crypto.reason_codes
    assert other.normalized_score == Decimal("0.153000")
    assert other.freshness_score == Decimal("0.000000")
    assert other.score_status == "block"
    assert "normalized_score_block" in other.reason_codes
    assert {summary.domain_status for summary in report.domain_summaries} == {
        "pass",
        "watch",
        "block",
    }
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_serializes_decimals_as_strings_and_digest_is_deterministic() -> None:
    inputs = (
        _input(domain="crypto", team_label="crypto_alpha"),
        _input(domain="politics", team_label="politics_alpha"),
    )
    report = _report(inputs)
    reversed_report = _report(tuple(reversed(inputs)))

    payload = report.payload
    json.dumps(payload, sort_keys=True)

    assert report.derived_validation_digest == reversed_report.derived_validation_digest
    assert payload["team_count"] == "2.000000"
    assert payload["rows"][0]["normalized_score"] == "0.794250"
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_non_decimal_public_numbers(report)
    _assert_no_decimal_objects(payload)


def test_frozen_dataclasses_reject_subclassing_and_digest_tampering() -> None:
    report = _report((_input(),))

    with pytest.raises(FrozenInstanceError):
        report.report_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchDomainSpecialistScoreNormalizationConfig):
            pass

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="score_status"):
        replace(report.rows[0], score_status="blocked")


def test_rejects_non_decimal_numeric_inputs_bad_domains_and_hard_flag_downgrades() -> None:
    with pytest.raises(ValueError, match="raw_research_score"):
        _input(raw_research_score=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="domain"):
        _input(domain="hockey")

    with pytest.raises(ValueError, match="timezone-aware"):
        _input(observed_at=datetime(2026, 1, 1))

    with pytest.raises(ValueError, match="observed_at"):
        _report((_input(observed_at=NOW + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="paper_only"):
        ResearchDomainSpecialistScoreNormalizationConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        ResearchDomainSpecialistScoreInput(
            domain="politics",
            team_label="politics_alpha",
            observed_at=NOW,
            raw_research_score=Decimal("0.900000"),
            aggregate_calibration_score=Decimal("0.900000"),
            evidence_quality_score=Decimal("0.850000"),
            capacity_score=Decimal("0.800000"),
            report_only=False,
        )


def test_public_surface_excludes_identifiers_execution_and_sizing_language() -> None:
    unsafe_fragments = (
        "event",
        "market",
        "source",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "execution",
        "recommendation",
        "sizing",
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in unsafe_fragments)

    for cls in (
        ResearchDomainSpecialistScoreNormalizationConfig,
        ResearchDomainSpecialistScoreInput,
        api.ResearchDomainSpecialistScoreNormalizationRow,
        api.ResearchDomainSpecialistScoreDomainSummary,
        ResearchDomainSpecialistScoreNormalizationReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in unsafe_fragments)

    with pytest.raises(ValueError, match="unsafe public"):
        _input(team_label="market_alpha")

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
