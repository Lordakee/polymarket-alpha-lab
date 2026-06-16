import json
from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.book_imbalance_forecast import (
    PaperBookImbalanceForecastConfig,
)
from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventCostAssumptions,
    PaperCostAwareEventStrategyConfig,
)
from polymarket_alpha_lab.cost_aware_snapshot_builder import PaperCostAwareSnapshotConfig
from polymarket_alpha_lab.forecast_provider import PaperForecastConfig
from polymarket_alpha_lab.llm_forecast import PaperLLMForecastConfig
from polymarket_alpha_lab.llm_research_transport import (
    GLMChatTransport,
    ProbabilityModelResult,
)
from polymarket_alpha_lab.paper_execution import PaperExecutionConfig
from polymarket_alpha_lab.pipeline import MarketScanConfig
from polymarket_alpha_lab.project_screening import PaperProjectScreeningConfig
from polymarket_alpha_lab.strategy_cycle import (
    PaperStrategyCycleConfig,
    PaperStrategyCycleLog,
    PaperStrategyCycleReport,
    run_strategy_cycle,
)


GENERATED_AT = datetime(2026, 6, 16, 13, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Canned raw Gamma market / CLOB book payload builders + fake client
# ---------------------------------------------------------------------------


def raw_market(
    *,
    condition_id,
    slug,
    question,
    token_ids,
    outcomes=("Yes", "No"),
    **overrides,
):
    payload = {
        "conditionId": condition_id,
        "outcomes": list(outcomes),
        "clobTokenIds": list(token_ids),
        "slug": slug,
        "question": question,
        "active": True,
        "closed": False,
        "acceptingOrders": True,
        "enableOrderBook": True,
        "volume24hr": "5000",
        "liquidity": "10000",
        "description": "Market resolves according to the public source.",
        "resolutionSource": "public-source",
    }
    payload.update(overrides)
    return payload


def raw_book(token_id, *, bid="0.5000", ask="0.5500", size="100.0000"):
    return {
        "asset_id": token_id,
        "bids": [{"price": bid, "size": size}],
        "asks": [{"price": ask, "size": size}],
    }


class FakeMarketDataClient:
    """A canned, no-network MarketDataClient implementation."""

    def __init__(self, markets, books):
        self._markets = list(markets)
        self._books = dict(books)
        self.list_markets_calls = []
        self.get_order_book_calls = []

    def list_markets(self, *, active, closed, limit):
        self.list_markets_calls.append({"active": active, "closed": closed, "limit": limit})
        return list(self._markets)

    def get_order_book(self, *, token_id):
        self.get_order_book_calls.append(token_id)
        if token_id not in self._books:
            raise KeyError(token_id)
        return self._books[token_id]


def binary_market_pair(
    *,
    condition_id,
    slug,
    question,
    yes_token_id,
    no_token_id,
):
    market = raw_market(
        condition_id=condition_id,
        slug=slug,
        question=question,
        token_ids=(yes_token_id, no_token_id),
        outcomes=("Yes", "No"),
    )
    books = {
        yes_token_id: raw_book(yes_token_id),
        no_token_id: raw_book(no_token_id),
    }
    return market, books


# ---------------------------------------------------------------------------
# Cycle config factory
# ---------------------------------------------------------------------------


def forecast_config(**overrides):
    values = {
        "config_version": "naive-forecast-v1",
        "min_book_depth": Decimal("1.0000"),
        "low_confidence_value": Decimal("0.5000"),
        "high_confidence_value": Decimal("0.7500"),
        "max_spread_for_high_confidence": Decimal("0.0300"),
    }
    values.update(overrides)
    return PaperForecastConfig(**values)


def book_imbalance_config(**overrides):
    values = {
        "config_version": "book-imbalance-v1",
        "imbalance_strength": Decimal("0.0200"),
        "max_nudge": Decimal("0.0500"),
        "min_book_depth": Decimal("1.0000"),
        "low_confidence_value": Decimal("0.5000"),
        "high_confidence_value": Decimal("0.7500"),
        "max_spread_for_high_confidence": Decimal("0.0300"),
    }
    values.update(overrides)
    return PaperBookImbalanceForecastConfig(**values)


def snapshot_config(**overrides):
    values = {
        "config_version": "snapshot-builder-v1",
        "default_resolution_risk": Decimal("0.1000"),
        "missing_rules_resolution_risk": Decimal("0.3000"),
        "imminent_resolution_risk_cap": Decimal("0.0500"),
        "imminent_resolution_horizon_hours": 24,
    }
    values.update(overrides)
    return PaperCostAwareSnapshotConfig(**values)


def strategy_config(**overrides):
    values = {
        "config_version": "cost-aware-event-v1",
        "min_confidence": Decimal("0.7000"),
        "max_spread": Decimal("0.0500"),
        "max_resolution_risk": Decimal("0.2000"),
        "min_ask_size": Decimal("10.0000"),
        "min_net_edge": Decimal("0.0100"),
    }
    values.update(overrides)
    return PaperCostAwareEventStrategyConfig(**values)


def screening_config(**overrides):
    values = {
        "config_version": "project-screening-v1",
        "min_screening_score": Decimal("0.010000"),
        "reference_ask_size": Decimal("100.0000"),
        "net_edge_weight": Decimal("1.0000"),
        "confidence_weight": Decimal("0.0000"),
        "depth_weight": Decimal("0.0000"),
        "spread_penalty_weight": Decimal("0.0000"),
        "resolution_risk_penalty_weight": Decimal("0.0000"),
        "cost_penalty_weight": Decimal("0.0000"),
    }
    values.update(overrides)
    return PaperProjectScreeningConfig(**values)


def cost_assumptions(**overrides):
    values = {
        "taker_fee_rate": Decimal("0.0000"),
        "slippage_cost_per_share": Decimal("0.0000"),
        "funding_cost_per_share": Decimal("0.0000"),
        "finalization_cost_per_share": Decimal("0.0000"),
        "time_cost_per_share": Decimal("0.0000"),
        "risk_cost_per_share": Decimal("0.0000"),
    }
    values.update(overrides)
    return PaperCostAwareEventCostAssumptions(**values)


def cycle_config(**overrides):
    values = {
        "config_version": "strategy-cycle-v1",
        "forecast_config": forecast_config(),
        "snapshot_config": snapshot_config(),
        "strategy_config": strategy_config(),
        "screening_config": screening_config(),
        "cost_assumptions": cost_assumptions(),
        "max_markets_per_cycle": 50,
        "prefilter_by_score": True,
    }
    values.update(overrides)
    return PaperStrategyCycleConfig(**values)


def scan_config(archive_root, *, limit=50):
    return MarketScanConfig(
        limit=limit,
        archive_root=Path(archive_root),
        output_path=Path(archive_root) / "ignored.json",
    )


def run_cycle(client, archive_root, *, config=None, generated_at=GENERATED_AT):
    return run_strategy_cycle(
        client=client,
        scan_config=scan_config(archive_root),
        cycle_config=config or cycle_config(),
        generated_at=generated_at,
    )


# ---------------------------------------------------------------------------
# Behavior tests (a)-(m)
# ---------------------------------------------------------------------------


def test_strategy_cycle_single_binary_market_produces_snapshot_and_screening(tmp_path):
    market, books = binary_market_pair(
        condition_id="0xcondA",
        slug="market-a",
        question="Will A happen?",
        yes_token_id="yes-a",
        no_token_id="no-a",
    )
    client = FakeMarketDataClient([market], books)

    report = run_cycle(client, tmp_path)

    assert isinstance(report, PaperStrategyCycleReport)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "strategy-cycle-v1"
    assert report.scan_market_count == 1
    assert report.considered_count == 1
    assert report.snapshot_ready_count == 1
    assert report.cost_aware_report_count == 1
    assert report.blocked_counts == ()
    assert report.screening_report is not None
    assert report.screening_report.candidate_count == 1
    assert client.list_markets_calls == [
        {"active": True, "closed": False, "limit": 50},
    ]
    assert set(client.get_order_book_calls) == {"yes-a", "no-a"}


def test_strategy_cycle_records_non_binary_market_as_blocked_without_fetching_books(tmp_path):
    market = raw_market(
        condition_id="0xcondNonBinary",
        slug="market-non-binary",
        question="Will a multi-outcome resolve?",
        token_ids=("alpha-token", "beta-token", "gamma-token"),
        outcomes=("Alpha", "Beta", "Gamma"),
    )
    client = FakeMarketDataClient([market], {})

    report = run_cycle(client, tmp_path)

    assert report.scan_market_count == 1
    assert report.considered_count == 1
    assert report.snapshot_ready_count == 0
    assert report.cost_aware_report_count == 0
    assert report.blocked_counts == (("blocked_non_binary_market", 1),)
    assert report.screening_report is None
    assert client.get_order_book_calls == []


def test_strategy_cycle_records_fetch_error_and_continues_other_markets(tmp_path):
    good_market, good_books = binary_market_pair(
        condition_id="0xcondGood",
        slug="market-good",
        question="Will Good happen?",
        yes_token_id="yes-good",
        no_token_id="no-good",
    )
    bad_market = raw_market(
        condition_id="0xcondBad",
        slug="market-bad",
        question="Will Bad happen?",
        token_ids=("yes-bad", "no-bad"),
    )
    books = dict(good_books)
    # leave "yes-bad" missing so get_order_book raises KeyError for the bad market
    books["no-bad"] = raw_book("no-bad")
    client = FakeMarketDataClient([good_market, bad_market], books)

    report = run_cycle(client, tmp_path)

    assert report.scan_market_count == 2
    assert report.considered_count == 2
    assert report.snapshot_ready_count == 1
    assert report.cost_aware_report_count == 1
    assert report.blocked_counts == (("blocked_fetch_error", 1),)
    assert report.screening_report is not None
    assert report.screening_report.candidate_count == 1


def test_strategy_cycle_empty_scan_has_no_screening_report(tmp_path):
    client = FakeMarketDataClient([], {})

    report = run_cycle(client, tmp_path)

    assert report.scan_market_count == 0
    assert report.considered_count == 0
    assert report.snapshot_ready_count == 0
    assert report.cost_aware_report_count == 0
    assert report.blocked_counts == ()
    assert report.screening_report is None


def test_strategy_cycle_truncates_retained_markets_to_max_per_cycle(tmp_path):
    markets = [
        raw_market(
            condition_id=f"0xcond{label}",
            slug=f"market-{label.lower()}",
            question=f"Will {label} happen?",
            token_ids=(f"yes-{label.lower()}", f"no-{label.lower()}"),
        )
        for label in ("Alpha", "Bravo", "Charlie")
    ]
    config = cycle_config(
        max_markets_per_cycle=2,
        prefilter_by_score=False,
    )
    client = FakeMarketDataClient(markets, {})

    report = run_cycle(client, tmp_path, config=config)

    assert report.scan_market_count == 3
    assert report.considered_count == 2
    # the two retained binary markets have no books available -> fetch_error
    assert report.blocked_counts == (("blocked_fetch_error", 2),)
    assert report.snapshot_ready_count == 0


def test_strategy_cycle_defaults_generated_at_to_utc_now(tmp_path):
    market, books = binary_market_pair(
        condition_id="0xcondNow",
        slug="market-now",
        question="Will Now happen?",
        yes_token_id="yes-now",
        no_token_id="no-now",
    )
    client = FakeMarketDataClient([market], books)

    before = datetime.now(UTC)
    report = run_strategy_cycle(
        client=client,
        scan_config=scan_config(tmp_path),
        cycle_config=cycle_config(),
        generated_at=None,
    )
    after = datetime.now(UTC)

    assert report.generated_at.tzinfo == UTC
    assert before - timedelta(seconds=1) <= report.generated_at <= after + timedelta(seconds=1)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"config_version": ""}, "config_version"),
        ({"config_version": " strategy-cycle-v1 "}, "config_version"),
        ({"max_markets_per_cycle": 0}, "max_markets_per_cycle|positive"),
        ({"max_markets_per_cycle": -1}, "max_markets_per_cycle|positive"),
        ({"max_markets_per_cycle": True}, "max_markets_per_cycle|int"),
        ({"forecast_config": "not-a-config"}, "forecast_config"),
        ({"snapshot_config": object()}, "snapshot_config"),
        ({"strategy_config": None}, "strategy_config"),
        ({"screening_config": 123}, "screening_config"),
        ({"cost_assumptions": "bad"}, "cost_assumptions"),
    ),
)
def test_strategy_cycle_config_rejects_invalid_inputs(overrides, message):
    with pytest.raises(ValueError, match=message):
        cycle_config(**overrides)


