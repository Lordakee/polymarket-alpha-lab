import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.book_imbalance_forecast import (
    PaperBookImbalanceForecastConfig,
    build_paper_book_imbalance_forecast,
)
from polymarket_alpha_lab.cost_aware_event_strategy import PaperCostAwareEventMarketSnapshot
from polymarket_alpha_lab.cost_aware_snapshot_builder import (
    PaperCostAwareSnapshotAttempt,
    PaperCostAwareSnapshotConfig,
    PaperCostAwareSnapshotLog,
    build_paper_cost_aware_event_market_snapshot,
)
from polymarket_alpha_lab.domain import (
    MarketSnapshot,
    NormalizedMarket,
    OrderBookLevel,
    OrderBookSnapshot,
    OutcomeToken,
)
from polymarket_alpha_lab.forecast_provider import PaperForecast


GENERATED_AT = datetime(2026, 6, 16, 14, 0, tzinfo=UTC)


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


def normalized_market(**overrides):
    values = {
        "condition_id": "0xcondition",
        "market_slug": "fed-cut-june-2026",
        "question": "Will the Fed cut rates by June 2026?",
        "active": True,
        "closed": False,
        "accepting_orders": True,
        "end_time": None,
        "volume_24h": Decimal("1000.0000"),
        "liquidity": Decimal("500.0000"),
        "captured_at": GENERATED_AT,
        "tokens": (
            OutcomeToken(
                condition_id="0xcondition",
                token_id="yes-token",
                outcome_index=0,
                outcome_name="Yes",
            ),
            OutcomeToken(
                condition_id="0xcondition",
                token_id="no-token",
                outcome_index=1,
                outcome_name="No",
            ),
        ),
        "rules_text": "Market resolves according to the public source.",
        "resolution_source": "public-source",
    }
    values.update(overrides)
    return NormalizedMarket(
        market=MarketSnapshot(
            condition_id=values["condition_id"],
            market_slug=values["market_slug"],
            question=values["question"],
            active=values["active"],
            closed=values["closed"],
            accepting_orders=values["accepting_orders"],
            end_time=values["end_time"],
            volume_24h=values["volume_24h"],
            liquidity=values["liquidity"],
            captured_at=values["captured_at"],
        ),
        tokens=values["tokens"],
        rules_text=values["rules_text"],
        resolution_source=values["resolution_source"],
    )


def book_level(price, size):
    return OrderBookLevel(price=Decimal(price), size=Decimal(size))


def yes_book(**overrides):
    values = {
        "token_id": "yes-token",
        "bids": (book_level("0.5200", "250.0000"),),
        "asks": (book_level("0.5400", "250.0000"),),
        "captured_at": GENERATED_AT,
    }
    values.update(overrides)
    return OrderBookSnapshot(**values)


def no_book(**overrides):
    values = {
        "token_id": "no-token",
        "bids": (book_level("0.4400", "200.0000"),),
        "asks": (book_level("0.4800", "200.0000"),),
        "captured_at": GENERATED_AT,
    }
    values.update(overrides)
    return OrderBookSnapshot(**values)


def forecast(**overrides):
    values = {
        "generated_at": GENERATED_AT,
        "config_version": "naive-forecast-v1",
        "market_slug": "fed-cut-june-2026",
        "question": "Will the Fed cut rates by June 2026?",
        "fair_probability_yes": Decimal("0.540000"),
        "confidence": Decimal("0.750000"),
        "basis": "yes_ask_naive_v0",
        "reason_codes": ("yes_ask_basis", "high_confidence_book"),
        "paper_only": True,
        "report_only": True,
    }
    values.update(overrides)
    return PaperForecast(**values)


def build_snapshot(market=None, yes=None, no=None, forecast_value=None, config=None, generated_at=GENERATED_AT):
    return build_paper_cost_aware_event_market_snapshot(
        market or normalized_market(),
        yes or yes_book(),
        no or no_book(),
        forecast_value or forecast(),
        config=config or snapshot_config(),
        generated_at=generated_at,
    )


