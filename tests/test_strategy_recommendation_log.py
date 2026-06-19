from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_strategy_selection_policy import (
    PaperStrategySelectionPolicyReport,
    PaperStrategySelectionPolicyRow,
)
from polymarket_alpha_lab.strategy_candidate_recommendation import (
    PaperStrategyCandidateRecommendationReport,
    PaperStrategyCandidateRecommendationRow,
)
from polymarket_alpha_lab.strategy_recommendation_explain import (
    PaperStrategyRecommendationExplanationReport,
    PaperStrategyRecommendationExplanationRow,
)
from polymarket_alpha_lab.strategy_recommendation_bundle import (
    PaperStrategyRecommendationBundleReport,
)
from polymarket_alpha_lab.strategy_recommendation_log import (
    _json_ready,
    append_paper_strategy_recommendation_bundle_log,
    read_paper_strategy_recommendation_bundle_log,
)


GENERATED_AT = datetime(2026, 6, 18, 16, 0, tzinfo=UTC)


class PaperStrategyRecommendationBundleReportSubclass(
    PaperStrategyRecommendationBundleReport
):
    pass


def _recommendation_report(
    *,
    market_slug: str = "market-alpha",
    score: Decimal = Decimal("0.750000"),
) -> PaperStrategyCandidateRecommendationReport:
    return PaperStrategyCandidateRecommendationReport(
        generated_at=GENERATED_AT,
        config_version="strategy-candidate-recommendation-v1",
        readiness_overall_status="pass",
        candidate_count=1,
        recommend_count=1,
        watch_count=0,
        reject_count=0,
        recommendation_rows=(
            PaperStrategyCandidateRecommendationRow(
                market_slug=market_slug,
                question=f"Will {market_slug} resolve yes?",
                action="recommend",
                assessment_status="ready",
                readiness_status="pass",
                selected_side="yes",
                scoring_side="yes",
                recommendation_score=score,
                reason_codes=("assessment_ready", "readiness_passed"),
            ),
        ),
    )


def _selection_report(
    *,
    market_slug: str = "market-alpha",
    score: Decimal = Decimal("0.750000"),
    notional: Decimal = Decimal("7.500000"),
) -> PaperStrategySelectionPolicyReport:
    return PaperStrategySelectionPolicyReport(
        generated_at=GENERATED_AT,
        config_version="paper-strategy-selection-policy-v1",
        row_count=1,
        selected_count=1,
        skipped_count=0,
        not_selected_count=0,
        total_selected_notional=notional,
        selection_rows=(
            PaperStrategySelectionPolicyRow(
                market_slug=market_slug,
                question=f"Will {market_slug} resolve yes?",
                source_action="recommend",
                selected_side="yes",
                recommendation_score=score,
                decision="selected",
                suggested_position_notional=notional,
                selected_position_notional=notional,
                reason_codes=(
                    "selected_by_policy",
                    "assessment_ready",
                    "readiness_passed",
                ),
            ),
        ),
    )


def _explanation_report(
    *,
    market_slug: str = "market-alpha",
    score: Decimal = Decimal("0.750000"),
) -> PaperStrategyRecommendationExplanationReport:
    return PaperStrategyRecommendationExplanationReport(
        generated_at=GENERATED_AT,
        source_config_version="strategy-candidate-recommendation-v1",
        recommendation_count=1,
        recommend_count=1,
        watch_count=0,
        reject_count=0,
        explanation_rows=(
            PaperStrategyRecommendationExplanationRow(
                market_slug=market_slug,
                action="recommend",
                selected_side="yes",
                recommendation_score=score,
                primary_reason_code="assessment_ready",
                reason_codes=("assessment_ready", "readiness_passed"),
                explanation=f"recommend yes because assessment_ready (score {score})",
            ),
        ),
    )


def _bundle_report(
    *,
    market_slug: str = "market-alpha",
    score: Decimal = Decimal("0.750000"),
    notional: Decimal = Decimal("7.500000"),
):
    return PaperStrategyRecommendationBundleReport(
        generated_at=GENERATED_AT,
        config_version="strategy-recommendation-bundle-v1",
        candidate_count=1,
        recommend_count=1,
        selected_count=1,
        total_selected_notional=notional,
        recommendation_report=_recommendation_report(
            market_slug=market_slug,
            score=score,
        ),
        selection_policy_report=_selection_report(
            market_slug=market_slug,
            score=score,
            notional=notional,
        ),
        explanation_report=_explanation_report(
            market_slug=market_slug,
            score=score,
        ),
    )


