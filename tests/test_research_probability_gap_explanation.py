from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def _module():
    from polymarket_alpha_lab import research_probability_gap_explanation

    return research_probability_gap_explanation


def _input(
    redacted_candidate_ref: str = "candidate_ref_alpha",
    *,
    probability_gap: Decimal = Decimal("0.010000"),
    evidence_quality_score: Decimal = Decimal("0.900000"),
    base_rate_drift: Decimal = Decimal("0.010000"),
    source_conflict_score: Decimal = Decimal("0.020000"),
):
    gap = _module()
    return gap.ResearchProbabilityGapExplanationInput(
        redacted_candidate_ref=redacted_candidate_ref,
        probability_gap=probability_gap,
        evidence_quality_score=evidence_quality_score,
        base_rate_drift=base_rate_drift,
        source_conflict_score=source_conflict_score,
    )


def _config():
    return _module().ResearchProbabilityGapExplanationConfig(
        config_version="research-probability-gap-explanation-test",
        watch_probability_gap=Decimal("0.030000"),
        block_probability_gap=Decimal("0.100000"),
        watch_min_evidence_quality_score=Decimal("0.600000"),
        block_min_evidence_quality_score=Decimal("0.300000"),
        watch_base_rate_drift=Decimal("0.040000"),
        block_base_rate_drift=Decimal("0.120000"),
        watch_source_conflict_score=Decimal("0.250000"),
        block_source_conflict_score=Decimal("0.550000"),
    )


def _report(rows):
    gap = _module()
    return gap.build_research_probability_gap_explanation_report(
        rows,
        config=_config(),
        generated_at=GENERATED_AT,
    )


def test_probability_gap_explanation_reports_pass_watch_and_block_statuses() -> None:
    report = _report(
        (
            _input(
                "candidate_ref_pass",
                probability_gap=Decimal("0.010000"),
                evidence_quality_score=Decimal("0.900000"),
                base_rate_drift=Decimal("0.010000"),
                source_conflict_score=Decimal("0.020000"),
            ),
            _input(
                "candidate_ref_watch",
                probability_gap=Decimal("0.050000"),
                evidence_quality_score=Decimal("0.500000"),
                base_rate_drift=Decimal("0.050000"),
                source_conflict_score=Decimal("0.300000"),
            ),
            _input(
                "candidate_ref_block",
                probability_gap=Decimal("-0.150000"),
                evidence_quality_score=Decimal("0.200000"),
                base_rate_drift=Decimal("0.200000"),
                source_conflict_score=Decimal("0.600000"),
            ),
        ),
    )

    assert report.status == "block"
    assert report.pass_count == Decimal("1")
    assert report.watch_count == Decimal("1")
    assert report.block_count == Decimal("1")
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert report.rows[0].redacted_candidate_ref == "candidate_ref_block"
    assert report.rows[0].probability_gap_direction == "below_reference"
    assert "source_conflict_block" in report.rows[0].explanation_codes
    assert report.rows[1].status == "watch"
    assert report.rows[2].status == "pass"


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    (
        ("probability_gap", 0.01),
        ("evidence_quality_score", 1),
        ("base_rate_drift", "0.010000"),
        ("source_conflict_score", Decimal("NaN")),
    ),
)
def test_probability_gap_explanation_rejects_non_exact_decimal_values(
    field_name: str,
    field_value: object,
) -> None:
    gap = _module()
    kwargs = {
        "redacted_candidate_ref": "candidate_ref_alpha",
        "probability_gap": Decimal("0.010000"),
        "evidence_quality_score": Decimal("0.900000"),
        "base_rate_drift": Decimal("0.010000"),
        "source_conflict_score": Decimal("0.020000"),
    }
    kwargs[field_name] = field_value

    with pytest.raises(ValueError, match=field_name):
        gap.ResearchProbabilityGapExplanationInput(**kwargs)


@pytest.mark.parametrize(
    "unsafe_ref",
    (
        "candidate_raw_123",
        "market_123",
        "slug-election-2028",
        "question-will-this-happen",
        "https://example.com/source",
        "source_ref_abc",
        "table_predictions",
        "postgres://dsn",
        "token_secret",
        "wallet_0xabc",
        "auth_header",
        "order_entry",
        "trade_ticket",
        "position_size",
    ),
)
def test_probability_gap_explanation_rejects_leaking_public_identifiers(
    unsafe_ref: str,
) -> None:
    with pytest.raises(ValueError, match="redacted_candidate_ref"):
        _input(redacted_candidate_ref=unsafe_ref)


def test_probability_gap_explanation_public_payload_keeps_hard_flags_and_safe_surface() -> None:
    gap = _module()
    report = _report((_input("candidate_ref_safe"),))

    payload = gap.research_probability_gap_explanation_payload(report)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["paper_only"] is True
    assert payload["rows"][0]["report_only"] is True
    assert payload["rows"][0]["readonly"] is True
    flattened = repr(payload).lower()
    for forbidden in (
        "raw",
        "market",
        "slug",
        "question",
        "source_ref",
        "url",
        "http",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    ):
        assert forbidden not in flattened


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_probability_gap_explanation_rejects_false_hard_flags(flag_name: str) -> None:
    gap = _module()
    kwargs = {
        "config_version": "research-probability-gap-explanation-test",
        "watch_probability_gap": Decimal("0.030000"),
        "block_probability_gap": Decimal("0.100000"),
        "watch_min_evidence_quality_score": Decimal("0.600000"),
        "block_min_evidence_quality_score": Decimal("0.300000"),
        "watch_base_rate_drift": Decimal("0.040000"),
        "block_base_rate_drift": Decimal("0.120000"),
        "watch_source_conflict_score": Decimal("0.250000"),
        "block_source_conflict_score": Decimal("0.550000"),
        flag_name: False,
    }

    with pytest.raises(ValueError, match=flag_name):
        gap.ResearchProbabilityGapExplanationConfig(**kwargs)


def test_probability_gap_explanation_report_and_digest_are_deterministic() -> None:
    gap = _module()
    rows = (
        _input("candidate_ref_low", probability_gap=Decimal("0.010000")),
        _input("candidate_ref_high", probability_gap=Decimal("0.090000")),
    )

    report_a = _report(rows)
    report_b = _report(tuple(reversed(rows)))
    payload_a = gap.research_probability_gap_explanation_payload(report_a)
    payload_b = gap.research_probability_gap_explanation_payload(report_b)

    assert payload_a == payload_b
    assert gap.research_probability_gap_explanation_digest(report_a) == (
        gap.research_probability_gap_explanation_digest(report_b)
    )
    assert tuple(row.redacted_candidate_ref for row in report_a.rows) == (
        "candidate_ref_high",
        "candidate_ref_low",
    )


def test_probability_gap_explanation_dataclasses_are_frozen() -> None:
    gap = _module()
    row = _input()

    with pytest.raises(FrozenInstanceError):
        row.redacted_candidate_ref = "candidate_ref_changed"

    report = _report((row,))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