def test_cost_aware_snapshot_builder_builds_snapshot_from_binary_market_and_books():
    result = build_snapshot()

    assert isinstance(result, PaperCostAwareSnapshotAttempt)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "snapshot-builder-v1"
    assert result.market_slug == "fed-cut-june-2026"
    assert result.question == "Will the Fed cut rates by June 2026?"
    assert result.status == "snapshot_ready"
    assert result.reason_codes == ("snapshot_built",)
    assert isinstance(result.snapshot, PaperCostAwareEventMarketSnapshot)
    assert result.snapshot.market_slug == "fed-cut-june-2026"
    assert result.snapshot.question == "Will the Fed cut rates by June 2026?"
    assert result.snapshot.fair_probability_yes == Decimal("0.540000")
    assert result.snapshot.confidence == Decimal("0.750000")


def test_cost_aware_snapshot_builder_accepts_book_imbalance_forecast_via_protocol():
    # Stage 3 fix: the snapshot builder accepts any forecast satisfying the
    # Forecast Protocol (fair_probability_yes + confidence), not just PaperForecast.
    # PaperBookImbalanceForecast must now reach snapshot_ready end-to-end.
    from polymarket_alpha_lab.book_imbalance_forecast import (
        PaperBookImbalanceForecastConfig,
        build_paper_book_imbalance_forecast,
    )

    bi_forecast = build_paper_book_imbalance_forecast(
        normalized_market(),
        yes_book(),
        no_book(),
        config=PaperBookImbalanceForecastConfig(
            config_version="book-imbalance-forecast-v1"
        ),
        generated_at=GENERATED_AT,
    )

    result = build_snapshot(forecast_value=bi_forecast)

    assert result.status == "snapshot_ready"
    assert isinstance(result.snapshot, PaperCostAwareEventMarketSnapshot)
    assert result.snapshot.fair_probability_yes == bi_forecast.fair_probability_yes
    assert result.snapshot.confidence == bi_forecast.confidence
    assert result.snapshot.yes_bid == Decimal("0.5200")
    assert result.snapshot.yes_ask == Decimal("0.5400")
    assert result.snapshot.yes_ask_size == Decimal("250.0000")
    assert result.snapshot.no_bid == Decimal("0.4400")
    assert result.snapshot.no_ask == Decimal("0.4800")
    assert result.snapshot.no_ask_size == Decimal("200.0000")
    assert result.snapshot.spread == Decimal("0.020000")
    assert result.snapshot.resolution_risk == Decimal("0.100000")


def test_cost_aware_snapshot_builder_accepts_paper_book_imbalance_forecast():
    # Stage 2 regression / bug-fix proof: the builder must accept ANY forecast
    # that structurally exposes fair_probability_yes + confidence, including
    # PaperBookImbalanceForecast (a separate frozen dataclass from the naive
    # PaperForecast). Previously the leaf's isinstance(forecast, PaperForecast)
    # guard hard-rejected it with ValueError, which -- caught by strategy_cycle's
    # per-market isolation -- zeroed out the book_imbalance selector end-to-end
    # (every market -> blocked_fetch_error, empty screening queue). This test
    # builds a real PaperBookImbalanceForecast via its public builder and proves
    # the snapshot now reaches snapshot_ready with the nudged fair value.
    yes = yes_book(
        bids=(book_level("0.5200", "300.0000"),),
        asks=(book_level("0.5400", "100.0000"),),
    )
    imbalance_forecast = build_paper_book_imbalance_forecast(
        normalized_market(),
        yes,
        no_book(),
        config=PaperBookImbalanceForecastConfig(
            config_version="book-imbalance-forecast-v1",
            imbalance_strength=Decimal("0.0200"),
            max_nudge=Decimal("0.0500"),
            min_book_depth=Decimal("1.0000"),
            low_confidence_value=Decimal("0.5000"),
            high_confidence_value=Decimal("0.7500"),
            max_spread_for_high_confidence=Decimal("0.0300"),
        ),
        generated_at=GENERATED_AT,
    )

    result = build_paper_cost_aware_event_market_snapshot(
        normalized_market(),
        yes,
        no_book(),
        imbalance_forecast,
        config=snapshot_config(),
        generated_at=GENERATED_AT,
    )

    assert result.status == "snapshot_ready"
    assert isinstance(result.snapshot, PaperCostAwareEventMarketSnapshot)
    assert result.reason_codes == ("snapshot_built",)
    assert result.snapshot.market_slug == "fed-cut-june-2026"
    # Bid-heavy YES book (bid_size 300 vs ask_size 100) -> imbalance +0.5 ->
    # nudge +0.01 -> fair_probability_yes nudged up from the 0.5400 yes_ask
    # baseline to 0.550000. This proves the PaperBookImbalanceForecast value
    # (not a naive PaperForecast) flowed through the builder unchanged.
    assert result.snapshot.fair_probability_yes == Decimal("0.550000")
    assert result.snapshot.confidence == Decimal("0.750000")
    assert result.snapshot.yes_ask == Decimal("0.5400")
    assert result.snapshot.yes_ask_size == Decimal("100.0000")


