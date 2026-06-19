import ast
import inspect
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timezone
from decimal import Context, Decimal, localcontext

import pytest

import polymarket_alpha_lab.paper_recommendation_score_explanation as score_explanation
from polymarket_alpha_lab.paper_recommendation_score_explanation import (
    PaperRecommendationScoreComponent,
    PaperRecommendationScoreExplanationReport,
    PaperRecommendationScoreExplanationRow,
    build_paper_recommendation_score_explanation_report,
)


GENERATED_AT = datetime(2026, 6, 18, 16, 30, tzinfo=UTC)


class TaggedDecimal(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def _component(**overrides) -> PaperRecommendationScoreComponent:
    values = {
        "component_name": "probability_edge",
        "contribution": Decimal("0.070000"),
        "direction": "positive",
        "reason_code": "model_price_edge",
        "flags": ("paper_only",),
    }
    values.update(overrides)
    return PaperRecommendationScoreComponent(**values)


def _row(**overrides) -> PaperRecommendationScoreExplanationRow:
    components = overrides.pop(
        "components",
        (
            _component(
                component_name="probability_edge",
                contribution=Decimal("0.070000"),
                direction="positive",
                reason_code="model_price_edge",
                flags=("edge_available",),
            ),
            _component(
                component_name="confidence",
                contribution=Decimal("0.020000"),
                direction="positive",
                reason_code="confidence_supports_edge",
                flags=("confidence_available",),
            ),
            _component(
                component_name="liquidity_depth",
                contribution=Decimal("0.015000"),
                direction="positive",
                reason_code="sufficient_depth",
                flags=("depth_available",),
            ),
            _component(
                component_name="cost_drag",
                contribution=Decimal("-0.010000"),
                direction="negative",
                reason_code="spread_and_slippage_drag",
                flags=("cost_included",),
            ),
            _component(
                component_name="uncertainty_penalty",
                contribution=Decimal("-0.020000"),
                direction="negative",
                reason_code="uncertainty_discount",
                flags=("uncertainty_included",),
            ),
            _component(
                component_name="correlation_penalty",
                contribution=Decimal("-0.005000"),
                direction="negative",
                reason_code="portfolio_correlation_discount",
                flags=("correlation_included",),
            ),
        ),
    )
    values = {
        "market_slug": "market-a",
        "side": "yes",
        "total_score": Decimal("0.070000"),
        "score_status": "pass",
        "components": components,
        "reason_codes": ("candidate_score_explained",),
        "flags": ("paper_only", "report_only", "readonly"),
    }
    values.update(overrides)
    return PaperRecommendationScoreExplanationRow(**values)


def _report(*rows: PaperRecommendationScoreExplanationRow):
    return build_paper_recommendation_score_explanation_report(
        generated_at=GENERATED_AT,
        config_version="paper-recommendation-score-explanation-v0",
        rows=rows,
    )


def test_build_report_sorts_rows_and_summarizes_supplied_scores():
    low = _row(
        market_slug="market-a",
        side="no",
        total_score=Decimal("0.020000"),
        score_status="watch",
        components=(
            _component(
                component_name="probability_edge",
                contribution=Decimal("0.050000"),
                direction="positive",
                reason_code="model_price_edge",
                flags=("edge_available",),
            ),
            _component(
                component_name="cost_drag",
                contribution=Decimal("-0.030000"),
                direction="negative",
                reason_code="spread_and_slippage_drag",
                flags=("cost_included",),
            ),
        ),
    )
    high = _row(
        market_slug="market-c",
        side="yes",
        total_score=Decimal("0.120000"),
        score_status="pass",
        components=(
            _component(
                component_name="probability_edge",
                contribution=Decimal("0.130000"),
                direction="positive",
                reason_code="model_price_edge",
                flags=("depth_available",),
            ),
            _component(
                component_name="cost_drag",
                contribution=Decimal("-0.010000"),
                direction="negative",
                reason_code="spread_and_slippage_drag",
                flags=("uncertainty_included",),
            ),
        ),
    )
    blocked = _row(
        market_slug="market-b",
        side="yes",
        total_score=Decimal("0.120000"),
        score_status="blocked",
        components=(
            _component(
                component_name="probability_edge",
                contribution=Decimal("0.150000"),
                direction="positive",
                reason_code="model_price_edge",
                flags=("paper_only",),
            ),
            _component(
                component_name="correlation_penalty",
                contribution=Decimal("-0.030000"),
                direction="negative",
                reason_code="portfolio_correlation_discount",
                flags=("correlation_included",),
            ),
        ),
    )

    report = _report(low, high, blocked)

    assert isinstance(report, PaperRecommendationScoreExplanationReport)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-recommendation-score-explanation-v0"
    assert report.row_count == 3
    assert report.pass_count == 1
    assert report.watch_count == 1
    assert report.blocked_count == 1
    assert report.average_total_score == Decimal("0.086667")
    assert report.top_total_score == Decimal("0.120000")
    assert tuple((row.market_slug, row.side) for row in report.rows) == (
        ("market-b", "yes"),
        ("market-c", "yes"),
        ("market-a", "no"),
    )
    assert report.flags == (
        "correlation_included",
        "cost_included",
        "depth_available",
        "edge_available",
        "paper_only",
        "readonly",
        "report_only",
        "uncertainty_included",
    )


def test_row_component_contributions_sum_to_quantized_total_score():
    row = _row(
        total_score=Decimal("0.123457"),
        components=(
            _component(
                component_name="probability_edge",
                contribution=Decimal("0.1000004"),
                direction="positive",
                reason_code="model_price_edge",
            ),
            _component(
                component_name="confidence",
                contribution=Decimal("0.0234564"),
                direction="positive",
                reason_code="confidence_supports_edge",
            ),
        ),
    )

    assert row.total_score == Decimal("0.123457")
    assert sum(
        (component.contribution for component in row.components),
        Decimal("0"),
    ).quantize(Decimal("0.000001")) == row.total_score


def test_builder_ignores_caller_decimal_context_when_computing_summary_values():
    rows = (
        _row(
            market_slug="market-a",
            total_score=Decimal("0.100000"),
            components=(
                _component(
                    component_name="probability_edge",
                    contribution=Decimal("0.100000"),
                    direction="positive",
                    reason_code="model_price_edge",
                ),
            ),
        ),
        _row(
            market_slug="market-b",
            total_score=Decimal("0.160000"),
            components=(
                _component(
                    component_name="probability_edge",
                    contribution=Decimal("0.160000"),
                    direction="positive",
                    reason_code="model_price_edge",
                ),
            ),
        ),
    )

    with localcontext(Context(prec=2)):
        report = _report(*rows)

    assert report.average_total_score == Decimal("0.130000")
    assert report.top_total_score == Decimal("0.160000")


def test_empty_report_is_readonly_paper_report_with_zero_counts():
    report = _report()

    assert report.row_count == 0
    assert report.pass_count == 0
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.average_total_score is None
    assert report.top_total_score is None
    assert report.rows == ()
    assert report.flags == ("paper_only", "readonly", "report_only")


def test_dataclasses_are_frozen_and_generated_at_is_canonicalized_to_utc():
    report = build_paper_recommendation_score_explanation_report(
        generated_at=datetime(2026, 6, 18, 12, 30, tzinfo=timezone.utc),
        config_version="paper-recommendation-score-explanation-v0",
        rows=(),
    )

    assert report.generated_at == datetime(2026, 6, 18, 12, 30, tzinfo=UTC)
    with pytest.raises(FrozenInstanceError):
        report.row_count = 1


@pytest.mark.parametrize("direction", ["buy", "up", "", "positive "])
def test_rejects_bad_component_direction(direction):
    with pytest.raises(ValueError, match="direction"):
        _component(direction=direction)


@pytest.mark.parametrize("score_status", ["approved", "reject", "", "pass "])
def test_rejects_bad_row_score_status(score_status):
    with pytest.raises(ValueError, match="score_status"):
        _row(score_status=score_status)


@pytest.mark.parametrize(
    "unsafe_flag",
    [
        "live_trading",
        "auth_required",
        "wallet_connected",
        "private_key_present",
        "sign_order",
        "submit_order",
        "cancel_order",
        "network_mutation",
        "exchange_write",
    ],
)
def test_rejects_unsafe_flags(unsafe_flag):
    with pytest.raises(ValueError, match="unsafe flag"):
        _component(flags=(unsafe_flag,))


def test_rejects_duplicate_component_names_per_row():
    with pytest.raises(ValueError, match="duplicate component_name"):
        _row(
            components=(
                _component(component_name="probability_edge"),
                _component(component_name="probability_edge"),
            ),
            total_score=Decimal("0.140000"),
        )


def test_rejects_inconsistent_total_score():
    with pytest.raises(ValueError, match="total_score"):
        _row(
            total_score=Decimal("0.010000"),
            components=(
                _component(
                    component_name="probability_edge",
                    contribution=Decimal("0.025000"),
                    direction="positive",
                    reason_code="model_price_edge",
                ),
            ),
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("contribution", "0.010000"),
        ("contribution", TaggedDecimal("0.010000")),
        ("total_score", "0.010000"),
        ("total_score", TaggedDecimal("0.010000")),
    ],
)
def test_rejects_non_plain_decimal_scores(field_name, value):
    if field_name == "contribution":
        with pytest.raises(ValueError, match="Decimal"):
            _component(contribution=value)
    else:
        with pytest.raises(ValueError, match="Decimal"):
            _row(
                total_score=value,
                components=(
                    _component(
                        component_name="probability_edge",
                        contribution=Decimal("0.010000"),
                        direction="positive",
                        reason_code="model_price_edge",
                    ),
                ),
            )


def test_rejects_non_plain_datetime_generated_at():
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_recommendation_score_explanation_report(
            generated_at=_DatetimeSubclass(2026, 6, 18, 16, 30, tzinfo=UTC),
            config_version="paper-recommendation-score-explanation-v0",
            rows=(),
        )


def test_rejects_report_rows_that_are_not_score_explanation_rows():
    with pytest.raises(ValueError, match="rows"):
        build_paper_recommendation_score_explanation_report(
            generated_at=GENERATED_AT,
            config_version="paper-recommendation-score-explanation-v0",
            rows=(object(),),
        )


def test_module_has_no_live_auth_order_or_network_imports():
    source = inspect.getsource(score_explanation)
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    forbidden_import_roots = {
        "aiohttp",
        "clob",
        "httpx",
        "polymarket",
        "py_clob_client",
        "requests",
        "socket",
        "urllib",
        "web3",
        "websocket",
    }
    assert imported_roots.isdisjoint(forbidden_import_roots)
