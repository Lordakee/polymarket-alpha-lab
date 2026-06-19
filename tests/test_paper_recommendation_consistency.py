from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module

import pytest


GENERATED_AT = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)
CONFIG_VERSION = "recommendation-consistency-v1"
QUANTUM = Decimal("0.000001")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _IntSubclass(int):
    pass


def _api():
    try:
        module = import_module("polymarket_alpha_lab.paper_recommendation_consistency")
    except ModuleNotFoundError as exc:
        pytest.fail(f"paper recommendation consistency module is missing: {exc}")
    return module


def _config(**overrides: object) -> PaperRecommendationConsistencyConfig:
    values = {
        "config_version": CONFIG_VERSION,
        "max_edge_spread": Decimal("0.020000"),
        "max_score_spread": Decimal("0.050000"),
        "min_source_count": 2,
    }
    values.update(overrides)
    return _api().PaperRecommendationConsistencyConfig(**values)


def _fact(
    market_slug: str,
    side: str,
    source_name: str,
    *,
    action_or_status: str = "recommend",
    net_probability_edge: Decimal = Decimal("0.100000"),
    recommendation_score: Decimal = Decimal("0.700000"),
    reason_codes: tuple[str, ...] = ("recommendation_ready",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperRecommendationConsistencyFact:
    return _api().PaperRecommendationConsistencyFact(
        market_slug=market_slug,
        side=side,
        source_name=source_name,
        action_or_status=action_or_status,
        net_probability_edge=net_probability_edge,
        recommendation_score=recommendation_score,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    facts: tuple[PaperRecommendationConsistencyFact, ...],
    *,
    config: PaperRecommendationConsistencyConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> PaperRecommendationConsistencyReport:
    return _api().build_paper_recommendation_consistency_report(
        facts,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_consistency_passes_when_sources_agree_within_spread_caps():
    report = _report(
        (
            _fact(
                "beta-market",
                "no",
                "risk_budget",
                net_probability_edge=Decimal("0.0500004"),
                recommendation_score=Decimal("0.5000004"),
            ),
            _fact(
                "alpha-market",
                "yes",
                "risk_budget",
                net_probability_edge=Decimal("0.1000004"),
                recommendation_score=Decimal("0.7000004"),
                reason_codes=("risk_budget_passed",),
            ),
            _fact(
                "alpha-market",
                "yes",
                "thresholds",
                net_probability_edge=Decimal("0.1100004"),
                recommendation_score=Decimal("0.7250004"),
                reason_codes=("thresholds_passed",),
            ),
            _fact(
                "beta-market",
                "no",
                "thresholds",
                net_probability_edge=Decimal("0.0550004"),
                recommendation_score=Decimal("0.5050004"),
            ),
        ),
    )

    api = _api()

    assert isinstance(report, api.PaperRecommendationConsistencyReport)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == CONFIG_VERSION
    assert report.group_count == 2
    assert report.pass_count == 2
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.consistency_rows == (
        api.PaperRecommendationConsistencyRow(
            market_slug="alpha-market",
            side="yes",
            source_count=2,
            distinct_statuses=("recommend",),
            edge_min=Decimal("0.100000"),
            edge_max=Decimal("0.110000"),
            edge_spread=Decimal("0.010000"),
            score_min=Decimal("0.700000"),
            score_max=Decimal("0.725000"),
            score_spread=Decimal("0.025000"),
            consistency_status="pass",
            reason_codes=("recommendation_consistency_passed",),
        ),
        api.PaperRecommendationConsistencyRow(
            market_slug="beta-market",
            side="no",
            source_count=2,
            distinct_statuses=("recommend",),
            edge_min=Decimal("0.050000"),
            edge_max=Decimal("0.055000"),
            edge_spread=Decimal("0.005000"),
            score_min=Decimal("0.500000"),
            score_max=Decimal("0.505000"),
            score_spread=Decimal("0.005000"),
            consistency_status="pass",
            reason_codes=("recommendation_consistency_passed",),
        ),
    )
    assert report.reason_codes == ("recommendation_consistency_passed",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_consistency_watches_when_source_count_is_below_minimum():
    report = _report(
        (
            _fact(
                "single-source-market",
                "yes",
                "thresholds",
                net_probability_edge=Decimal("0.100000"),
                recommendation_score=Decimal("0.700000"),
            ),
        ),
        config=_config(min_source_count=2),
    )

    row = report.consistency_rows[0]
    assert row.consistency_status == "watch"
    assert row.source_count == 1
    assert row.distinct_statuses == ("recommend",)
    assert row.edge_min == Decimal("0.100000")
    assert row.edge_max == Decimal("0.100000")
    assert row.edge_spread == Decimal("0.000000")
    assert row.score_spread == Decimal("0.000000")
    assert row.reason_codes == ("missing_recommendation_sources",)
    assert report.pass_count == 0
    assert report.watch_count == 1
    assert report.blocked_count == 0
    assert report.reason_codes == ("missing_recommendation_sources",)


def test_consistency_watches_when_statuses_disagree_across_sources():
    report = _report(
        (
            _fact("status-market", "yes", "thresholds", action_or_status="recommend"),
            _fact("status-market", "yes", "risk_budget", action_or_status="watch"),
        ),
    )

    row = report.consistency_rows[0]
    assert row.consistency_status == "watch"
    assert row.distinct_statuses == ("recommend", "watch")
    assert row.reason_codes == ("recommendation_status_disagreement",)
    assert report.reason_codes == ("recommendation_status_disagreement",)


def test_consistency_blocks_when_edge_or_score_spread_is_too_wide():
    report = _report(
        (
            _fact(
                "wide-market",
                "yes",
                "thresholds",
                net_probability_edge=Decimal("0.100000"),
                recommendation_score=Decimal("0.700000"),
            ),
            _fact(
                "wide-market",
                "yes",
                "risk_budget",
                net_probability_edge=Decimal("0.130000"),
                recommendation_score=Decimal("0.760001"),
            ),
        ),
        config=_config(
            max_edge_spread=Decimal("0.020000"),
            max_score_spread=Decimal("0.050000"),
        ),
    )

    row = report.consistency_rows[0]
    assert row.consistency_status == "blocked"
    assert row.edge_spread == Decimal("0.030000")
    assert row.score_spread == Decimal("0.060001")
    assert row.reason_codes == (
        "edge_spread_exceeds_consistency_cap",
        "score_spread_exceeds_consistency_cap",
    )
    assert report.pass_count == 0
    assert report.watch_count == 0
    assert report.blocked_count == 1
    assert report.reason_codes == (
        "edge_spread_exceeds_consistency_cap",
        "score_spread_exceeds_consistency_cap",
    )


def test_consistency_blocks_take_precedence_over_watch_reasons():
    report = _report(
        (
            _fact(
                "mixed-market",
                "yes",
                "thresholds",
                action_or_status="recommend",
                net_probability_edge=Decimal("0.100000"),
                recommendation_score=Decimal("0.700000"),
            ),
            _fact(
                "mixed-market",
                "yes",
                "risk_budget",
                action_or_status="watch",
                net_probability_edge=Decimal("0.130000"),
                recommendation_score=Decimal("0.720000"),
            ),
        ),
    )

    row = report.consistency_rows[0]
    assert row.consistency_status == "blocked"
    assert row.reason_codes == (
        "edge_spread_exceeds_consistency_cap",
        "recommendation_status_disagreement",
    )
    assert report.reason_codes == (
        "edge_spread_exceeds_consistency_cap",
        "recommendation_status_disagreement",
    )


def test_consistency_allows_spreads_at_exact_caps():
    report = _report(
        (
            _fact(
                "exact-cap-market",
                "yes",
                "thresholds",
                net_probability_edge=Decimal("0.100000"),
                recommendation_score=Decimal("0.700000"),
            ),
            _fact(
                "exact-cap-market",
                "yes",
                "risk_budget",
                net_probability_edge=Decimal("0.120000"),
                recommendation_score=Decimal("0.750000"),
            ),
        ),
        config=_config(
            max_edge_spread=Decimal("0.020000"),
            max_score_spread=Decimal("0.050000"),
        ),
    )

    row = report.consistency_rows[0]
    assert row.consistency_status == "pass"
    assert row.edge_spread == Decimal("0.020000")
    assert row.score_spread == Decimal("0.050000")
    assert row.reason_codes == ("recommendation_consistency_passed",)


def test_consistency_orders_rows_and_distinct_statuses_deterministically():
    report = _report(
        (
            _fact("zeta-market", "yes", "b", action_or_status="watch"),
            _fact("alpha-market", "yes", "b", action_or_status="watch"),
            _fact("zeta-market", "yes", "a", action_or_status="blocked"),
            _fact("alpha-market", "no", "b", action_or_status="blocked"),
            _fact("alpha-market", "yes", "a", action_or_status="recommend"),
            _fact("alpha-market", "no", "a", action_or_status="recommend"),
        ),
        config=_config(max_edge_spread=Decimal("1.000000"), max_score_spread=Decimal("1.000000")),
    )

    assert tuple((row.market_slug, row.side) for row in report.consistency_rows) == (
        ("alpha-market", "no"),
        ("alpha-market", "yes"),
        ("zeta-market", "yes"),
    )
    assert tuple(row.distinct_statuses for row in report.consistency_rows) == (
        ("blocked", "recommend"),
        ("recommend", "watch"),
        ("blocked", "watch"),
    )


def test_consistency_empty_facts_returns_blocked_report_without_rows():
    report = _report(())

    assert report.group_count == 0
    assert report.pass_count == 0
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.consistency_rows == ()
    assert report.reason_codes == ("empty_recommendation_facts",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_consistency_config_validates_decimal_caps_and_min_sources():
    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=" consistency-v1")
    with pytest.raises(ValueError, match="max_edge_spread"):
        _config(max_edge_spread=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="max_edge_spread"):
        _config(max_edge_spread=Decimal("0.0100001"))
    with pytest.raises(ValueError, match="max_edge_spread"):
        _config(max_edge_spread=Decimal("-0.000001"))
    with pytest.raises(ValueError, match="max_score_spread"):
        _config(max_score_spread=Decimal("0.0100001"))
    with pytest.raises(ValueError, match="min_source_count"):
        _config(min_source_count=0)
    with pytest.raises(ValueError, match="min_source_count"):
        _config(min_source_count=_IntSubclass(2))


def test_consistency_fact_validates_decimal_only_canonical_fields_and_flags():
    fact = _fact(
        "validated-market",
        "yes",
        "thresholds",
        net_probability_edge=Decimal("0.1234567"),
        recommendation_score=Decimal("0.9876547"),
        reason_codes=("from_source", "threshold_passed"),
    )

    assert fact.net_probability_edge == Decimal("0.123457")
    assert fact.recommendation_score == Decimal("0.987655")
    assert fact.reason_codes == ("from_source", "threshold_passed")

    with pytest.raises(ValueError, match="market_slug"):
        _fact(" validated-market", "yes", "thresholds")
    with pytest.raises(ValueError, match="side"):
        _fact("validated-market", "", "thresholds")
    with pytest.raises(ValueError, match="source_name"):
        _fact("validated-market", "yes", " thresholds")
    with pytest.raises(ValueError, match="action_or_status"):
        _fact("validated-market", "yes", "thresholds", action_or_status=" recommend")
    with pytest.raises(ValueError, match="net_probability_edge"):
        _fact(
            "validated-market",
            "yes",
            "thresholds",
            net_probability_edge=_DecimalSubclass("0.100000"),
        )
    with pytest.raises(ValueError, match="recommendation_score"):
        _fact(
            "validated-market",
            "yes",
            "thresholds",
            recommendation_score=Decimal("NaN"),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        _fact(
            "validated-market",
            "yes",
            "thresholds",
            reason_codes=("duplicate", "duplicate"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        _fact("validated-market", "yes", "thresholds", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _fact("validated-market", "yes", "thresholds", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        _fact("validated-market", "yes", "thresholds", readonly=False)


def test_consistency_report_normalizes_generated_at_to_utc_and_rejects_subclasses():
    report = _report(
        (
            _fact("tz-market", "yes", "thresholds"),
            _fact("tz-market", "yes", "risk_budget"),
        ),
        generated_at=datetime(2026, 6, 19, 14, 0, tzinfo=timezone(timedelta(hours=2))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC

    with pytest.raises(ValueError, match="generated_at"):
        _report(
            (
                _fact("tz-market", "yes", "thresholds"),
                _fact("tz-market", "yes", "risk_budget"),
            ),
            generated_at=_DatetimeSubclass(2026, 6, 19, 12, 0, tzinfo=UTC),
        )


def test_consistency_rows_and_reports_are_frozen_and_validate_consistency():
    report = _report(
        (
            _fact("frozen-market", "yes", "thresholds"),
            _fact("frozen-market", "yes", "risk_budget"),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        report.consistency_rows[0].consistency_status = "blocked"
    with pytest.raises(FrozenInstanceError):
        report.group_count = 2
    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=2)
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            report.consistency_rows[0],
            reason_codes=("edge_spread_exceeds_consistency_cap",),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