def test_cost_aware_snapshot_builder_still_accepts_naive_paper_forecast():
    # Regression guard: widening the forecast guard to the structural protocol
    # must NOT regress the original naive PaperForecast path. The same canned
    # PaperForecast that always worked must still reach snapshot_ready.
    result = build_snapshot(forecast_value=forecast())

    assert result.status == "snapshot_ready"
    assert isinstance(result.snapshot, PaperCostAwareEventMarketSnapshot)
    assert result.snapshot.fair_probability_yes == Decimal("0.540000")
    assert result.snapshot.confidence == Decimal("0.750000")


def test_cost_aware_snapshot_builder_rejects_forecast_missing_protocol_fields():
    # The widened protocol guard is structural but still a guard: an object that
    # does NOT expose fair_probability_yes + confidence must be rejected with a
    # clear ValueError (not silently accepted).
    with pytest.raises(ValueError, match="fair_probability_yes and confidence"):
        build_paper_cost_aware_event_market_snapshot(
            normalized_market(),
            yes_book(),
            no_book(),
            object(),  # no fair_probability_yes / confidence attributes
            config=snapshot_config(),
            generated_at=GENERATED_AT,
        )


def test_cost_aware_snapshot_builder_uses_no_side_spread_when_yes_side_is_unavailable():
    result = build_snapshot(yes=yes_book(asks=(), bids=()))

    assert result.status == "snapshot_ready"
    assert result.snapshot is not None
    assert result.snapshot.yes_ask is None
    assert result.snapshot.yes_bid is None
    assert result.snapshot.spread == Decimal("0.040000")


@pytest.mark.parametrize(
    ("market_overrides", "expected_status"),
    (
        ({"tokens": ()}, "blocked_non_binary_market"),
        (
            {
                "tokens": (
                    OutcomeToken(
                        condition_id="0xcondition",
                        token_id="yes-token",
                        outcome_index=0,
                        outcome_name="Yes",
                    ),
                    OutcomeToken(
                        condition_id="0xcondition",
                        token_id="no-token",
                        outcome_index=1,
                        outcome_name="No",
                    ),
                    OutcomeToken(
                        condition_id="0xcondition",
                        token_id="maybe-token",
                        outcome_index=2,
                        outcome_name="Maybe",
                    ),
                )
            },
            "blocked_non_binary_market",
        ),
    ),
)
def test_cost_aware_snapshot_builder_blocks_non_binary_markets(market_overrides, expected_status):
    result = build_snapshot(market=normalized_market(**market_overrides))

    assert result.status == expected_status
    assert result.snapshot is None
    assert result.reason_codes == ("non_binary_market",)


