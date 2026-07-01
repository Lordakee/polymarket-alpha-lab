from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

from polymarket_alpha_lab.team_diagnostics_cli_format import (
    format_team_diagnostics_cli_lines,
    format_team_diagnostics_cli_stdout,
)


@dataclass(frozen=True)
class MemoryReferenceRow:
    condition_id: str
    market_slug: str
    reason: str
    score: float


@dataclass(frozen=True)
class EvidenceQualityRow:
    label: str
    rows: int
    memory_eligible: bool


def test_format_team_diagnostics_cli_lines_handles_empty_bundle() -> None:
    bundle = SimpleNamespace()

    lines = format_team_diagnostics_cli_lines(bundle)

    assert lines == (
        "team-diagnostics: paper_only=True report_only=True readonly=True",
        (
            "row-counts: calibration=0 event_template_rows=0 "
            "source_reliability_rows=0 evidence_quality_rows=0 "
            "memory_eligible_references=0"
        ),
        "memory-eligible-references: count=0",
        "calibration-summary: bucket_count=0 observation_count=0 brier_mean=n/a ece=n/a",
        "event-template-rows: count=0",
        "source-reliability-rows: count=0",
        "evidence-quality-rows: count=0",
    )


def test_format_team_diagnostics_cli_stdout_joins_lines_with_trailing_newline() -> None:
    bundle = SimpleNamespace()

    stdout = format_team_diagnostics_cli_stdout(bundle)

    assert stdout == (
        "team-diagnostics: paper_only=True report_only=True readonly=True\n"
        "row-counts: calibration=0 event_template_rows=0 "
        "source_reliability_rows=0 evidence_quality_rows=0 "
        "memory_eligible_references=0\n"
        "memory-eligible-references: count=0\n"
        "calibration-summary: bucket_count=0 observation_count=0 brier_mean=n/a ece=n/a\n"
        "event-template-rows: count=0\n"
        "source-reliability-rows: count=0\n"
        "evidence-quality-rows: count=0\n"
    )


def test_format_team_diagnostics_cli_lines_formats_populated_duck_typed_bundle() -> None:
    bundle = SimpleNamespace(
        row_counts={
            "calibration": 4,
            "event_template_rows": 2,
            "source_reliability_rows": 2,
            "evidence_quality_rows": 2,
            "memory_eligible_references": 2,
        },
        memory_eligible_references=(
            {
                "condition_id": "0xz",
                "market_slug": "zeta-election",
                "reason": "quality-threshold",
                "score": 0.911,
            },
            MemoryReferenceRow(
                condition_id="0xa",
                market_slug="alpha-election",
                reason="recent-resolution",
                score=0.82,
            ),
        ),
        calibration_summary={
            "observation_count": 144,
            "bucket_count": 6,
            "brier_mean": 0.1855,
            "ece": 0.04125,
        },
        event_template_rows=(
            {
                "event_type": "macro",
                "template_id": "macro-fed",
                "row_count": 7,
            },
            {
                "event_type": "earnings",
                "template_id": "earnings-large-cap",
                "row_count": 3,
            },
        ),
        source_reliability_rows=(
            {
                "source": "prediction-market",
                "resolved_count": 9,
                "mean_error": 0.12,
            },
            {
                "source": "news-wire",
                "resolved_count": 12,
                "mean_error": 0.31,
            },
        ),
        evidence_quality_rows=(
            EvidenceQualityRow(label="weak", rows=2, memory_eligible=False),
            EvidenceQualityRow(label="strong", rows=5, memory_eligible=True),
        ),
    )

    lines = format_team_diagnostics_cli_lines(bundle)

    assert lines == (
        "team-diagnostics: paper_only=True report_only=True readonly=True",
        (
            "row-counts: calibration=4 event_template_rows=2 "
            "source_reliability_rows=2 evidence_quality_rows=2 "
            "memory_eligible_references=2"
        ),
        "memory-eligible-references: count=2",
        (
            "memory-eligible-reference: condition_id=0xa "
            "market_slug=alpha-election reason=recent-resolution score=0.82"
        ),
        (
            "memory-eligible-reference: condition_id=0xz "
            "market_slug=zeta-election reason=quality-threshold score=0.911"
        ),
        "calibration-summary: bucket_count=6 observation_count=144 brier_mean=0.1855 ece=0.04125",
        "event-template-rows: count=2",
        "event-template-row: event_type=earnings template_id=earnings-large-cap row_count=3",
        "event-template-row: event_type=macro template_id=macro-fed row_count=7",
        "source-reliability-rows: count=2",
        "source-reliability-row: source=news-wire resolved_count=12 mean_error=0.31",
        "source-reliability-row: source=prediction-market resolved_count=9 mean_error=0.12",
        "evidence-quality-rows: count=2",
        "evidence-quality-row: label=strong rows=5 memory_eligible=True",
        "evidence-quality-row: label=weak rows=2 memory_eligible=False",
    )