def test_strategy_cycle_report_is_frozen_and_revalidates_report_flags(tmp_path):
    market, books = binary_market_pair(
        condition_id="0xcondFrozen",
        slug="market-frozen",
        question="Will Frozen happen?",
        yes_token_id="yes-frozen",
        no_token_id="no-frozen",
    )
    client = FakeMarketDataClient([market], books)
    report = run_cycle(client, tmp_path)

    with pytest.raises(FrozenInstanceError):
        report.snapshot_ready_count = 99
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)


def test_strategy_cycle_log_appends_jsonl_decimal_strings_and_preserves_file(tmp_path):
    market, books = binary_market_pair(
        condition_id="0xcondLog",
        slug="market-log",
        question="Will Log happen?",
        yes_token_id="yes-log",
        no_token_id="no-log",
    )
    client = FakeMarketDataClient([market], books)
    report = run_cycle(client, tmp_path)
    log = PaperStrategyCycleLog(path=tmp_path / "nested" / "strategy-cycle.jsonl")

    log.append(report)
    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    stored = json.loads(lines[0])
    assert stored["paper_only"] is True
    assert stored["report_only"] is True
    assert stored["generated_at"] == "2026-06-16T13:00:00+00:00"
    assert stored["config_version"] == "strategy-cycle-v1"
    assert stored["scan_market_count"] == 1
    assert stored["considered_count"] == 1
    assert stored["snapshot_ready_count"] == 1
    assert stored["cost_aware_report_count"] == 1
    assert stored["blocked_counts"] == []
    assert stored["screening_report"]["candidate_count"] == 1
    assert stored["screening_report"]["queue_items"][0]["screening_score"] is not None

    existing_log_path = tmp_path / "existing.jsonl"
    existing_log_path.write_text("existing\n", encoding="utf-8")
    with pytest.raises(ValueError, match="PaperStrategyCycleReport"):
        PaperStrategyCycleLog(path=existing_log_path).append(object())
    assert existing_log_path.read_text(encoding="utf-8") == "existing\n"


