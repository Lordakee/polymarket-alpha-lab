from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab import strategy_human_review_queue_v6 as queue_module
from polymarket_alpha_lab.strategy_human_review_queue_v6 import (
    PaperStrategyHumanReviewQueueV6Config,
    PaperStrategyHumanReviewQueueV6Recommendation,
    PaperStrategyHumanReviewQueueV6Report,
    PaperStrategyHumanReviewQueueV6Row,
    build_paper_strategy_human_review_queue_v6,
    paper_strategy_human_review_queue_v6_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 30, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def recommendation(
    recommendation_id: str,
    *,
    action: str = "enter",
    audit_packet_complete: bool = True,
    risk_flags: tuple[str, ...] = (),
    source_conflict: bool = False,
    notional_size: Decimal = d("25.000000"),
    team_confidence: Decimal = d("0.820000"),
    reason_codes: tuple[str, ...] = ("source_recommendation_reason",),
) -> PaperStrategyHumanReviewQueueV6Recommendation:
    return PaperStrategyHumanReviewQueueV6Recommendation(
        recommendation_id=recommendation_id,
        candidate_id=f"candidate-{recommendation_id}",
        market_slug=f"market-{recommendation_id}",
        outcome_name="Yes",
        team_id="macro-rates",
        action=action,
        audit_packet_complete=audit_packet_complete,
        risk_flags=risk_flags,
        source_conflict=source_conflict,
        notional_size=notional_size,
        team_confidence=team_confidence,
        reason_codes=reason_codes,
    )


def build_report(
    rows: tuple[PaperStrategyHumanReviewQueueV6Recommendation, ...],
    *,
    config: PaperStrategyHumanReviewQueueV6Config | None = None,
) -> PaperStrategyHumanReviewQueueV6Report:
    return build_paper_strategy_human_review_queue_v6(
        rows,
        config=config
        or PaperStrategyHumanReviewQueueV6Config(
            config_version="human-review-queue-v6-test",
            large_notional_threshold=d("100.000000"),
            min_team_confidence=d("0.650000"),
        ),
        generated_at=GENERATED_AT,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            assert "auth" not in lowered
            assert "wallet" not in lowered
            assert "order" not in lowered
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_queue_ranks_human_review_items_by_action_packet_risk_conflict_size_confidence() -> None:
    report = build_report(
        (
            recommendation(
                "watch-risky",
                action="watch",
                audit_packet_complete=False,
                risk_flags=("stale_resolution_source",),
                source_conflict=True,
                notional_size=d("500.000000"),
                team_confidence=d("0.300000"),
            ),
            recommendation(
                "enter-large",
                action="enter",
                notional_size=d("250.000000"),
                team_confidence=d("0.900000"),
            ),
            recommendation(
                "enter-incomplete",
                action="enter",
                audit_packet_complete=False,
                notional_size=d("10.000000"),
                team_confidence=d("0.950000"),
            ),
            recommendation(
                "enter-risk-conflict",
                action="enter",
                risk_flags=("portfolio_concentration", "thin_exit_depth"),
                source_conflict=True,
                notional_size=d("75.000000"),
                team_confidence=d("0.400000"),
            ),
        ),
    )

    assert isinstance(report, PaperStrategyHumanReviewQueueV6Report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "human-review-queue-v6-test"
    assert report.input_count == 4
    assert report.queue_count == 4
    assert report.incomplete_audit_packet_count == 2
    assert report.risk_flagged_count == 2
    assert report.source_conflict_count == 2
    assert report.large_notional_count == 2
    assert report.low_confidence_count == 2
    assert report.top_recommendation_id == "enter-incomplete"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.recommendation_id for row in report.rows) == (
        "enter-incomplete",
        "enter-risk-conflict",
        "enter-large",
        "watch-risky",
    )
    assert tuple(row.review_rank for row in report.rows) == (1, 2, 3, 4)
    assert tuple(row.review_status for row in report.rows) == (
        "incomplete_audit_packet",
        "risk_review",
        "large_notional_review",
        "incomplete_audit_packet",
    )
    assert report.rows[0].reason_codes == (
        "action_enter",
        "audit_packet_incomplete",
        "human_review_required",
        "source_recommendation_reason",
    )
    assert report.rows[1].reason_codes == (
        "action_enter",
        "audit_packet_complete",
        "human_review_required",
        "low_team_confidence",
        "risk_flags_present",
        "source_conflict_present",
        "source_recommendation_reason",
    )


def test_queue_uses_deterministic_tie_breakers_and_preserves_skip_actions() -> None:
    report = build_report(
        (
            recommendation("beta", action="skip", notional_size=d("40.000000")),
            recommendation("gamma", action="enter", notional_size=d("50.000000")),
            recommendation("alpha", action="enter", notional_size=d("50.000000")),
        ),
    )

    assert tuple(row.recommendation_id for row in report.rows) == (
        "alpha",
        "gamma",
        "beta",
    )
    assert report.rows[0].review_status == "review_ready"
    assert report.rows[2].reason_codes == (
        "action_skip",
        "audit_packet_complete",
        "human_review_required",
        "source_recommendation_reason",
    )


def test_payload_is_readonly_paper_report_only_and_stringifies_decimals() -> None:
    report = build_report(
        (
            recommendation(
                "enter-low-confidence",
                action="enter",
                notional_size=d("101.123456"),
                team_confidence=d("0.640000"),
            ),
        ),
    )

    payload = paper_strategy_human_review_queue_v6_payload(report)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["notional_size"] == "101.123456"
    assert payload["rows"][0]["team_confidence"] == "0.640000"
    assert payload["rows"][0]["review_status"] == "large_notional_review"
    assert_no_float_values(payload)


def test_dataclasses_are_frozen_and_reject_float_numeric_inputs() -> None:
    row = build_report((recommendation("frozen"),)).rows[0]

    with pytest.raises(FrozenInstanceError):
        row.review_rank = 99  # type: ignore[misc]

    with pytest.raises(ValueError, match="notional_size must be a Decimal"):
        recommendation("float-notional", notional_size=12.5)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="team_confidence must be a Decimal"):
        recommendation("float-confidence", team_confidence=0.7)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="team_confidence must be between zero and one"):
        recommendation("bad-confidence", team_confidence=d("1.100000"))

    with pytest.raises(ValueError, match="paper_only must be True"):
        PaperStrategyHumanReviewQueueV6Recommendation(
            recommendation_id="live-surface",
            candidate_id="candidate-live",
            market_slug="market-live",
            outcome_name="Yes",
            team_id="macro-rates",
            action="enter",
            audit_packet_complete=True,
            risk_flags=(),
            source_conflict=False,
            notional_size=d("1.000000"),
            team_confidence=d("0.900000"),
            reason_codes=("source_recommendation_reason",),
            paper_only=False,
        )


