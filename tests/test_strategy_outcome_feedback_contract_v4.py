from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_outcome_feedback_contract_v4",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def feedback(
    recommendation_id: str = "rec-alpha",
    team_id: str = "politics",
    category_id: str = "politics",
    *,
    settled_at: datetime | None = None,
    outcome: str = "win",
    payout: str = "1.000000",
    forecast_probability: str = "0.620000",
    cost_adjusted_edge: str = "0.080000",
    source_failure_tags: tuple[str, ...] = (),
    resolution_notes: str = "Official resolution matched the paper recommendation thesis.",
):
    module = api()
    return module.StrategyOutcomeFeedbackContractV4Input(
        recommendation_id=recommendation_id,
        team_id=team_id,
        category_id=category_id,
        settled_at=settled_at or GENERATED_AT - timedelta(hours=2),
        outcome=outcome,
        payout=d(payout),
        forecast_probability=d(forecast_probability),
        cost_adjusted_edge=d(cost_adjusted_edge),
        source_failure_tags=source_failure_tags,
        resolution_notes=resolution_notes,
    )


def report(*rows, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_outcome_feedback_contract_v4_report(
        rows,
        generated_at=generated_at,
    )


def test_report_flags_feedback_ready_rows_and_contract_gaps() -> None:
    validation_report = report(
        feedback(
            "rec-ready-win",
            outcome="win",
            payout="1.000000",
            forecast_probability="0.620000",
            cost_adjusted_edge="0.080000",
            source_failure_tags=(),
            resolution_notes=(
                "Official resolution confirmed the paper recommendation outcome."
            ),
        ),
        feedback(
            "rec-loss-needs-memory",
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            outcome="loss",
            payout="0.000000",
            forecast_probability="0.710000",
            cost_adjusted_edge="0.140000",
            source_failure_tags=(),
            resolution_notes="",
        ),
        feedback(
            "rec-loss-documented",
            team_id="macro_rates",
            category_id="finance.macro.rates",
            outcome="loss",
            payout="0.000000",
            forecast_probability="0.550000",
            cost_adjusted_edge="-0.030000",
            source_failure_tags=("stale_source", "resolution_rule_miss"),
            resolution_notes=(
                "Resolution exposed stale source coverage and a missed rule nuance."
            ),
        ),
    )

    assert is_dataclass(validation_report)
    assert validation_report.generated_at == GENERATED_AT
    assert validation_report.generated_at.tzinfo is UTC
    assert validation_report.source_row_count == d("3")
    assert validation_report.feedback_ready_count == d("2")
    assert validation_report.blocked_count == d("1")
    assert validation_report.total_payout == d("1.000000")
    assert validation_report.average_forecast_probability == d("0.626667")
    assert validation_report.average_cost_adjusted_edge == d("0.063333")
    assert validation_report.source_failure_tagged_count == d("1")
    assert validation_report.missing_resolution_notes_count == d("1")
    assert validation_report.status == "blocked"
    assert validation_report.reason_codes == (
        "missing_source_failure_tags",
        "missing_resolution_notes",
    )
    assert validation_report.paper_only is True
    assert validation_report.report_only is True
    assert validation_report.readonly is True

    assert tuple(row.recommendation_id for row in validation_report.rows) == (
        "rec-loss-needs-memory",
        "rec-loss-documented",
        "rec-ready-win",
    )
    blocked = validation_report.rows[0]
    assert blocked.validation_status == "blocked"
    assert blocked.reason_codes == (
        "missing_source_failure_tags",
        "missing_resolution_notes",
    )

    documented = validation_report.rows[1]
    assert documented.validation_status == "pass"
    assert documented.source_failure_tags == (
        "stale_source",
        "resolution_rule_miss",
    )
    assert documented.reason_codes == ("feedback_contract_ready",)


def test_empty_report_is_readonly_paper_report_with_decimal_zeroes() -> None:
    validation_report = report()

    assert validation_report.source_row_count == d("0")
    assert validation_report.feedback_ready_count == d("0")
    assert validation_report.blocked_count == d("0")
    assert validation_report.total_payout == d("0.000000")
    assert validation_report.average_forecast_probability == d("0.000000")
    assert validation_report.average_cost_adjusted_edge == d("0.000000")
    assert validation_report.source_failure_tagged_count == d("0")
    assert validation_report.missing_resolution_notes_count == d("0")
    assert validation_report.status == "pass"
    assert validation_report.reason_codes == ("feedback_contract_ready",)
    assert validation_report.rows == ()
    assert validation_report.paper_only is True
    assert validation_report.report_only is True
    assert validation_report.readonly is True


def test_total_payout_accumulates_across_multiple_settled_wins() -> None:
    validation_report = report(
        feedback("rec-win-a"),
        feedback(
            "rec-win-b",
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
        ),
    )

    assert validation_report.source_row_count == d("2")
    assert validation_report.total_payout == d("2.000000")
    assert validation_report.average_forecast_probability == d("0.620000")
    assert validation_report.status == "pass"


def test_validates_decimal_only_datetime_flags_and_immutability() -> None:
    module = api()

    with pytest.raises(ValueError, match="payout must be a Decimal"):
        module.StrategyOutcomeFeedbackContractV4Input(
            recommendation_id="rec-alpha",
            team_id="politics",
            category_id="politics",
            settled_at=GENERATED_AT,
            outcome="win",
            payout=1,
            forecast_probability=d("0.620000"),
            cost_adjusted_edge=d("0.080000"),
            source_failure_tags=(),
            resolution_notes="Official resolution matched the paper recommendation.",
        )

    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        feedback(forecast_probability="0.620000").__class__(
            recommendation_id="rec-beta",
            team_id="politics",
            category_id="politics",
            settled_at=GENERATED_AT,
            outcome="win",
            payout=d("1.000000"),
            forecast_probability=0.62,
            cost_adjusted_edge=d("0.080000"),
            source_failure_tags=(),
            resolution_notes="Official resolution matched the paper recommendation.",
        )

    with pytest.raises(ValueError, match="cost_adjusted_edge must be a Decimal"):
        module.StrategyOutcomeFeedbackContractV4Input(
            recommendation_id="rec-gamma",
            team_id="politics",
            category_id="politics",
            settled_at=GENERATED_AT,
            outcome="win",
            payout=d("1.000000"),
            forecast_probability=d("0.620000"),
            cost_adjusted_edge=0.08,
            source_failure_tags=(),
            resolution_notes="Official resolution matched the paper recommendation.",
        )

    with pytest.raises(ValueError, match="settled_at must be timezone-aware"):
        feedback(settled_at=datetime(2026, 7, 6, 10, 0))

    row = feedback()
    with pytest.raises(FrozenInstanceError):
        row.payout = d("0.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)


def test_validates_contract_fields_duplicates_and_generated_at() -> None:
    with pytest.raises(ValueError, match="category_id must match team_id"):
        feedback(team_id="crypto_btc", category_id="politics")

    with pytest.raises(ValueError, match="source_failure_tags must be unique"):
        feedback(
            outcome="loss",
            payout="0.000000",
            source_failure_tags=("stale_source", "stale_source"),
        )

    unsupported = report(
        feedback(
            outcome="cancelled",
            payout="0.000000",
            source_failure_tags=("resolution_rule_miss",),
            resolution_notes="Settlement state did not map to a supported outcome.",
        ),
    )
    assert unsupported.status == "blocked"
    assert unsupported.rows[0].reason_codes == ("unsupported_outcome",)

    payout_mismatch = report(feedback(outcome="win", payout="0.000000"))
    assert payout_mismatch.status == "blocked"
    assert payout_mismatch.rows[0].reason_codes == ("outcome_payout_mismatch",)

    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        report(
            feedback("rec-alpha"),
            feedback("rec-alpha", team_id="macro_rates", category_id="finance.macro.rates"),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(feedback(), generated_at=datetime(2026, 7, 6, 12, 0))


def test_payload_is_json_ready_readonly_and_has_no_live_surface() -> None:
    payload = api().strategy_outcome_feedback_contract_v4_payload(
        report(
            feedback(
                "rec-loss-documented",
                outcome="loss",
                payout="0.000000",
                forecast_probability="0.710000",
                cost_adjusted_edge="0.140000",
                source_failure_tags=("stale_source",),
                resolution_notes="Team memory should lower stale source trust.",
            ),
        ),
    )

    payload_text = repr(payload).lower()
    for forbidden in (
        "auth",
        "wallet",
        "order",
        "account",
        "broker",
        "investment",
        "database",
    ):
        assert forbidden not in payload_text
    assert payload["source_row_count"] == "1"
    assert payload["total_payout"] == "0.000000"
    assert payload["average_forecast_probability"] == "0.710000"
    assert payload["average_cost_adjusted_edge"] == "0.140000"
    assert payload["rows"][0]["recommendation_id"] == "rec-loss-documented"
    assert payload["rows"][0]["source_failure_tags"] == ["stale_source"]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_module_scope_has_no_persistence_network_db_or_ordering_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_outcome_feedback_contract_v4.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live_trading",
        "auth",
        "wallet",
        "account",
        "broker",
        "investment",
        "database",
        "payload_json",
        "open(",
        "requests",
        "http",
        "submit_order",
        "place_order",
        "persist",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