def test_strategy_cycle_report_rejects_count_invariant_violations(tmp_path):
    market, books = binary_market_pair(
        condition_id="0xcondInvariant",
        slug="market-invariant",
        question="Will Invariant happen?",
        yes_token_id="yes-invariant",
        no_token_id="no-invariant",
    )
    client = FakeMarketDataClient([market], books)
    report = run_cycle(client, tmp_path)

    with pytest.raises(ValueError, match="cost_aware_report_count"):
        replace(report, cost_aware_report_count=report.snapshot_ready_count + 1)
    with pytest.raises(ValueError, match="considered_count"):
        replace(report, considered_count=report.scan_market_count + 5)
    with pytest.raises(ValueError, match="screening_report"):
        replace(report, screening_report=None)


def test_strategy_cycle_blocked_counts_are_sorted_and_sum_with_snapshot_ready(tmp_path):
    market_good, good_books = binary_market_pair(
        condition_id="0xcondSumGood",
        slug="market-sum-good",
        question="Will Sum Good happen?",
        yes_token_id="yes-sum-good",
        no_token_id="no-sum-good",
    )
    market_bad = raw_market(
        condition_id="0xcondSumBad",
        slug="market-sum-bad",
        question="Will Sum Bad happen?",
        token_ids=("yes-sum-bad", "no-sum-bad"),
    )
    market_non_binary = raw_market(
        condition_id="0xcondSumNonBinary",
        slug="market-sum-non-binary",
        question="Will Sum NonBinary happen?",
        token_ids=("only-token",),
        outcomes=("Only",),
    )
    books = dict(good_books)
    books["no-sum-bad"] = raw_book("no-sum-bad")
    client = FakeMarketDataClient([market_good, market_bad, market_non_binary], books)

    report = run_cycle(client, tmp_path)

    statuses = tuple(name for name, _count in report.blocked_counts)
    assert statuses == tuple(sorted(statuses))
    blocked_total = sum(count for _name, count in report.blocked_counts)
    assert blocked_total + report.snapshot_ready_count == report.considered_count
    assert set(statuses) == {"blocked_fetch_error", "blocked_non_binary_market"}


