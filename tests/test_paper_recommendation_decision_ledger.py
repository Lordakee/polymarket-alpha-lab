from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_recommendation_decision_ledger import (
    PaperRecommendationDecisionLedgerReasonCodeCount,
    PaperRecommendationDecisionLedgerReport,
    PaperRecommendationDecisionLedgerRow,
    build_paper_recommendation_decision_ledger_report,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "paper_recommendation_decision_ledger.py"
)
GENERATED_AT = datetime(2026, 6, 19, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedLedgerShape:
    market_slug: str
    side: str
    decision: str
    primary_reason_code: str
    reason_codes: tuple[str, ...]
    expected_edge_per_share: Decimal
    max_cost_per_share: Decimal
    suggested_notional: Decimal
    flags: tuple[str, ...] = ("paper_only", "report_only", "readonly")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def ledger_row(
    market_slug: str = "market-alpha",
    *,
    side: str = "yes",
    decision: str = "recommend",
    primary_reason_code: str = "positive_expected_edge",
    reason_codes: tuple[str, ...] = ("positive_expected_edge",),
    expected_edge_per_share: Decimal = d("0.1000004"),
    max_cost_per_share: Decimal = d("0.0300004"),
    suggested_notional: Decimal = d("25.0000004"),
    flags: tuple[str, ...] = ("paper_only", "report_only", "readonly"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperRecommendationDecisionLedgerRow:
    return PaperRecommendationDecisionLedgerRow(
        market_slug=market_slug,
        side=side,
        decision=decision,
        primary_reason_code=primary_reason_code,
        reason_codes=reason_codes,
        expected_edge_per_share=expected_edge_per_share,
        max_cost_per_share=max_cost_per_share,
        suggested_notional=suggested_notional,
        flags=flags,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    config_version: str = "paper-recommendation-decision-ledger-v0",
) -> PaperRecommendationDecisionLedgerReport:
    return build_paper_recommendation_decision_ledger_report(
        generated_at=generated_at,
        config_version=config_version,
        rows=rows,
    )


def test_decision_ledger_summarizes_decisions_and_reason_counts_deterministically():
    summary = report(
        (
            ledger_row(
                "beta-watch",
                decision="watch",
                primary_reason_code="below_minimum_notional",
                reason_codes=("below_minimum_notional", "wide_spread"),
                expected_edge_per_share=d("0.0200004"),
                max_cost_per_share=d("0.0400004"),
                suggested_notional=d("0.0000004"),
            ),
            ledger_row(
                "alpha-recommend",
                primary_reason_code="positive_expected_edge",
                reason_codes=("positive_expected_edge", "wide_spread"),
                expected_edge_per_share=d("0.1000004"),
                max_cost_per_share=d("0.0200004"),
                suggested_notional=d("30.0000004"),
            ),
            ledger_row(
                "gamma-block",
                decision="block",
                primary_reason_code="negative_expected_edge",
                reason_codes=("negative_expected_edge",),
                expected_edge_per_share=d("-0.0500004"),
                max_cost_per_share=d("0.0100004"),
                suggested_notional=d("0.0000004"),
            ),
            SuppliedLedgerShape(
                market_slug="delta-recommend",
                side="no",
                decision="recommend",
                primary_reason_code="positive_expected_edge",
                reason_codes=("positive_expected_edge",),
                expected_edge_per_share=d("0.0300004"),
                max_cost_per_share=d("0.0300004"),
                suggested_notional=d("20.0000004"),
                flags=("paper_only", "report_only", "readonly"),
            ),
        ),
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == "paper-recommendation-decision-ledger-v0"
    assert summary.row_count == 4
    assert summary.recommend_count == 2
    assert summary.watch_count == 1
    assert summary.block_count == 1
    assert summary.total_suggested_notional == d("50.000000")
    assert summary.average_expected_edge_per_share == d("0.025000")
    assert summary.reason_code_counts == (
        PaperRecommendationDecisionLedgerReasonCodeCount(
            reason_code="positive_expected_edge",
            count=2,
        ),
        PaperRecommendationDecisionLedgerReasonCodeCount(
            reason_code="wide_spread",
            count=2,
        ),
        PaperRecommendationDecisionLedgerReasonCodeCount(
            reason_code="below_minimum_notional",
            count=1,
        ),
        PaperRecommendationDecisionLedgerReasonCodeCount(
            reason_code="negative_expected_edge",
            count=1,
        ),
    )
    assert summary.flags == ("paper_only", "report_only", "readonly")
    assert summary.rows == (
        ledger_row(
            "beta-watch",
            decision="watch",
            primary_reason_code="below_minimum_notional",
            reason_codes=("below_minimum_notional", "wide_spread"),
            expected_edge_per_share=d("0.0200004"),
            max_cost_per_share=d("0.0400004"),
            suggested_notional=d("0.0000004"),
        ),
        ledger_row(
            "alpha-recommend",
            primary_reason_code="positive_expected_edge",
            reason_codes=("positive_expected_edge", "wide_spread"),
            expected_edge_per_share=d("0.1000004"),
            max_cost_per_share=d("0.0200004"),
            suggested_notional=d("30.0000004"),
        ),
        ledger_row(
            "gamma-block",
            decision="block",
            primary_reason_code="negative_expected_edge",
            reason_codes=("negative_expected_edge",),
            expected_edge_per_share=d("-0.0500004"),
            max_cost_per_share=d("0.0100004"),
            suggested_notional=d("0.0000004"),
        ),
        ledger_row(
            "delta-recommend",
            side="no",
            primary_reason_code="positive_expected_edge",
            reason_codes=("positive_expected_edge",),
            expected_edge_per_share=d("0.0300004"),
            max_cost_per_share=d("0.0300004"),
            suggested_notional=d("20.0000004"),
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_decision_ledger_average_is_quantized_to_six_decimal_places():
    summary = report(
        (
            ledger_row("alpha", expected_edge_per_share=d("0.1000004")),
            ledger_row(
                "beta",
                decision="watch",
                expected_edge_per_share=d("0.0000004"),
                suggested_notional=d("0"),
            ),
            ledger_row(
                "gamma",
                decision="block",
                expected_edge_per_share=d("0.0000004"),
                suggested_notional=d("0"),
            ),
        ),
    )

    assert summary.average_expected_edge_per_share == d("0.033334")
    assert summary.average_expected_edge_per_share.as_tuple().exponent == -6


def test_decision_ledger_empty_report_uses_zero_summaries():
    summary = report(())

    assert summary.row_count == 0
    assert summary.recommend_count == 0
    assert summary.watch_count == 0
    assert summary.block_count == 0
    assert summary.total_suggested_notional == ZERO
    assert summary.average_expected_edge_per_share == ZERO
    assert summary.reason_code_counts == ()
    assert summary.rows == ()


def test_decision_ledger_rejects_invalid_decision_negative_notional_and_unsafe_flags():
    with pytest.raises(ValueError, match="decision"):
        ledger_row(decision="hold")
    with pytest.raises(ValueError, match="suggested_notional"):
        ledger_row(suggested_notional=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        report((ledger_row(paper_only=False),))
    with pytest.raises(ValueError, match="report_only"):
        report((ledger_row(report_only=False),))
    with pytest.raises(ValueError, match="readonly"):
        report((ledger_row(readonly=False),))
    with pytest.raises(ValueError, match="flags"):
        ledger_row(flags=("paper_only", "paper_only"))
    with pytest.raises(ValueError, match="flags"):
        ledger_row(flags=("paper_only", "live_trading"))
    with pytest.raises(ValueError, match="flags"):
        replace(report((ledger_row(),)), flags=("paper_only", "live_trading"))
    with pytest.raises(ValueError, match="primary_reason_code"):
        ledger_row(primary_reason_code="missing_from_tuple")
    with pytest.raises(ValueError, match="reason_codes"):
        ledger_row(reason_codes=("duplicate", "duplicate"))


def test_decision_ledger_normalizes_generated_at_to_utc_and_is_frozen():
    summary = report(
        (ledger_row(),),
        generated_at=datetime(2026, 6, 19, 8, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC

    with pytest.raises(FrozenInstanceError):
        summary.row_count = 2  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].decision = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="generated_at"):
        report((ledger_row(),), generated_at="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (ledger_row(),),
            generated_at=_DatetimeSubclass(2026, 6, 19, 15, 0, tzinfo=UTC),
        )


def test_decision_ledger_constructor_rejects_inconsistent_summaries():
    summary = report(
        (
            ledger_row("alpha"),
            ledger_row("beta", decision="watch", suggested_notional=d("0")),
        ),
    )

    with pytest.raises(ValueError, match="row_count"):
        replace(summary, row_count=3)
    with pytest.raises(ValueError, match="recommend_count"):
        replace(summary, recommend_count=2)
    with pytest.raises(ValueError, match="total_suggested_notional"):
        replace(summary, total_suggested_notional=d("999.000000"))
    with pytest.raises(ValueError, match="average_expected_edge_per_share"):
        replace(summary, average_expected_edge_per_share=d("0.999999"))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(summary, reason_code_counts=())


def test_decision_ledger_has_no_live_auth_order_or_network_imports():
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")

    allowed_imports = {
        "__future__",
        "collections",
        "collections.abc",
        "dataclasses",
        "datetime",
        "decimal",
    }
    forbidden_fragments = {
        "api",
        "auth",
        "client",
        "exchange",
        "http",
        "network",
        "order",
        "private_key",
        "request",
        "sign",
        "submit",
        "trade",
        "urllib",
        "wallet",
    }
    forbidden_call_names = {
        "cancel",
        "delete",
        "fetch",
        "get",
        "open",
        "post",
        "put",
        "read",
        "request",
        "send",
        "sign",
        "submit",
        "write",
    }

    for module in imported_modules:
        top_level = module.split(".", 1)[0]
        assert top_level in allowed_imports, module
        normalized = "".join(character for character in module.lower() if character.isalnum())
        for fragment in forbidden_fragments:
            assert fragment not in normalized, (module, fragment)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names, callee_name
