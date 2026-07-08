from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_market_event_spread_shock_watch_report as api
from polymarket_alpha_lab.research_market_event_spread_shock_watch_report import (
    ResearchMarketEventSpreadShockObservation,
    ResearchMarketEventSpreadShockWatchConfig,
    ResearchMarketEventSpreadShockWatchItem,
    ResearchMarketEventSpreadShockWatchReport,
    build_research_market_event_spread_shock_watch_report,
    research_market_event_spread_shock_watch_digest,
    research_market_event_spread_shock_watch_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    event_domain: str,
    *,
    observed_at: datetime | None = None,
    spread_widening_bps: Decimal = d("10.000000"),
    depth_fade_ratio: Decimal = d("0.020000"),
    quote_staleness_seconds: Decimal = d("30.000000"),
    catalyst_pressure_score: Decimal = d("0.100000"),
    cost_friction_score: Decimal = d("0.050000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchMarketEventSpreadShockObservation:
    return ResearchMarketEventSpreadShockObservation(
        event_domain=event_domain,
        observed_at=(
            observed_at
            if observed_at is not None
            else GENERATED_AT - timedelta(minutes=5)
        ),
        spread_widening_bps=spread_widening_bps,
        depth_fade_ratio=depth_fade_ratio,
        quote_staleness_seconds=quote_staleness_seconds,
        catalyst_pressure_score=catalyst_pressure_score,
        cost_friction_score=cost_friction_score,
        reason_codes=reason_codes,
    )


def report(
    observations: tuple[ResearchMarketEventSpreadShockObservation, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    config: ResearchMarketEventSpreadShockWatchConfig | None = None,
) -> ResearchMarketEventSpreadShockWatchReport:
    return build_research_market_event_spread_shock_watch_report(
        observations,
        generated_at=generated_at,
        config=config,
    )


def test_empty_input_returns_public_safe_block_report() -> None:
    shock_report = report(())

    assert type(shock_report) is ResearchMarketEventSpreadShockWatchReport
    assert shock_report.generated_at == GENERATED_AT
    assert shock_report.domain_count == d("0")
    assert shock_report.observation_count == d("0")
    assert shock_report.pass_count == d("0")
    assert shock_report.watch_count == d("0")
    assert shock_report.block_count == d("0")
    assert shock_report.average_shock_score is None
    assert shock_report.max_shock_score == d("0.000000")
    assert shock_report.status == "block"
    assert shock_report.reason_codes == ("no_event_domain_observations",)
    assert shock_report.items == ()
    assert shock_report.paper_only is True
    assert shock_report.report_only is True
    assert shock_report.readonly is True


def test_groups_event_domains_and_detects_pass_watch_and_block_shocks() -> None:
    shock_report = report(
        (
            observation(
                "macro",
                spread_widening_bps=d("120.000000"),
                depth_fade_ratio=d("0.400000"),
                quote_staleness_seconds=d("600.000000"),
                catalyst_pressure_score=d("0.600000"),
                cost_friction_score=d("0.400000"),
                reason_codes=("manual_review",),
            ),
            observation(
                "crypto",
                spread_widening_bps=d("350.000000"),
                depth_fade_ratio=d("0.800000"),
                quote_staleness_seconds=d("1200.000000"),
                catalyst_pressure_score=d("0.900000"),
                cost_friction_score=d("0.900000"),
            ),
            observation("sports"),
            observation(
                "macro",
                spread_widening_bps=d("60.000000"),
                depth_fade_ratio=d("0.200000"),
                quote_staleness_seconds=d("300.000000"),
                catalyst_pressure_score=d("0.400000"),
                cost_friction_score=d("0.200000"),
            ),
        ),
    )

    sports_item, macro_item, crypto_item = shock_report.items
    assert tuple(item.status for item in shock_report.items) == (
        "pass",
        "watch",
        "block",
    )
    assert shock_report.status == "block"
    assert shock_report.domain_count == d("3")
    assert shock_report.observation_count == d("4")
    assert shock_report.pass_count == d("1")
    assert shock_report.watch_count == d("1")
    assert shock_report.block_count == d("1")
    assert shock_report.spread_widening_count == d("2")
    assert shock_report.depth_fade_count == d("2")
    assert shock_report.quote_staleness_count == d("2")
    assert shock_report.catalyst_pressure_count == d("2")
    assert shock_report.cost_friction_count == d("2")
    assert shock_report.average_shock_score == d("0.450769")
    assert shock_report.max_shock_score == d("1.000000")

    assert type(sports_item) is ResearchMarketEventSpreadShockWatchItem
    assert sports_item.event_domain == "sports"
    assert sports_item.shock_score == d("0.000000")
    assert sports_item.status == "pass"
    assert sports_item.reason_codes == ("spread_shock_pass",)

    assert macro_item.event_domain == "macro"
    assert macro_item.observation_count == d("2")
    assert macro_item.average_spread_widening_bps == d("90.000000")
    assert macro_item.max_spread_widening_bps == d("120.000000")
    assert macro_item.average_depth_fade_ratio == d("0.300000")
    assert macro_item.max_quote_staleness_seconds == d("600.000000")
    assert macro_item.spread_widening_pressure == d("0.222222")
    assert macro_item.depth_fade_pressure == d("0.333333")
    assert macro_item.quote_staleness_pressure == d("0.615385")
    assert macro_item.catalyst_pressure_component == d("0.400000")
    assert macro_item.cost_friction_pressure == d("0.300000")
    assert macro_item.shock_score == d("0.352308")
    assert macro_item.status == "watch"
    assert macro_item.reason_codes == (
        "aggregate_spread_widening_watch",
        "catalyst_pressure_watch",
        "cost_friction_watch",
        "depth_fade_watch",
        "input_manual_review",
        "quote_staleness_watch",
        "spread_shock_watch",
    )

    assert crypto_item.event_domain == "crypto"
    assert crypto_item.shock_score == d("1.000000")
    assert crypto_item.status == "block"
    assert crypto_item.reason_codes == (
        "aggregate_spread_widening_block",
        "catalyst_pressure_block",
        "cost_friction_block",
        "depth_fade_block",
        "quote_staleness_block",
        "spread_shock_block",
    )


def test_payload_and_digest_are_deterministic_decimal_string_only_and_public_safe() -> None:
    observations = (
        observation("sports"),
        observation(
            "macro",
            spread_widening_bps=d("120.000000"),
            depth_fade_ratio=d("0.400000"),
            quote_staleness_seconds=d("600.000000"),
            catalyst_pressure_score=d("0.600000"),
            cost_friction_score=d("0.400000"),
            reason_codes=("zeta", "alpha"),
        ),
        observation(
            "macro",
            spread_widening_bps=d("60.000000"),
            depth_fade_ratio=d("0.200000"),
            quote_staleness_seconds=d("300.000000"),
            catalyst_pressure_score=d("0.400000"),
            cost_friction_score=d("0.200000"),
        ),
    )
    first_report = report(observations)
    second_report = report(tuple(reversed(observations)))

    first_payload = research_market_event_spread_shock_watch_payload(first_report)
    second_payload = research_market_event_spread_shock_watch_payload(second_report)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["items"][0]["event_domain"] == "sports"
    assert first_payload["items"][1]["shock_score"] == "0.352308"
    assert first_payload["derived_validation_digest"] == first_report.derived_validation_digest
    assert len(first_report.derived_validation_digest) == 64
    assert research_market_event_spread_shock_watch_digest(first_report) == (
        research_market_event_spread_shock_watch_digest(second_report)
    )
    assert tuple(
        (count.reason_code, count.count)
        for count in first_report.reason_code_counts
        if count.reason_code.startswith("input_")
    ) == (("input_alpha", d("1")), ("input_zeta", d("1")))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert ": 0.5" not in encoded
    _assert_public_payload_has_no_raw_identifiers_or_execution_language(first_payload)


def test_frozen_dataclasses_and_validation_reject_bad_types_flags_and_tampering() -> None:
    shock_report = report((observation("macro"),))

    with pytest.raises(FrozenInstanceError):
        shock_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        shock_report.items[0].shock_score = d("0.500000")  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadObservation(ResearchMarketEventSpreadShockObservation):
            pass

    with pytest.raises(ValueError, match="spread_widening_bps"):
        observation("macro", spread_widening_bps=30)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="depth_fade_ratio"):
        observation("macro", depth_fade_ratio=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation("macro"),), generated_at=_DatetimeSubclass(2026, 7, 8, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        report((observation("macro", observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="event_domain"):
        observation("raw_market_id_123")
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation("macro"), paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(shock_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="shock_score"):
        replace(shock_report.items[0], shock_score=d("0.500000"))
    with pytest.raises(ValueError, match="status"):
        replace(shock_report.items[0], status="blocked")


def test_public_surface_has_no_raw_identifier_or_execution_vocabulary() -> None:
    forbidden_terms = (
        "raw_market",
        "market_id",
        "condition_id",
        "source_id",
        "raw_source",
        "wallet",
        "auth",
        "order",
        "trade",
        "recommend",
        "sizing",
        "database",
        "network",
        "live_execution",
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in forbidden_terms)

    for cls in (
        ResearchMarketEventSpreadShockObservation,
        ResearchMarketEventSpreadShockWatchConfig,
        ResearchMarketEventSpreadShockWatchItem,
        ResearchMarketEventSpreadShockWatchReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in forbidden_terms)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)

    with pytest.raises(ValueError, match="unsafe"):
        research_market_event_spread_shock_watch_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "items": [{"raw_market_id": "abc"}],
            },
        )
    with pytest.raises(ValueError, match="unsafe"):
        research_market_event_spread_shock_watch_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "items": [{"public_note": "wallet=abc"}],
            },
        )
    with pytest.raises(ValueError, match="readonly"):
        research_market_event_spread_shock_watch_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": False,
            },
        )


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = [value]
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    return tuple(values)


def _assert_public_payload_has_no_raw_identifiers_or_execution_language(
    value: object,
) -> None:
    forbidden_terms = (
        "raw_market",
        "market_id",
        "condition_id",
        "source_id",
        "raw_source",
        "wallet",
        "auth",
        "order",
        "trade",
        "recommend",
        "sizing",
        "database",
        "network",
        "live_execution",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            assert not any(term in lowered for term in forbidden_terms)
            _assert_public_payload_has_no_raw_identifiers_or_execution_language(item)
    elif isinstance(value, list):
        for item in value:
            _assert_public_payload_has_no_raw_identifiers_or_execution_language(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert not any(term in lowered for term in forbidden_terms)