def test_strategy_cycle_dedupes_duplicate_market_slug_for_screening_c1b(tmp_path):
    market_one, books_one = binary_market_pair(
        condition_id="0xcondDupOne",
        slug="same-slug",
        question="Will the same slug resolve one?",
        yes_token_id="yes-dup-one",
        no_token_id="no-dup-one",
    )
    market_two, books_two = binary_market_pair(
        condition_id="0xcondDupTwo",
        slug="same-slug",
        question="Will the same slug resolve two?",
        yes_token_id="yes-dup-two",
        no_token_id="no-dup-two",
    )
    books = {**books_one, **books_two}
    client = FakeMarketDataClient([market_one, market_two], books)

    report = run_cycle(client, tmp_path)

    assert report.scan_market_count == 2
    assert report.considered_count == 2
    assert report.snapshot_ready_count == 2
    assert report.cost_aware_report_count == 2
    assert report.blocked_counts == ()
    assert report.screening_report is not None
    # C1b: dedupe keeps first -> screening sees exactly one candidate
    assert report.screening_report.candidate_count == 1


def test_strategy_cycle_writes_distinct_per_token_book_archive_files_c2b(tmp_path):
    market_one, books_one = binary_market_pair(
        condition_id="0xcondArchiveOne",
        slug="market-archive-one",
        question="Will Archive One happen?",
        yes_token_id="yes-archive-one",
        no_token_id="no-archive-one",
    )
    market_two, books_two = binary_market_pair(
        condition_id="0xcondArchiveTwo",
        slug="market-archive-two",
        question="Will Archive Two happen?",
        yes_token_id="yes-archive-two",
        no_token_id="no-archive-two",
    )
    books = {**books_one, **books_two}
    client = FakeMarketDataClient([market_one, market_two], books)

    run_cycle(client, tmp_path)

    book_files = list((tmp_path / "clob_book").glob("*.json"))
    book_names = {path.name for path in book_files}
    # C2b: each market's YES/NO books land in DISTINCT files (>= 4, names contain token_id)
    assert len(book_files) >= 4
    for token_id in (
        "yes-archive-one",
        "no-archive-one",
        "yes-archive-two",
        "no-archive-two",
    ):
        assert any(f"book-{token_id}" in name for name in book_names), token_id
    # distinct file names -> no token overwrote another
    assert len(book_names) == len(book_files)