def test_cost_aware_snapshot_builder_resolves_yes_no_by_outcome_name_case_insensitively():
    market = normalized_market(
        tokens=(
            OutcomeToken(
                condition_id="0xcondition",
                token_id="yes-token",
                outcome_index=1,
                outcome_name="long",
            ),
            OutcomeToken(
                condition_id="0xcondition",
                token_id="no-token",
                outcome_index=0,
                outcome_name="false",
            ),
        ),
    )

    result = build_snapshot(market=market)

    assert result.status == "snapshot_ready"
    assert result.snapshot is not None
    assert result.snapshot.yes_bid == Decimal("0.5200")
    assert result.snapshot.no_ask == Decimal("0.4800")


def test_cost_aware_snapshot_builder_falls_back_to_outcome_index_for_non_standard_names():
    market = normalized_market(
        tokens=(
            OutcomeToken(
                condition_id="0xcondition",
                token_id="first-token",
                outcome_index=0,
                outcome_name="Side A",
            ),
            OutcomeToken(
                condition_id="0xcondition",
                token_id="second-token",
                outcome_index=1,
                outcome_name="Side B",
            ),
        ),
    )
    yes = yes_book(token_id="first-token")
    no = no_book(token_id="second-token")

    result = build_snapshot(market=market, yes=yes, no=no)

    assert result.status == "snapshot_ready"
    assert result.snapshot is not None
    assert result.snapshot.market_slug == "fed-cut-june-2026"


def test_cost_aware_snapshot_builder_blocks_unresolvable_outcome_pairs():
    market = normalized_market(
        tokens=(
            OutcomeToken(
                condition_id="0xcondition",
                token_id="shared-token",
                outcome_index=0,
                outcome_name="Side A",
            ),
            OutcomeToken(
                condition_id="0xcondition",
                token_id="shared-token",
                outcome_index=1,
                outcome_name="Side B",
            ),
        ),
    )

    result = build_snapshot(market=market)

    assert result.status == "blocked_unresolvable_outcome_pair"
    assert result.snapshot is None
    assert result.reason_codes == ("unresolvable_outcome_pair",)


def test_cost_aware_snapshot_builder_blocks_book_token_mismatches():
    result = build_snapshot(
        yes=yes_book(token_id="wrong-yes-token"),
        no=no_book(token_id="wrong-no-token"),
    )

    assert result.status == "blocked_book_token_mismatch"
    assert result.snapshot is None
    assert result.reason_codes == ("book_token_mismatch",)


def test_cost_aware_snapshot_builder_bumps_resolution_risk_when_rules_are_missing():
    result = build_snapshot(
        market=normalized_market(rules_text=None, resolution_source=None),
    )

    assert result.snapshot is not None
    assert result.snapshot.resolution_risk == Decimal("0.300000")


def test_cost_aware_snapshot_builder_caps_resolution_risk_near_resolution():
    market = normalized_market(
        end_time=datetime(2026, 6, 16, 20, 0, tzinfo=UTC),
    )

    result = build_snapshot(market=market)

    assert result.snapshot is not None
    assert result.snapshot.resolution_risk == Decimal("0.050000")


@pytest.mark.parametrize(
    ("config_overrides", "message"),
    (
        ({"config_version": ""}, "config_version"),
        ({"default_resolution_risk": Decimal("-0.0001")}, "default_resolution_risk"),
        ({"missing_rules_resolution_risk": Decimal("NaN")}, "missing_rules_resolution_risk|finite"),
        ({"imminent_resolution_risk_cap": "0.0500"}, "imminent_resolution_risk_cap"),
        ({"imminent_resolution_horizon_hours": 0}, "imminent_resolution_horizon_hours|positive"),
        ({"imminent_resolution_horizon_hours": True}, "imminent_resolution_horizon_hours|int"),
    ),
)
def test_cost_aware_snapshot_config_rejects_invalid_inputs(config_overrides, message):
    with pytest.raises(ValueError, match=message):
        snapshot_config(**config_overrides)