def _assert_jsonable_contains_no_floats(value):
    if isinstance(value, float):
        pytest.fail("jsonable recommendation log payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_jsonable_contains_no_floats(item)
    elif isinstance(value, list):
        for item in value:
            _assert_jsonable_contains_no_floats(item)


def test_empty_existing_file_returns_empty_tuple(tmp_path):
    path = tmp_path / "empty" / "strategy-recommendations.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()

    assert read_paper_strategy_recommendation_bundle_log(path) == ()


def test_read_recommendation_bundle_log_missing_file_propagates_file_not_found(
    tmp_path,
):
    path = tmp_path / "missing" / "strategy-recommendations.jsonl"

    with pytest.raises(FileNotFoundError):
        read_paper_strategy_recommendation_bundle_log(path)


def test_recommendation_bundle_log_appends_jsonl_and_round_trips_reports(tmp_path):
    path = tmp_path / "nested" / "strategy-recommendations.jsonl"
    report = _bundle_report()

    append_paper_strategy_recommendation_bundle_log(path, report)

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["generated_at"] == "2026-06-18T16:00:00+00:00"
    assert payload["config_version"] == "strategy-recommendation-bundle-v1"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert (
        payload["recommendation_report"]["recommendation_rows"][0][
            "recommendation_score"
        ]
        == "0.750000"
    )
    assert (
        payload["selection_policy_report"]["selection_rows"][0][
            "selected_position_notional"
        ]
        == "7.500000"
    )

    recovered = read_paper_strategy_recommendation_bundle_log(path)
    assert recovered == (report,)
    assert type(recovered[0]) is PaperStrategyRecommendationBundleReport
    assert (
        recovered[0]
        .recommendation_report.recommendation_rows[0]
        .recommendation_score
        == Decimal("0.750000")
    )
    assert (
        recovered[0]
        .selection_policy_report.selection_rows[0]
        .selected_position_notional
        == Decimal("7.500000")
    )


def test_recommendation_bundle_log_skips_blank_lines(tmp_path):
    path = tmp_path / "strategy-recommendations.jsonl"
    first = _bundle_report(market_slug="market-alpha")
    second = _bundle_report(
        market_slug="market-beta",
        score=Decimal("0.500000"),
        notional=Decimal("5.000000"),
    )

    append_paper_strategy_recommendation_bundle_log(path, first)
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n")
    append_paper_strategy_recommendation_bundle_log(path, second)

    assert read_paper_strategy_recommendation_bundle_log(path) == (first, second)


def test_recommendation_bundle_log_reads_legacy_minimal_rows_without_hard_flags(
    tmp_path,
):
    path = tmp_path / "strategy-recommendations.jsonl"
    report = _bundle_report()
    append_paper_strategy_recommendation_bundle_log(path, report)
    payload = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    for report_payload in (
        payload,
        payload["recommendation_report"],
        payload["selection_policy_report"],
        payload["explanation_report"],
    ):
        report_payload.pop("paper_only")
        report_payload.pop("report_only")
        report_payload.pop("readonly")
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")

    assert read_paper_strategy_recommendation_bundle_log(path) == (report,)


def test_recommendation_bundle_log_json_ready_serializes_summary_shapes_without_floats():
    @dataclass(frozen=True)
    class ReasonCount:
        reason_code: str
        count: int
        share: Decimal

    @dataclass(frozen=True)
    class RecommendationSummary:
        score_mean: Decimal
        score_quantiles: tuple[Decimal, Decimal]
        reason_count_pairs: tuple[tuple[str, int], ...]
        reason_count_rows: tuple[ReasonCount, ...]

    payload = _json_ready(
        RecommendationSummary(
            score_mean=Decimal("0.750000"),
            score_quantiles=(Decimal("0.500000"), Decimal("0.900000")),
            reason_count_pairs=(("assessment_ready", 2), ("readiness_passed", 1)),
            reason_count_rows=(
                ReasonCount(
                    reason_code="assessment_ready",
                    count=2,
                    share=Decimal("0.666667"),
                ),
            ),
        ),
    )

    assert payload == {
        "score_mean": "0.750000",
        "score_quantiles": ["0.500000", "0.900000"],
        "reason_count_pairs": [["assessment_ready", 2], ["readiness_passed", 1]],
        "reason_count_rows": [
            {
                "reason_code": "assessment_ready",
                "count": 2,
                "share": "0.666667",
            },
        ],
    }
    _assert_jsonable_contains_no_floats(payload)
    encoded = json.dumps(payload, allow_nan=False, sort_keys=True)
    assert '"0.750000"' in encoded
    assert '"0.666667"' in encoded


def test_recommendation_bundle_log_invalid_json_reports_line_number(tmp_path):
    path = tmp_path / "strategy-recommendations.jsonl"
    report = _bundle_report()
    append_paper_strategy_recommendation_bundle_log(path, report)
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n")
        handle.write("not json\n")

    with pytest.raises(ValueError, match="strategy recommendation bundle log line 3"):
        read_paper_strategy_recommendation_bundle_log(path)


def test_recommendation_bundle_log_invalid_row_reports_line_number(tmp_path):
    path = tmp_path / "strategy-recommendations.jsonl"
    report = _bundle_report()
    append_paper_strategy_recommendation_bundle_log(path, report)
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n")
        handle.write('{"paper_only": true, "report_only": true, "readonly": true}\n')

    with pytest.raises(
        ValueError,
        match="strategy recommendation bundle log line 3 is not a valid report",
    ):
        read_paper_strategy_recommendation_bundle_log(path)


def test_recommendation_bundle_log_malformed_decimal_reports_line_number(tmp_path):
    path = tmp_path / "strategy-recommendations.jsonl"
    report = _bundle_report()
    append_paper_strategy_recommendation_bundle_log(path, report)
    payload = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    payload["total_selected_notional"] = "not-a-decimal"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")

    with pytest.raises(
        ValueError,
        match="strategy recommendation bundle log line 2 is not a valid report",
    ):
        read_paper_strategy_recommendation_bundle_log(path)


def test_recommendation_bundle_log_false_top_level_hard_flag_reports_line_number(
    tmp_path,
):
    path = tmp_path / "strategy-recommendations.jsonl"
    report = _bundle_report()
    append_paper_strategy_recommendation_bundle_log(path, report)
    payload = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    payload["readonly"] = False
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")

    with pytest.raises(
        ValueError,
        match="strategy recommendation bundle log line 2 is not a valid report",
    ):
        read_paper_strategy_recommendation_bundle_log(path)


def test_recommendation_bundle_log_false_nested_hard_flag_reports_line_number(
    tmp_path,
):
    path = tmp_path / "strategy-recommendations.jsonl"
    report = _bundle_report()
    append_paper_strategy_recommendation_bundle_log(path, report)
    payload = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    payload["selection_policy_report"]["readonly"] = False
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")

    with pytest.raises(
        ValueError,
        match="strategy recommendation bundle log line 2 is not a valid report",
    ):
        read_paper_strategy_recommendation_bundle_log(path)


def test_recommendation_bundle_log_rejects_string_reason_codes(tmp_path):
    path = tmp_path / "strategy-recommendations.jsonl"
    report = _bundle_report()
    append_paper_strategy_recommendation_bundle_log(path, report)
    payload = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    payload["recommendation_report"]["recommendation_rows"][0]["reason_codes"] = (
        "not-an-array"
    )
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")

    with pytest.raises(
        ValueError,
        match="strategy recommendation bundle log line 2 is not a valid report",
    ):
        read_paper_strategy_recommendation_bundle_log(path)


def test_recommendation_bundle_log_rejects_non_bundle_reports_without_writing(
    tmp_path,
):
    path = tmp_path / "strategy-recommendations.jsonl"

    with pytest.raises(ValueError, match="PaperStrategyRecommendationBundleReport"):
        append_paper_strategy_recommendation_bundle_log(path, object())
    assert not path.exists()


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_recommendation_bundle_log_rejects_reports_with_false_hard_flags(
    tmp_path,
    flag_name,
):
    path = tmp_path / "strategy-recommendations.jsonl"
    report = _bundle_report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        append_paper_strategy_recommendation_bundle_log(path, report)

    assert not path.exists()


def test_recommendation_bundle_log_rejects_nested_non_paper_readonly_reports(
    tmp_path,
):
    path = tmp_path / "strategy-recommendations.jsonl"
    report = _bundle_report()
    object.__setattr__(report.selection_policy_report, "readonly", False)

    with pytest.raises(ValueError, match="selection_policy_report.*readonly"):
        append_paper_strategy_recommendation_bundle_log(path, report)

    assert not path.exists()


def test_recommendation_bundle_log_rejects_subclass_reports(tmp_path):
    path = tmp_path / "strategy-recommendations.jsonl"
    report = PaperStrategyRecommendationBundleReportSubclass(
        generated_at=GENERATED_AT,
        config_version="strategy-recommendation-bundle-v1",
        candidate_count=1,
        recommend_count=1,
        selected_count=1,
        total_selected_notional=Decimal("7.500000"),
        recommendation_report=_recommendation_report(),
        selection_policy_report=_selection_report(),
        explanation_report=_explanation_report(),
    )

    with pytest.raises(ValueError, match="PaperStrategyRecommendationBundleReport"):
        append_paper_strategy_recommendation_bundle_log(path, report)
