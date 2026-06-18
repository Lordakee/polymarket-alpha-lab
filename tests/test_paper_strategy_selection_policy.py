from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

import pytest

try:
    from polymarket_alpha_lab.strategy_candidate_recommendation import (
        PaperStrategyCandidateRecommendationReport as UpstreamRecommendationReport,
    )
except ModuleNotFoundError:
    UpstreamRecommendationReport = None

from polymarket_alpha_lab.paper_strategy_selection_policy import (
    PaperStrategySelectionPolicyConfig,
    PaperStrategySelectionPolicyReport,
    PaperStrategySelectionPolicyRow,
    build_paper_strategy_selection_policy_report,
)


GENERATED_AT = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
ZERO_NOTIONAL = Decimal("0.000000")


@dataclass(frozen=True)
class RecommendationRow:
    market_slug: str
    question: str
    action: str
    selected_side: str
    recommendation_score: Decimal
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class PaperStrategyCandidateRecommendationReport:
    recommendation_rows: tuple[RecommendationRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def recommendation_row(
    market_slug: str = "fed-cut-june-2026",
    *,
    question: str = "Will the Fed cut rates by June 2026?",
    action: str = "recommend",
    selected_side: str = "yes",
    recommendation_score: Decimal = Decimal("1.000000"),
    reason_codes: tuple[str, ...] = ("candidate_recommended",),
) -> RecommendationRow:
    return RecommendationRow(
        market_slug=market_slug,
        question=question,
        action=action,
        selected_side=selected_side,
        recommendation_score=recommendation_score,
        reason_codes=reason_codes,
    )


def recommendation_report(
    rows: tuple[RecommendationRow, ...],
    *,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> object:
    if UpstreamRecommendationReport is None:
        return PaperStrategyCandidateRecommendationReport(
            recommendation_rows=rows,
            paper_only=paper_only,
            report_only=report_only,
            readonly=readonly,
        )
    report = object.__new__(UpstreamRecommendationReport)
    object.__setattr__(report, "recommendation_rows", rows)
    object.__setattr__(report, "paper_only", paper_only)
    object.__setattr__(report, "report_only", report_only)
    object.__setattr__(report, "readonly", readonly)
    return report


def policy_config(**overrides: object) -> PaperStrategySelectionPolicyConfig:
    values = {
        "config_version": "selection-policy-v1",
        "base_position_notional": Decimal("10.000000"),
        "max_position_notional": Decimal("100.000000"),
        "max_total_notional": Decimal("100.000000"),
    }
    values.update(overrides)
    return PaperStrategySelectionPolicyConfig(**values)


def build_report(
    rows: tuple[RecommendationRow, ...],
    *,
    config: PaperStrategySelectionPolicyConfig | None = None,
) -> PaperStrategySelectionPolicyReport:
    return build_paper_strategy_selection_policy_report(
        recommendation_report(rows),
        config=config or policy_config(),
        generated_at=GENERATED_AT,
    )


def test_selection_policy_selects_recommendations_under_caps_in_source_order():
    report = build_report(
        (
            recommendation_row(
                "fed-cut-june-2026",
                recommendation_score=Decimal("0.500000"),
                reason_codes=("high_edge",),
            ),
            recommendation_row(
                "inflation-above-three-2026",
                question="Will inflation be above 3% in 2026?",
                selected_side="no",
                recommendation_score=Decimal("0.750000"),
                reason_codes=("strong_no_edge",),
            ),
        ),
        config=policy_config(base_position_notional=Decimal("20.000000")),
    )

    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "selection-policy-v1"
    assert report.row_count == 2
    assert report.selected_count == 2
    assert report.skipped_count == 0
    assert report.not_selected_count == 0
    assert report.total_selected_notional == Decimal("25.000000")
    assert tuple(row.market_slug for row in report.selection_rows) == (
        "fed-cut-june-2026",
        "inflation-above-three-2026",
    )
    assert report.selection_rows[0].decision == "selected"
    assert report.selection_rows[0].suggested_position_notional == Decimal("10.000000")
    assert report.selection_rows[0].selected_position_notional == Decimal("10.000000")
    assert report.selection_rows[0].reason_codes == ("selected_by_policy", "high_edge")
    assert report.selection_rows[1].selected_side == "no"
    assert report.selection_rows[1].suggested_position_notional == Decimal("15.000000")
    assert report.selection_rows[1].selected_position_notional == Decimal("15.000000")


def test_selection_policy_applies_per_position_cap_before_selecting():
    report = build_report(
        (
            recommendation_row(
                recommendation_score=Decimal("1.000000"),
                reason_codes=("outsized_score",),
            ),
        ),
        config=policy_config(
            base_position_notional=Decimal("25.000000"),
            max_position_notional=Decimal("12.345678"),
        ),
    )

    row = report.selection_rows[0]
    assert row.decision == "selected"
    assert row.suggested_position_notional == Decimal("12.345678")
    assert row.selected_position_notional == Decimal("12.345678")
    assert report.total_selected_notional == Decimal("12.345678")


def test_selection_policy_skips_recommendations_after_total_cap_is_reached():
    report = build_report(
        (
            recommendation_row("first", recommendation_score=Decimal("1.000000")),
            recommendation_row("cap-breaker", recommendation_score=Decimal("1.000000")),
            recommendation_row("later-recommend", recommendation_score=Decimal("1.000000")),
            recommendation_row(
                "later-watch",
                action="watch",
                recommendation_score=Decimal("0.900000"),
                reason_codes=("watchlist_only",),
            ),
        ),
        config=policy_config(max_total_notional=Decimal("15.000000")),
    )

    assert tuple(row.decision for row in report.selection_rows) == (
        "selected",
        "skipped",
        "skipped",
        "not_selected",
    )
    assert report.selected_count == 1
    assert report.skipped_count == 2
    assert report.not_selected_count == 1
    assert report.total_selected_notional == Decimal("10.000000")
    assert report.selection_rows[1].suggested_position_notional == Decimal("10.000000")
    assert report.selection_rows[1].selected_position_notional == ZERO_NOTIONAL
    assert report.selection_rows[1].reason_codes[0] == "total_notional_cap_reached"
    assert report.selection_rows[2].suggested_position_notional == Decimal("10.000000")
    assert report.selection_rows[2].reason_codes[0] == "total_notional_cap_reached"
    assert report.selection_rows[3].reason_codes == (
        "source_action_watch",
        "watchlist_only",
    )


def test_selection_policy_marks_watch_and_reject_inputs_not_selected():
    report = build_report(
        (
            recommendation_row(
                "watch-market",
                action="watch",
                recommendation_score=Decimal("0.750000"),
                reason_codes=("needs_more_liquidity",),
            ),
            recommendation_row(
                "reject-market",
                action="reject",
                recommendation_score=Decimal("0.100000"),
                reason_codes=("below_threshold",),
            ),
        ),
    )

    assert report.selected_count == 0
    assert report.skipped_count == 0
    assert report.not_selected_count == 2
    assert report.total_selected_notional == ZERO_NOTIONAL
    assert tuple(row.decision for row in report.selection_rows) == (
        "not_selected",
        "not_selected",
    )
    assert tuple(row.selected_position_notional for row in report.selection_rows) == (
        ZERO_NOTIONAL,
        ZERO_NOTIONAL,
    )
    assert report.selection_rows[0].reason_codes == (
        "source_action_watch",
        "needs_more_liquidity",
    )
    assert report.selection_rows[1].reason_codes == (
        "source_action_reject",
        "below_threshold",
    )


def test_selection_policy_validates_source_report_type_and_paper_flags():
    rows = (recommendation_row(),)

    with pytest.raises(ValueError, match="PaperStrategyCandidateRecommendationReport"):
        build_paper_strategy_selection_policy_report(
            object(),
            config=policy_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only"):
        build_paper_strategy_selection_policy_report(
            recommendation_report(rows, paper_only=False),
            config=policy_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="report_only"):
        build_paper_strategy_selection_policy_report(
            recommendation_report(rows, report_only=False),
            config=policy_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="readonly"):
        build_paper_strategy_selection_policy_report(
            recommendation_report(rows, readonly=False),
            config=policy_config(),
            generated_at=GENERATED_AT,
        )


def test_selection_policy_report_constructor_validates_counts_and_total():
    selected_row = PaperStrategySelectionPolicyRow(
        market_slug="selected",
        question="Will this selected market resolve yes?",
        source_action="recommend",
        selected_side="yes",
        recommendation_score=Decimal("1.000000"),
        decision="selected",
        suggested_position_notional=Decimal("5.000000"),
        selected_position_notional=Decimal("5.000000"),
        reason_codes=("selected_by_policy",),
    )
    not_selected_row = PaperStrategySelectionPolicyRow(
        market_slug="watch",
        question="Will this watch market resolve yes?",
        source_action="watch",
        selected_side="none",
        recommendation_score=Decimal("0.500000"),
        decision="not_selected",
        suggested_position_notional=ZERO_NOTIONAL,
        selected_position_notional=ZERO_NOTIONAL,
        reason_codes=("source_action_watch",),
    )

    PaperStrategySelectionPolicyReport(
        generated_at=GENERATED_AT,
        config_version="selection-policy-v1",
        row_count=2,
        selected_count=1,
        skipped_count=0,
        not_selected_count=1,
        total_selected_notional=Decimal("5.000000"),
        selection_rows=(selected_row, not_selected_row),
    )
    with pytest.raises(ValueError, match="row_count"):
        PaperStrategySelectionPolicyReport(
            generated_at=GENERATED_AT,
            config_version="selection-policy-v1",
            row_count=3,
            selected_count=1,
            skipped_count=0,
            not_selected_count=1,
            total_selected_notional=Decimal("5.000000"),
            selection_rows=(selected_row, not_selected_row),
        )
    with pytest.raises(ValueError, match="selected_count"):
        PaperStrategySelectionPolicyReport(
            generated_at=GENERATED_AT,
            config_version="selection-policy-v1",
            row_count=2,
            selected_count=2,
            skipped_count=0,
            not_selected_count=0,
            total_selected_notional=Decimal("5.000000"),
            selection_rows=(selected_row, not_selected_row),
        )
    with pytest.raises(ValueError, match="total_selected_notional"):
        PaperStrategySelectionPolicyReport(
            generated_at=GENERATED_AT,
            config_version="selection-policy-v1",
            row_count=2,
            selected_count=1,
            skipped_count=0,
            not_selected_count=1,
            total_selected_notional=Decimal("4.000000"),
            selection_rows=(selected_row, not_selected_row),
        )


def test_selection_policy_rejects_zero_sizing_config_and_invalid_selected_rows():
    with pytest.raises(ValueError, match="base_position_notional"):
        policy_config(base_position_notional=ZERO_NOTIONAL)
    with pytest.raises(ValueError, match="max_position_notional"):
        policy_config(max_position_notional=ZERO_NOTIONAL)
    with pytest.raises(ValueError, match="max_total_notional"):
        policy_config(max_total_notional=ZERO_NOTIONAL)

    with pytest.raises(ValueError, match="selected side"):
        PaperStrategySelectionPolicyRow(
            market_slug="no-side-selected",
            question="Will this no-side selection resolve yes?",
            source_action="recommend",
            selected_side="none",
            recommendation_score=Decimal("1.000000"),
            decision="selected",
            suggested_position_notional=Decimal("5.000000"),
            selected_position_notional=Decimal("5.000000"),
            reason_codes=("selected_by_policy",),
        )
    with pytest.raises(ValueError, match="positive selected_position_notional"):
        PaperStrategySelectionPolicyRow(
            market_slug="zero-selected",
            question="Will this zero selection resolve yes?",
            source_action="recommend",
            selected_side="yes",
            recommendation_score=Decimal("1.000000"),
            decision="selected",
            suggested_position_notional=ZERO_NOTIONAL,
            selected_position_notional=ZERO_NOTIONAL,
            reason_codes=("selected_by_policy",),
        )