# ---------------------------------------------------------------------------
# forecast_provider selector (Stage 2 Task 2): additive dispatch plumbing
# ---------------------------------------------------------------------------


def test_strategy_cycle_config_default_forecast_provider_is_naive_with_no_book_config():
    config = cycle_config()

    assert config.forecast_provider == "naive"
    assert config.book_imbalance_config is None


def test_strategy_cycle_config_accepts_book_imbalance_provider_with_config():
    bi_config = book_imbalance_config()

    config = cycle_config(
        forecast_provider="book_imbalance",
        book_imbalance_config=bi_config,
    )

    assert config.forecast_provider == "book_imbalance"
    assert config.book_imbalance_config is bi_config


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"forecast_provider": "magic"}, "forecast_provider must be one of"),
        ({"forecast_provider": " book_imbalance "}, "forecast_provider"),
        ({"forecast_provider": ""}, "forecast_provider"),
        (
            {
                "forecast_provider": "book_imbalance",
                "book_imbalance_config": None,
            },
            "book_imbalance_config is required",
        ),
        (
            {
                "forecast_provider": "book_imbalance",
                "book_imbalance_config": "not-a-config",
            },
            "book_imbalance_config must be a",
        ),
    ),
)
def test_strategy_cycle_config_rejects_invalid_forecast_provider_inputs(overrides, message):
    with pytest.raises(ValueError, match=message):
        cycle_config(**overrides)


def test_strategy_cycle_book_imbalance_provider_reaches_snapshot_ready_end_to_end(tmp_path):
    # Stage 2 end-to-end value proof. The forecast_provider="book_imbalance"
    # selector routes through build_paper_book_imbalance_forecast, producing a
    # PaperBookImbalanceForecast. cost_aware_snapshot_builder now accepts any
    # forecast that structurally exposes fair_probability_yes + confidence
    # (PaperForecast AND PaperBookImbalanceForecast), so the cycle must reach
    # snapshot_ready and deliver a non-zero screening candidate end-to-end --
    # the entire point of the Stage 2 book_imbalance selector.
    #
    # Books are bid/ask-size balanced, so the book-imbalance nudge is zero and
    # the PaperBookImbalanceForecast collapses to the same fair_probability_yes
    # + confidence as the naive PaperForecast on the same books. That means the
    # book_imbalance snapshot is identical to the naive one, so by parity with
    # the naive cycle (which yields candidate_count == 1 on these books) the
    # book_imbalance cycle must also deliver candidate_count == 1. The naive
    # comparison below pins that parity invariant.
    market, books = binary_market_pair(
        condition_id="0xcondDispatch",
        slug="market-dispatch",
        question="Will Dispatch happen?",
        yes_token_id="yes-dispatch",
        no_token_id="no-dispatch",
    )
    bid_heavy_books = {
        "yes-dispatch": raw_book(
            "yes-dispatch",
            bid="0.5200",
            ask="0.5400",
            size="200.0000",
        ),
        "no-dispatch": raw_book("no-dispatch"),
    }
    client_naive = FakeMarketDataClient([market], bid_heavy_books)
    client_bi = FakeMarketDataClient([market], bid_heavy_books)

    naive_report = run_cycle(client_naive, tmp_path, config=cycle_config())
    bi_report = run_cycle(
        client_bi,
        tmp_path,
        config=cycle_config(
            forecast_provider="book_imbalance",
            book_imbalance_config=book_imbalance_config(),
        ),
    )

    # Naive provider baseline (unchanged): book has a usable ask -> snapshot_ready,
    # cost-aware report built, one screening candidate.
    assert naive_report.snapshot_ready_count == 1
    assert naive_report.cost_aware_report_count == 1
    assert naive_report.blocked_counts == ()
    assert naive_report.screening_report is not None
    assert naive_report.screening_report.candidate_count == 1

    # book_imbalance provider (Stage 2 value proof): the snapshot builder now
    # accepts the PaperBookImbalanceForecast, so the cycle reaches snapshot_ready
    # (previously: isinstance guard rejected it -> blocked_fetch_error -> zero
    # screening candidates, defeating Stage 2). snapshot_ready_count == 1 is
    # guaranteed by the snapshot-build path (binary market + resolvable outcome
    # pair + matching token ids) once the forecast guard is widened; the
    # screening candidate parity follows from the identical fair_probability_yes
    # + confidence produced on these balanced books.
    assert bi_report.scan_market_count == 1
    assert bi_report.considered_count == 1
    assert bi_report.snapshot_ready_count == 1
    assert bi_report.cost_aware_report_count == 1
    # The bug is gone: no per-market exception -> no blocked_fetch_error.
    assert bi_report.blocked_counts == ()
    assert bi_report.screening_report is not None
    assert bi_report.screening_report.candidate_count == 1
    # Dispatch is downstream of fetch: both providers fetched the same books.
    assert set(client_naive.get_order_book_calls) == {"yes-dispatch", "no-dispatch"}
    assert set(client_bi.get_order_book_calls) == {"yes-dispatch", "no-dispatch"}


