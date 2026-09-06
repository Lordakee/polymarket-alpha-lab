from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab import strategy_cycle
from polymarket_alpha_lab.paper_execution import PaperExecutionConfig
from polymarket_alpha_lab.strategy_cycle import (
    PaperStrategyCycleReport,
    run_strategy_cycle,
)
from tests.test_strategy_cycle import (
    GENERATED_AT,
    FakeMarketDataClient,
    _screening_ready_market_and_books,
    binary_market_pair,
    cycle_config,
    scan_config,
)


def _blocked_codes(report: PaperStrategyCycleReport) -> dict[str, int]:
    return {code: count for code, count in report.blocked_counts}


def test_fetch_stage_failure_keeps_blocked_fetch_error_and_records_type(tmp_path):
    market, _books = binary_market_pair(
        condition_id="0xcondFetch",
        slug="fetch-fail",
        question="Fetch failure?",
        yes_token_id="7001",
        no_token_id="7002",
    )

    class RaisingClient(FakeMarketDataClient):
        def get_order_book(self, *, token_id):
            raise ConnectionError("transport refused")

    client = RaisingClient([market], {})
    report = run_strategy_cycle(
        client=client,
        scan_config=scan_config(tmp_path),
        cycle_config=cycle_config(),
        generated_at=GENERATED_AT,
    )
    codes = _blocked_codes(report)
    assert codes.get("blocked_fetch_error") == 1
    assert report.market_failure_types == ("ConnectionError",)
    assert report.paper_execution_failure_types == ()


def test_normalization_stage_failure_gets_its_own_code(tmp_path, monkeypatch):
    market, books = binary_market_pair(
        condition_id="0xcondNorm",
        slug="norm-fail",
        question="Normalization failure?",
        yes_token_id="7101",
        no_token_id="7102",
    )
    client = FakeMarketDataClient([market], books)

    def _bad_normalize(payload, *, captured_at):
        raise ValueError("malformed book")

    monkeypatch.setattr(strategy_cycle, "normalize_order_book", _bad_normalize)
    report = run_strategy_cycle(
        client=client,
        scan_config=scan_config(tmp_path),
        cycle_config=cycle_config(),
        generated_at=GENERATED_AT,
    )
    codes = _blocked_codes(report)
    assert codes.get("blocked_normalization_error") == 1
    assert "blocked_fetch_error" not in codes
    assert report.market_failure_types == ("ValueError",)


def test_forecast_stage_failure_gets_its_own_code(tmp_path):
    from dataclasses import dataclass

    from polymarket_alpha_lab.llm_research_transport import GLMChatTransport
    from polymarket_alpha_lab.llm_forecast import PaperLLMForecastConfig

    market, books = binary_market_pair(
        condition_id="0xcondFc",
        slug="forecast-fail",
        question="Forecast failure?",
        yes_token_id="7201",
        no_token_id="7202",
    )
    client = FakeMarketDataClient([market], books)

    @dataclass(frozen=True)
    class _ExplodingTransport(GLMChatTransport):
        def estimate(self, *, market_question, outcome_names, market_context=None):
            raise RuntimeError("provider unavailable")

    report = run_strategy_cycle(
        client=client,
        scan_config=scan_config(tmp_path),
        cycle_config=cycle_config(
            forecast_provider="llm",
            llm_transport=_ExplodingTransport(api_token="stub-token"),
            llm_forecast_config=PaperLLMForecastConfig(),
        ),
        generated_at=GENERATED_AT,
    )
    codes = _blocked_codes(report)
    assert codes.get("blocked_forecast_error") == 1
    assert "blocked_fetch_error" not in codes
    assert report.market_failure_types == ("RuntimeError",)


def test_paper_execution_failures_are_visible_not_silent(tmp_path, monkeypatch):
    market, books = _screening_ready_market_and_books()
    client = FakeMarketDataClient([market], books)
    config = cycle_config(
        paper_execution_config=PaperExecutionConfig(
            config_version="paper-execution-v1",
        ),
        paper_trade_journal_path=None,
    )
    sink_records: list[object] = []

    def _explode(*args, **kwargs):
        raise RuntimeError("simulated paper-execution defect")

    monkeypatch.setattr(
        strategy_cycle,
        "execute_paper_trade_from_screening",
        _explode,
    )
    report = run_strategy_cycle(
        client=client,
        scan_config=scan_config(tmp_path),
        cycle_config=config,
        generated_at=GENERATED_AT,
        paper_trade_record_sink=sink_records.append,
    )
    assert report.snapshot_ready_count == 1
    assert sink_records == []
    assert report.paper_execution_failure_types == ("RuntimeError",)


def test_new_report_fields_default_and_validate() -> None:
    report = PaperStrategyCycleReport(
        generated_at=datetime(2026, 9, 6, tzinfo=UTC),
        config_version="v1",
        scan_market_count=0,
        considered_count=0,
        snapshot_ready_count=0,
        cost_aware_report_count=0,
        blocked_counts=(),
        screening_report=None,
    )
    assert report.paper_execution_failure_types == ()
    assert report.market_failure_types == ()
    assert report.paper_only is True and report.report_only is True
    with pytest.raises(ValueError):
        PaperStrategyCycleReport(
            generated_at=datetime(2026, 9, 6, tzinfo=UTC),
            config_version="v1",
            scan_market_count=0,
            considered_count=0,
            snapshot_ready_count=0,
            cost_aware_report_count=0,
            blocked_counts=(),
            screening_report=None,
            market_failure_types=(1,),
        )