def test_format_team_diagnostics_cli_lines_derives_rows_from_real_bundle_shape() -> None:
    bundle = SimpleNamespace(
        forecast_row_count=5,
        evidence_row_count=4,
        outcome_row_count=3,
        memory_synthesis_report=SimpleNamespace(
            rows=(
                SimpleNamespace(
                    reference_id="ref-low",
                    team_id="crypto_btc",
                    category_id="finance.crypto.btc",
                    event_template="btc_hit_price",
                    gate_status="low_sample",
                    average_brier_score="0.220000",
                ),
                SimpleNamespace(
                    reference_id="ref-eligible",
                    team_id="crypto_btc",
                    category_id="finance.crypto.btc",
                    event_template="btc_hit_price",
                    gate_status="eligible",
                    average_brier_score="0.110000",
                ),
            ),
        ),
        forecast_calibration_report=SimpleNamespace(
            groups=(
                SimpleNamespace(
                    group_type="team",
                    group_key="crypto_btc",
                    settled_count=3,
                    average_brier_score="0.180000",
                    calibration_error="0.040000",
                ),
            ),
        ),
        event_template_performance_report=SimpleNamespace(
            rows=(
                SimpleNamespace(
                    category_id="finance.crypto.btc",
                    event_template="btc_hit_price",
                    settled_count=3,
                    average_brier_score="0.180000",
                ),
            ),
        ),
        source_reliability_report=SimpleNamespace(
            rows=(
                SimpleNamespace(
                    source_id="source-etf-flow-dashboard",
                    settled_evidence_count=3,
                    average_brier_score="0.170000",
                ),
            ),
        ),
        evidence_quality_report=SimpleNamespace(
            rows=(
                SimpleNamespace(
                    source_id="source-etf-flow-dashboard",
                    status="evidence_quality_pass",
                    quality_score="0.900000",
                ),
            ),
        ),
    )

    lines = format_team_diagnostics_cli_lines(bundle)

    assert lines == (
        "team-diagnostics: paper_only=True report_only=True readonly=True",
        (
            "row-counts: calibration=1 event_template_rows=1 "
            "source_reliability_rows=1 evidence_quality_rows=1 "
            "memory_eligible_references=1"
        ),
        "memory-eligible-references: count=1",
        (
            "memory-eligible-reference: condition_id=crypto_btc "
            "market_slug=btc_hit_price reason=eligible score=0.110000"
        ),
        (
            "calibration-summary: bucket_count=1 observation_count=3 "
            "brier_mean=0.180000 ece=0.040000"
        ),
        "event-template-rows: count=1",
        (
            "event-template-row: event_type=finance.crypto.btc "
            "template_id=btc_hit_price row_count=3"
        ),
        "source-reliability-rows: count=1",
        (
            "source-reliability-row: source=source-etf-flow-dashboard "
            "resolved_count=3 mean_error=0.170000"
        ),
        "evidence-quality-rows: count=1",
        (
            "evidence-quality-row: label=source-etf-flow-dashboard "
            "rows=evidence_quality_pass memory_eligible=0.900000"
        ),
    )