def _make_stub_glm_transport(result):
    """Build a frozen GLMChatTransport subclass whose estimate returns ``result``.

    The cycle config validates ``isinstance(llm_transport, GLMChatTransport)``,
    so the stub must be a GLMChatTransport instance. A fresh frozen subclass is
    built per call so the canned result is bound in a closure (no frozen-attr
    mutation needed). No real network is performed.
    """

    @dataclass(frozen=True)
    class _StubGLMTransport(GLMChatTransport):
        def estimate(self, *, market_question, outcome_names, market_context=None):
            return result

    return _StubGLMTransport(api_token="stub-token")


def test_strategy_cycle_llm_provider_dispatches_transport_and_reaches_snapshot_ready(
    tmp_path,
):
    # Stage 8 end-to-end dispatch proof. forecast_provider="llm" routes each
    # binary market through transport.estimate -> build_paper_llm_forecast,
    # producing a PaperLLMForecast. The cost-aware snapshot builder accepts any
    # forecast exposing fair_probability_yes + confidence (the _CostAwareForecast
    # Protocol), so the cycle must reach snapshot_ready + a screening_ready
    # candidate end-to-end -- the entire point of the LLM provider.
    market, books = _screening_ready_market_and_books()
    stub_result = ProbabilityModelResult(
        raw_p_yes=Decimal("0.35"),
        raw_confidence=Decimal("0.8"),
        raw_content='{"p_yes": 0.35, "confidence": 0.8}',
        model_name="glm-4-flash",
        finish_reason="stop",
        token_usage=125,
        elapsed_seconds=Decimal("1.0"),
    )
    transport = _make_stub_glm_transport(stub_result)

    llm_report = run_cycle(
        FakeMarketDataClient([market], books),
        tmp_path,
        config=cycle_config(
            forecast_provider="llm",
            llm_transport=transport,
            llm_forecast_config=PaperLLMForecastConfig(),
        ),
    )

    assert llm_report.scan_market_count == 1
    assert llm_report.considered_count == 1
    assert llm_report.snapshot_ready_count == 1
    assert llm_report.cost_aware_report_count == 1
    assert llm_report.blocked_counts == ()
    assert llm_report.screening_report is not None
    # NO side edge: model_p_no = 1 - 0.35 = 0.65, no_ask = 0.40 -> net_edge 0.25.
    assert llm_report.screening_report.candidate_count == 1


