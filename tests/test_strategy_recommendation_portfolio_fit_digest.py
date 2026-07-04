from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.strategy_recommendation_portfolio_fit_digest import (
    StrategyRecommendationPortfolioFitDigestConfig,
    StrategyRecommendationPortfolioFitDigestInput,
    StrategyRecommendationPortfolioFitDigestReasonCodeCount,
    StrategyRecommendationPortfolioFitDigestReport,
    StrategyRecommendationPortfolioFitDigestRow,
    build_strategy_recommendation_portfolio_fit_digest_report,
    strategy_recommendation_portfolio_fit_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyRecommendationPortfolioFitDigestConfig:
    values: dict[str, object] = {
        "config_version": "strategy-recommendation-portfolio-fit-digest-v0",
        "category_watch_share": d("0.500000"),
        "category_block_share": d("0.700000"),
        "event_overlap_watch_share": d("0.400000"),
        "event_overlap_block_share": d("0.600000"),
        "cash_watch_remaining": d("100.000000"),
        "cash_block_remaining": d("0.000000"),
        "capacity_watch_ratio": d("1.500000"),
        "capacity_block_ratio": d("1.000000"),
        "tail_cluster_watch_share": d("0.300000"),
        "tail_cluster_block_share": d("0.500000"),
        "settlement_watch_share": d("0.300000"),
        "settlement_block_share": d("0.500000"),
    }
    values.update(overrides)
    return StrategyRecommendationPortfolioFitDigestConfig(**values)


def candidate(
    recommendation_id: str = "candidate-alpha",
    *,
    market_slug: str | None = None,
    category_id: str = "sports",
    event_id: str = "event-alpha",
    tail_cluster_id: str = "tail-alpha",
    candidate_notional: Decimal = d("100.000000"),
    available_cash: Decimal = d("1000.000000"),
    liquidity_capacity: Decimal = d("300.000000"),
    existing_category_notional: Decimal = d("100.000000"),
    existing_event_notional: Decimal = d("50.000000"),
    existing_tail_cluster_notional: Decimal = d("25.000000"),
    settlement_lockup_notional: Decimal = d("50.000000"),
    unresolved_settlement_notional: Decimal = d("100.000000"),
    portfolio_notional: Decimal = d("1000.000000"),
    expected_settlement_at: datetime = GENERATED_AT + timedelta(days=3),
    reason_codes: tuple[str, ...] = ("portfolio_fit_input_available",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyRecommendationPortfolioFitDigestInput:
    return StrategyRecommendationPortfolioFitDigestInput(
        recommendation_id=recommendation_id,
        market_slug=market_slug or recommendation_id,
        category_id=category_id,
        event_id=event_id,
        tail_cluster_id=tail_cluster_id,
        candidate_notional=candidate_notional,
        available_cash=available_cash,
        liquidity_capacity=liquidity_capacity,
        existing_category_notional=existing_category_notional,
        existing_event_notional=existing_event_notional,
        existing_tail_cluster_notional=existing_tail_cluster_notional,
        settlement_lockup_notional=settlement_lockup_notional,
        unresolved_settlement_notional=unresolved_settlement_notional,
        portfolio_notional=portfolio_notional,
        expected_settlement_at=expected_settlement_at,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: StrategyRecommendationPortfolioFitDigestInput,
    cfg: StrategyRecommendationPortfolioFitDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> StrategyRecommendationPortfolioFitDigestReport:
    return build_strategy_recommendation_portfolio_fit_digest_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_happy_path_scores_portfolio_fit_and_payload() -> None:
    digest = report(
        candidate(
            "candidate-alpha",
            category_id="crypto",
            candidate_notional=d("100.000000"),
            liquidity_capacity=d("300.000000"),
            existing_category_notional=d("100.000000"),
            existing_event_notional=d("50.000000"),
            existing_tail_cluster_notional=d("25.000000"),
            settlement_lockup_notional=d("50.000000"),
            unresolved_settlement_notional=d("100.000000"),
            portfolio_notional=d("1000.000000"),
            reason_codes=("portfolio_fit_input_available", "operator_screened"),
        ),
    )

    assert is_dataclass(digest)
    assert digest.generated_at == GENERATED_AT
    assert digest.generated_at.tzinfo is UTC
    assert digest.candidate_count == ONE
    assert digest.pass_count == ONE
    assert digest.watch_count == ZERO
    assert digest.blocked_count == ZERO
    assert digest.status == "pass"
    assert digest.reason_codes == ("portfolio_fit_digest_clear",)
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True

    row = digest.recommendation_rows[0]
    assert row.fit_status == "pass"
    assert row.category_exposure_after_candidate == d("200.000000")
    assert row.category_exposure_share == d("0.181818")
    assert row.event_overlap_after_candidate == d("150.000000")
    assert row.event_overlap_share == d("0.136364")
    assert row.cash_remaining_after_candidate == d("900.000000")
    assert row.capacity_ratio == d("3.000000")
    assert row.tail_cluster_after_candidate == d("125.000000")
    assert row.tail_cluster_share == d("0.113636")
    assert row.settlement_notional_after_candidate == d("150.000000")
    assert row.settlement_share == d("0.136364")
    assert row.expected_settlement_at == GENERATED_AT + timedelta(days=3)
    assert row.reason_codes == (
        "operator_screened",
        "portfolio_fit_clear",
        "portfolio_fit_input_available",
    )

    payload = strategy_recommendation_portfolio_fit_digest_payload(digest)
    assert payload["candidate_count"] == "1.000000"
    assert payload["recommendation_rows"][0]["capacity_ratio"] == "3.000000"
    assert payload["recommendation_rows"][0]["expected_settlement_at"] == (
        GENERATED_AT + timedelta(days=3)
    ).isoformat()
    json.dumps(payload, sort_keys=True)
    assert not _contains_float(payload)


def test_utc_normalization_for_generated_and_settlement_times() -> None:
    digest = report(
        candidate(
            expected_settlement_at=datetime(
                2026,
                7,
                7,
                9,
                30,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            2,
            8,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert digest.generated_at == GENERATED_AT
    assert digest.recommendation_rows[0].expected_settlement_at == datetime(
        2026,
        7,
        7,
        13,
        30,
        tzinfo=UTC,
    )


def test_rejects_naive_generated_and_settlement_times() -> None:
    with pytest.raises(ValueError, match="expected_settlement_at.*timezone-aware"):
        candidate(expected_settlement_at=datetime(2026, 7, 7, 13, 30))

    with pytest.raises(ValueError, match="generated_at.*timezone-aware"):
        report(candidate("aware-time"), generated_at=datetime(2026, 7, 2, 12, 0))


def test_fit_guards_emit_category_event_cash_capacity_tail_and_settlement_reasons() -> None:
    digest = report(
        candidate(
            "candidate-watch",
            category_id="macro",
            event_id="jobs-print",
            tail_cluster_id="rates-tail",
            candidate_notional=d("300.000000"),
            available_cash=d("400.000000"),
            liquidity_capacity=d("360.000000"),
            existing_category_notional=d("250.000000"),
            existing_event_notional=d("150.000000"),
            existing_tail_cluster_notional=d("50.000000"),
            settlement_lockup_notional=d("150.000000"),
            unresolved_settlement_notional=d("150.000000"),
            portfolio_notional=d("700.000000"),
        ),
        candidate(
            "candidate-blocked",
            category_id="crypto",
            event_id="btc-election",
            tail_cluster_id="crypto-tail",
            candidate_notional=d("800.000000"),
            available_cash=d("500.000000"),
            liquidity_capacity=d("600.000000"),
            existing_category_notional=d("500.000000"),
            existing_event_notional=d("300.000000"),
            existing_tail_cluster_notional=d("100.000000"),
            settlement_lockup_notional=d("500.000000"),
            unresolved_settlement_notional=d("500.000000"),
            portfolio_notional=d("1000.000000"),
        ),
    )

    assert digest.status == "blocked"
    assert digest.watch_count == ONE
    assert digest.blocked_count == ONE
    assert digest.reason_codes == (
        "portfolio_fit_digest_blocked",
        "portfolio_fit_capacity_ratio_blocked",
        "portfolio_fit_capacity_ratio_watch",
        "portfolio_fit_cash_blocked",
        "portfolio_fit_category_exposure_blocked",
        "portfolio_fit_category_exposure_watch",
        "portfolio_fit_event_overlap_blocked",
        "portfolio_fit_event_overlap_watch",
        "portfolio_fit_settlement_timing_blocked",
        "portfolio_fit_settlement_timing_watch",
        "portfolio_fit_tail_cluster_blocked",
        "portfolio_fit_tail_cluster_watch",
    )
    assert digest.recommendation_rows[0].recommendation_id == "candidate-blocked"
    assert digest.recommendation_rows[0].reason_codes == (
        "portfolio_fit_capacity_ratio_blocked",
        "portfolio_fit_cash_blocked",
        "portfolio_fit_category_exposure_blocked",
        "portfolio_fit_event_overlap_blocked",
        "portfolio_fit_input_available",
        "portfolio_fit_settlement_timing_blocked",
        "portfolio_fit_tail_cluster_blocked",
    )
    assert digest.recommendation_rows[1].recommendation_id == "candidate-watch"
    assert digest.recommendation_rows[1].reason_codes == (
        "portfolio_fit_capacity_ratio_watch",
        "portfolio_fit_category_exposure_watch",
        "portfolio_fit_event_overlap_watch",
        "portfolio_fit_input_available",
        "portfolio_fit_settlement_timing_watch",
        "portfolio_fit_tail_cluster_watch",
    )


def test_deterministic_sorting_and_reason_code_counts() -> None:
    digest = report(
        candidate(
            "zeta-watch",
            candidate_notional=d("300.000000"),
            liquidity_capacity=d("360.000000"),
            existing_category_notional=d("250.000000"),
            existing_event_notional=d("150.000000"),
            existing_tail_cluster_notional=d("50.000000"),
            settlement_lockup_notional=d("150.000000"),
            unresolved_settlement_notional=d("150.000000"),
            portfolio_notional=d("700.000000"),
            reason_codes=("portfolio_fit_input_available", "watch_seed"),
        ),
        candidate(
            "beta-blocked",
            candidate_notional=d("800.000000"),
            available_cash=d("500.000000"),
            liquidity_capacity=d("600.000000"),
            existing_category_notional=d("500.000000"),
            existing_event_notional=d("300.000000"),
            existing_tail_cluster_notional=d("100.000000"),
            settlement_lockup_notional=d("500.000000"),
            unresolved_settlement_notional=d("500.000000"),
            portfolio_notional=d("1000.000000"),
            reason_codes=("blocked_seed", "portfolio_fit_input_available"),
        ),
        candidate(
            "alpha-pass",
            candidate_notional=d("100.000000"),
            liquidity_capacity=d("300.000000"),
            reason_codes=("portfolio_fit_input_available", "pass_seed"),
        ),
        candidate(
            "alpha-blocked",
            candidate_notional=d("750.000000"),
            available_cash=d("500.000000"),
            liquidity_capacity=d("600.000000"),
            existing_category_notional=d("500.000000"),
            existing_event_notional=d("350.000000"),
            existing_tail_cluster_notional=d("150.000000"),
            settlement_lockup_notional=d("450.000000"),
            unresolved_settlement_notional=d("450.000000"),
            portfolio_notional=d("1000.000000"),
        ),
    )

    assert tuple(row.recommendation_id for row in digest.recommendation_rows) == (
        "beta-blocked",
        "alpha-blocked",
        "zeta-watch",
        "alpha-pass",
    )
    assert digest.reason_code_counts == (
        StrategyRecommendationPortfolioFitDigestReasonCodeCount(
            reason_code="portfolio_fit_input_available",
            count=d("4.000000"),
        ),
        StrategyRecommendationPortfolioFitDigestReasonCodeCount(
            reason_code="portfolio_fit_capacity_ratio_blocked",
            count=d("2.000000"),
        ),
        StrategyRecommendationPortfolioFitDigestReasonCodeCount(
            reason_code="portfolio_fit_cash_blocked",
            count=d("2.000000"),
        ),
        StrategyRecommendationPortfolioFitDigestReasonCodeCount(
            reason_code="portfolio_fit_category_exposure_blocked",
            count=d("2.000000"),
        ),
        StrategyRecommendationPortfolioFitDigestReasonCodeCount(
            reason_code="portfolio_fit_event_overlap_blocked",
            count=d("2.000000"),
        ),
        StrategyRecommendationPortfolioFitDigestReasonCodeCount(
            reason_code="portfolio_fit_settlement_timing_blocked",
            count=d("2.000000"),
        ),
        StrategyRecommendationPortfolioFitDigestReasonCodeCount(
            reason_code="portfolio_fit_tail_cluster_blocked",
            count=d("2.000000"),
        ),
        StrategyRecommendationPortfolioFitDigestReasonCodeCount(
            reason_code="blocked_seed",
            count=d("1.000000"),
        ),
        StrategyRecommendationPortfolioFitDigestReasonCodeCount(
            reason_code="pass_seed",
            count=d("1.000000"),
        ),
        StrategyRecommendationPortfolioFitDigestReasonCodeCount(
            reason_code="portfolio_fit_capacity_ratio_watch",
            count=d("1.000000"),
        ),
        StrategyRecommendationPortfolioFitDigestReasonCodeCount(
            reason_code="portfolio_fit_category_exposure_watch",
            count=d("1.000000"),
        ),
        StrategyRecommendationPortfolioFitDigestReasonCodeCount(
            reason_code="portfolio_fit_clear",
            count=d("1.000000"),
        ),
        StrategyRecommendationPortfolioFitDigestReasonCodeCount(
            reason_code="portfolio_fit_event_overlap_watch",
            count=d("1.000000"),
        ),
        StrategyRecommendationPortfolioFitDigestReasonCodeCount(
            reason_code="portfolio_fit_settlement_timing_watch",
            count=d("1.000000"),
        ),
        StrategyRecommendationPortfolioFitDigestReasonCodeCount(
            reason_code="portfolio_fit_tail_cluster_watch",
            count=d("1.000000"),
        ),
        StrategyRecommendationPortfolioFitDigestReasonCodeCount(
            reason_code="watch_seed",
            count=d("1.000000"),
        ),
        )


def test_row_sorting_uses_total_tie_breakers() -> None:
    first = report(
        candidate(
            "same-id",
            market_slug="z-market",
            category_id="z-category",
            event_id="z-event",
            tail_cluster_id="z-tail",
        ),
        candidate(
            "same-id",
            market_slug="a-market",
            category_id="a-category",
            event_id="a-event",
            tail_cluster_id="a-tail",
        ),
    )
    second = report(
        candidate(
            "same-id",
            market_slug="a-market",
            category_id="a-category",
            event_id="a-event",
            tail_cluster_id="a-tail",
        ),
        candidate(
            "same-id",
            market_slug="z-market",
            category_id="z-category",
            event_id="z-event",
            tail_cluster_id="z-tail",
        ),
    )

    assert tuple(row.market_slug for row in first.recommendation_rows) == (
        "a-market",
        "z-market",
    )
    assert tuple(row.market_slug for row in second.recommendation_rows) == (
        "a-market",
        "z-market",
    )


def test_empty_input_returns_report_only_zero_digest() -> None:
    digest = report()

    assert digest.candidate_count == ZERO
    assert digest.pass_count == ZERO
    assert digest.watch_count == ZERO
    assert digest.blocked_count == ZERO
    assert digest.max_category_exposure_share == ZERO
    assert digest.max_event_overlap_share == ZERO
    assert digest.min_cash_remaining_after_candidate == ZERO
    assert digest.min_capacity_ratio == ZERO
    assert digest.max_tail_cluster_share == ZERO
    assert digest.max_settlement_share == ZERO
    assert digest.status == "pass"
    assert digest.reason_codes == ("portfolio_fit_digest_empty",)
    assert digest.reason_code_counts == ()
    assert digest.recommendation_rows == ()


def test_hard_flags_validation_and_decimal_public_numbers() -> None:
    digest = report(candidate("frozen"))

    assert is_dataclass(StrategyRecommendationPortfolioFitDigestConfig)
    assert is_dataclass(StrategyRecommendationPortfolioFitDigestInput)
    assert is_dataclass(StrategyRecommendationPortfolioFitDigestRow)
    assert is_dataclass(StrategyRecommendationPortfolioFitDigestReasonCodeCount)
    assert is_dataclass(StrategyRecommendationPortfolioFitDigestReport)
    with pytest.raises(FrozenInstanceError):
        digest.status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest.recommendation_rows[0].capacity_ratio = d("9.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(digest, readonly=False)

    for item in (digest, *digest.recommendation_rows, *digest.reason_code_counts):
        for field_name, value in item.__dict__.items():
            if field_name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field_name
            assert type(value) is not float, field_name
    for field_name in (
        "candidate_count",
        "pass_count",
        "watch_count",
        "blocked_count",
        "max_category_exposure_share",
        "max_event_overlap_share",
        "min_cash_remaining_after_candidate",
        "min_capacity_ratio",
        "max_tail_cluster_share",
        "max_settlement_share",
    ):
        assert isinstance(getattr(digest, field_name), Decimal)


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("candidate_notional", 1),
        ("available_cash", _DecimalSubclass("1.000000")),
        ("expected_settlement_at", _DatetimeSubclass(2026, 7, 2, tzinfo=UTC)),
    ),
)
def test_rejects_non_exact_public_numeric_and_datetime_types(
    field_name: str,
    bad_value: object,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        candidate(**{field_name: bad_value})  # type: ignore[arg-type]


def test_rejects_unsafe_live_surface_fields_in_payload() -> None:
    with pytest.raises(ValueError, match="unsafe"):
        strategy_recommendation_portfolio_fit_digest_payload(
            {
                "wallet": "0xabc",
                "candidate_count": d("1.000000"),
            },
        )


def test_payload_rejects_direct_integer_numeric_values() -> None:
    with pytest.raises(ValueError, match="candidate_count"):
        strategy_recommendation_portfolio_fit_digest_payload(
            {
                "candidate_count": 1,
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_payload_rejects_false_phase1_flags() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        strategy_recommendation_portfolio_fit_digest_payload(
            {
                "candidate_count": d("1.000000"),
                "paper_only": False,
                "report_only": True,
                "readonly": True,
            },
        )


def test_payload_rejects_naive_datetime_values() -> None:
    with pytest.raises(ValueError, match="generated_at.*timezone-aware"):
        strategy_recommendation_portfolio_fit_digest_payload(
            {
                "generated_at": datetime(2026, 7, 2, 12, 0),
                "candidate_count": d("1.000000"),
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_module_does_not_expose_live_trading_or_io_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_recommendation_portfolio_fit_digest.py",
    ).read_text()
    forbidden = re_forbidden_live_surface()
    assert not forbidden.search(source)


def _contains_float(value: Any) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False


def re_forbidden_live_surface() -> Any:
    import re

    return re.compile(
        r"\b("
        r"requests|httpx|urllib|socket|sqlite3|psycopg|open\(|Path\([^)]*\)\.write|"
        r"wallet|broker|order|signing|private_key|auth_token|trade_advice"
        r")\b",
    )