def test_module_stays_pure_readonly_and_exports_only_review_queue_surface() -> None:
    source = inspect.getsource(queue_module)
    tree = ast.parse(source)

    imported_modules: list[str] = []
    public_exports: tuple[str, ...] | None = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    public_exports = ast.literal_eval(node.value)

    assert public_exports == (
        "PaperStrategyHumanReviewQueueV6Config",
        "PaperStrategyHumanReviewQueueV6Recommendation",
        "PaperStrategyHumanReviewQueueV6Report",
        "PaperStrategyHumanReviewQueueV6Row",
        "build_paper_strategy_human_review_queue_v6",
        "paper_strategy_human_review_queue_v6_payload",
    )
    assert set(imported_modules) <= {
        "__future__",
        "collections.abc",
        "dataclasses",
        "datetime",
        "decimal",
        "typing",
        "polymarket_alpha_lab.team_paper_guard",
    }
    lowered_source = source.lower()
    for forbidden_fragment in (
        "requests",
        "httpx",
        "aiohttp",
        "sqlite3",
        "psycopg",
        "socket",
        "websocket",
        "py_clob_client",
        "place_order",
        "submit_order",
        "create_order",
        "cancel_order",
    ):
        assert forbidden_fragment not in lowered_source

    assert PaperStrategyHumanReviewQueueV6Row.__dataclass_params__.frozen is True