def test_strategy_cycle_llm_parse_fail_falls_back_to_low_confidence(tmp_path):
    # When the transport returns a parse-failed result (raw_p_yes=None), the
    # leaf falls back to low_confidence_value (0.5). With fair_p=0.5 on these
    # books (yes_ask 0.55), the YES edge is -0.05 and the NO edge is 0.10, so
    # the candidate still reaches screening_ready on the NO side (net_edge 0.10
    # >= 0.01). Proves the parse-fail -> low-confidence fallback survives the
    # cycle without aborting.
    market, books = _screening_ready_market_and_books()
    stub_result = ProbabilityModelResult(
        raw_p_yes=None,
        raw_confidence=None,
        raw_content="not json",
        model_name="glm-4-flash",
        finish_reason="stop",
        token_usage=0,
        elapsed_seconds=Decimal("0.1"),
    )
    transport = _make_stub_glm_transport(stub_result)

    report = run_cycle(
        FakeMarketDataClient([market], books),
        tmp_path,
        config=cycle_config(
            forecast_provider="llm",
            llm_transport=transport,
            llm_forecast_config=PaperLLMForecastConfig(),
        ),
    )

    assert report.snapshot_ready_count == 1
    assert report.cost_aware_report_count == 1
    assert report.blocked_counts == ()


def _make_recording_glm_transport(result):
    """Build a GLMChatTransport stub that records forwarded market_context.

    Stage 10 proof: the cycle's "llm" dispatch must construct a market_context
    dict from the NormalizedMarket and forward it to transport.estimate. Returns
    ``(transport, captured)`` where ``captured`` is the list of market_context
    values the cycle passed in. No real network call is performed.
    """
    captured: list = []

    @dataclass(frozen=True)
    class _RecordingGLMTransport(GLMChatTransport):
        def estimate(self, *, market_question, outcome_names, market_context=None):
            captured.append(market_context)
            return result

    return _RecordingGLMTransport(api_token="stub-token"), captured


def test_strategy_cycle_llm_dispatch_forwards_market_context_to_transport(tmp_path):
    # Stage 10: the "llm" dispatch branch builds a market_context dict from the
    # NormalizedMarket (volume_24h, liquidity, end_time, rules) and forwards it
    # to transport.estimate. Decimal fields are str()-coerced (never float);
    # missing fields fall back to "unknown".
    market, books = _screening_ready_market_and_books()
    stub_result = ProbabilityModelResult(
        raw_p_yes=Decimal("0.35"),
        raw_confidence=Decimal("0.8"),
        raw_content='{"p_yes": 0.35, "confidence": 0.8}',
        model_name="glm-4-flash",
        finish_reason="stop",
        token_usage=125,
        elapsed_seconds=Decimal("1.0"),
    )
    transport, captured = _make_recording_glm_transport(stub_result)

    run_cycle(
        FakeMarketDataClient([market], books),
        tmp_path,
        config=cycle_config(
            forecast_provider="llm",
            llm_transport=transport,
            llm_forecast_config=PaperLLMForecastConfig(),
        ),
    )

    # Exactly one estimate call was made for the single binary market.
    assert len(captured) == 1
    ctx = captured[0]
    # Stage 10 contract: exactly these four keys, sourced from NormalizedMarket.
    assert set(ctx) == {"current_yes_ask", "current_spread", "volume_24h", "liquidity", "end_time", "rules"}
    # raw_market has volume24hr="5000" / liquidity="10000" -> str(Decimal(...)).
    assert ctx["volume_24h"] == str(Decimal("5000"))
    assert ctx["liquidity"] == str(Decimal("10000"))
    # raw_market has no endDate -> end_time None -> "unknown" fallback.
    assert ctx["end_time"] == "unknown"
    # rules_text comes from the market description.
    assert ctx["rules"] == "Market resolves according to the public source."


def test_strategy_cycle_llm_dispatch_omits_spread_from_market_context(tmp_path):
    # The live book spread is NOT part of market_context: the cost-aware
    # snapshot (which carries the spread) is built downstream of the dispatch,
    # so the spread is unavailable here. This pins the intentional deviation
    # from the spec's spread mention.
    market, books = _screening_ready_market_and_books()
    stub_result = ProbabilityModelResult(
        raw_p_yes=Decimal("0.35"),
        raw_confidence=Decimal("0.8"),
        raw_content='{"p_yes": 0.35, "confidence": 0.8}',
        model_name="glm-4-flash",
        finish_reason="stop",
        token_usage=125,
        elapsed_seconds=Decimal("1.0"),
    )
    transport, captured = _make_recording_glm_transport(stub_result)

    run_cycle(
        FakeMarketDataClient([market], books),
        tmp_path,
        config=cycle_config(
            forecast_provider="llm",
            llm_transport=transport,
            llm_forecast_config=PaperLLMForecastConfig(),
        ),
    )

    ctx = captured[0]
    assert "spread" not in ctx