@pytest.mark.parametrize(
    ("attempt_overrides", "message"),
    (
        ({"generated_at": object()}, "datetime"),
        ({"config_version": ""}, "config_version"),
        ({"market_slug": " "}, "market_slug"),
        ({"question": ""}, "question"),
        ({"status": "snapshot_ready", "snapshot": None}, "snapshot"),
        ({"status": "unknown_status"}, "status"),
        ({"reason_codes": ()}, "reason_codes"),
        ({"reason_codes": (" snapshot_built",)}, "reason_codes"),
        ({"paper_only": False}, "paper_only"),
        ({"report_only": False}, "report_only"),
    ),
)
def test_cost_aware_snapshot_attempt_rejects_invalid_inputs(attempt_overrides, message):
    values = {
        "generated_at": GENERATED_AT,
        "config_version": "snapshot-builder-v1",
        "market_slug": "fed-cut-june-2026",
        "question": "Will the Fed cut rates by June 2026?",
        "status": "snapshot_ready",
        "snapshot": build_snapshot().snapshot,
        "reason_codes": ("snapshot_built",),
        "paper_only": True,
        "report_only": True,
    }
    values.update(attempt_overrides)
    if values["status"] != "snapshot_ready":
        values["snapshot"] = None

    with pytest.raises(ValueError, match=message):
        PaperCostAwareSnapshotAttempt(**values)


def test_cost_aware_snapshot_attempt_rejects_status_snapshot_invariant_both_directions():
    snapshot_value = build_snapshot().snapshot

    with pytest.raises(ValueError, match="snapshot"):
        PaperCostAwareSnapshotAttempt(
            generated_at=GENERATED_AT,
            config_version="snapshot-builder-v1",
            market_slug="fed-cut-june-2026",
            question="Will the Fed cut rates by June 2026?",
            status="snapshot_ready",
            snapshot=None,
            reason_codes=("snapshot_built",),
        )
    with pytest.raises(ValueError, match="snapshot"):
        PaperCostAwareSnapshotAttempt(
            generated_at=GENERATED_AT,
            config_version="snapshot-builder-v1",
            market_slug="fed-cut-june-2026",
            question="Will the Fed cut rates by June 2026?",
            status="blocked_missing_yes_book",
            snapshot=snapshot_value,
            reason_codes=("snapshot_built",),
        )


def test_cost_aware_snapshot_builder_dataclasses_are_frozen_and_revalidate_report_flags():
    attempt = build_snapshot()
    config = snapshot_config()

    with pytest.raises(FrozenInstanceError):
        attempt.status = "blocked_missing_forecast"
    with pytest.raises(FrozenInstanceError):
        config.config_version = "other"
    with pytest.raises(ValueError, match="paper_only"):
        replace(attempt, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(attempt, report_only=False)


def test_cost_aware_snapshot_log_appends_jsonl_decimal_strings_and_preserves_existing_file(tmp_path):
    attempt = build_snapshot()
    log = PaperCostAwareSnapshotLog(path=tmp_path / "nested" / "snapshot-builder.jsonl")

    log.append(attempt)
    log.append(attempt)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    stored = json.loads(lines[0])
    assert stored["paper_only"] is True
    assert stored["report_only"] is True
    assert stored["generated_at"] == "2026-06-16T14:00:00+00:00"
    assert stored["status"] == "snapshot_ready"
    assert stored["reason_codes"] == ["snapshot_built"]
    assert stored["snapshot"]["yes_ask"] == "0.5400"
    assert stored["snapshot"]["yes_ask_size"] == "250.0000"
    assert stored["snapshot"]["spread"] == "0.020000"
    assert stored["snapshot"]["resolution_risk"] == "0.100000"

    existing_log_path = tmp_path / "existing.jsonl"
    existing_log_path.write_text("existing\n", encoding="utf-8")
    with pytest.raises(ValueError, match="PaperCostAwareSnapshotAttempt"):
        PaperCostAwareSnapshotLog(path=existing_log_path).append(object())
    assert existing_log_path.read_text(encoding="utf-8") == "existing\n"