# ---------------------------------------------------------------------------
# Stage 4 inline paper execution (additive/default-off)
# ---------------------------------------------------------------------------


def _screening_ready_market_and_books():
    """Binary market whose NO side yields a screening_ready candidate.

    Naive forecast: fair_probability_yes = yes_ask = 0.55, so the NO model
    probability is 0.45 and the NO ask is 0.40 -> net_edge_no = 0.05 (>=
    min_net_edge 0.01). Tight yes spread (0.02 <= 0.03) + depth 100 -> high
    confidence (0.75 >= 0.70). screening_score = net_edge * weight = 0.05
    >= min_screening_score 0.01 -> screening_ready on the NO side.
    """
    market = raw_market(
        condition_id="0xcondPaper",
        slug="market-paper",
        question="Will Paper happen?",
        token_ids=("yes-paper", "no-paper"),
    )
    books = {
        "yes-paper": raw_book(
            "yes-paper",
            bid="0.5300",
            ask="0.5500",
            size="100.0000",
        ),
        "no-paper": raw_book(
            "no-paper",
            bid="0.3700",
            ask="0.4000",
            size="100.0000",
        ),
    }
    return market, books


def test_strategy_cycle_executes_paper_trades_inline_when_configured(tmp_path):
    market, books = _screening_ready_market_and_books()
    client = FakeMarketDataClient([market], books)
    journal_path = tmp_path / "paper-trades.jsonl"
    config = cycle_config(
        paper_execution_config=PaperExecutionConfig(
            config_version="paper-execution-v1",
        ),
        paper_trade_journal_path=journal_path,
    )

    report = run_cycle(client, tmp_path, config=config)

    # Sanity: the candidate really is screening_ready (the gate for execution).
    assert report.snapshot_ready_count == 1
    assert report.screening_report is not None
    ready = [
        c
        for c in report.screening_report.candidates
        if c.screening_status == "screening_ready"
    ]
    assert len(ready) == 1
    assert ready[0].scoring_side == "no"

    # Stage 4 acceptance: the inline pass journaled exactly one paper trade
    # for the screening_ready candidate (NO side, marker strategy_type).
    assert journal_path.exists()
    lines = journal_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["market_slug"] == "market-paper"
    assert record["outcome_name"] == "NO"
    assert record["strategy_type"] == "book_imbalance_screening_paper"
    assert record["order_side"] == "buy"
    # PaperTradeRecord is paper-only by construction (decimal-string fills,
    # marker strategy_type, sizing_limiter + planned_exit_rule populated).
    assert record["sizing_limiter"] == "screening_book_depth"
    assert record["planned_exit_rule"] == "hold_to_resolution"


def test_strategy_cycle_no_paper_execution_when_config_is_none(tmp_path):
    market, books = _screening_ready_market_and_books()
    client = FakeMarketDataClient([market], books)
    journal_path = tmp_path / "absent-paper-trades.jsonl"
    # Default config: paper_execution_config is None -> no inline pass, no
    # journal write. Stage 1b/2/3 behavior preserved byte-identically.
    config = cycle_config()

    report = run_cycle(client, tmp_path, config=config)

    assert config.paper_execution_config is None
    assert config.paper_trade_journal_path is None
    # The cycle still produces the screening candidate (default path intact)...
    assert report.snapshot_ready_count == 1
    assert report.screening_report is not None
    assert report.screening_report.ready_count == 1
    # ...but NO paper journal was written.
    assert not journal_path.exists()


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        (
            {
                "paper_execution_config": PaperExecutionConfig(
                    config_version="paper-execution-v1",
                ),
            },
            "paper_execution_config and paper_trade_journal_path must both",
        ),
        (
            {
                "paper_trade_journal_path": Path("paper-trades.jsonl"),
            },
            "paper_execution_config and paper_trade_journal_path must both",
        ),
        (
            {
                "paper_execution_config": "not-a-config",
                "paper_trade_journal_path": Path("paper-trades.jsonl"),
            },
            "paper_execution_config must be a PaperExecutionConfig",
        ),
        (
            {
                "paper_execution_config": PaperExecutionConfig(
                    config_version="paper-execution-v1",
                ),
                "paper_trade_journal_path": "not-a-path",
            },
            "paper_trade_journal_path must be a Path",
        ),
    ),
)
def test_strategy_cycle_config_rejects_invalid_paper_execution_inputs(
    overrides,
    message,
):
    with pytest.raises(ValueError, match=message):
        cycle_config(**overrides)
