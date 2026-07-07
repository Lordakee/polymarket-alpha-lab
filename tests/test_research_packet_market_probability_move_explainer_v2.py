from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


api = importlib.import_module(
    "polymarket_alpha_lab.research_packet_market_probability_move_explainer_v2",
)

GENERATED_AT = datetime(2026, 1, 3, 12, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    values: dict[str, object] = {
        "config_version": (
            api.DEFAULT_RESEARCH_PACKET_MARKET_PROBABILITY_MOVE_EXPLAINER_V2_CONFIG_VERSION
        ),
        "fresh_source_hours": d("2.000000"),
        "stale_source_hours": d("12.000000"),
        "thin_liquidity_depth_usd": d("100.000000"),
        "deep_liquidity_depth_usd": d("1000.000000"),
        "large_move_threshold": d("0.100000"),
        "medium_move_threshold": d("0.050000"),
    }
    values.update(overrides)
    return api.ResearchPacketMarketProbabilityMoveExplainerV2Config(**values)


def move(
    market_id: str = "market-alpha",
    *,
    market_title: str = "Will the candidate win?",
    before_price: object = d("0.250000"),
    after_price: object = d("0.310000"),
    latest_source_age_hours: object = d("10.000000"),
    source_events: tuple[str, ...] = ("proxy-report",),
    official_confirmation_status: str = "unconfirmed",
    contradiction_status: str = "material",
    liquidity_depth_usd: object = d("80.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    return api.ResearchPacketMarketProbabilityMoveExplainerV2Input(
        market_id=market_id,
        market_title=market_title,
        before_price=before_price,
        after_price=after_price,
        latest_source_age_hours=latest_source_age_hours,
        source_events=source_events,
        official_confirmation_status=official_confirmation_status,
        contradiction_status=contradiction_status,
        liquidity_depth_usd=liquidity_depth_usd,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*rows: object, generated_at: datetime = GENERATED_AT, **config_overrides: object):
    return api.build_research_packet_market_probability_move_explainer_v2(
        rows,
        config=config(**config_overrides),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError("float value found")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    core = {
        key: item
        for key, item in payload.items()
        if key != "derived_validation_digest"
    }
    payload["derived_validation_digest"] = hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    return payload


def test_builds_deterministic_probability_move_explainer_rows_and_digest() -> None:
    alpha = move()
    beta = move(
        "market-beta",
        market_title="Will the bill pass?",
        before_price=d("0.620000"),
        after_price=d("0.480000"),
        latest_source_age_hours=d("1.000000"),
        source_events=("pollster-correction", "official-campaign-statement"),
        official_confirmation_status="confirmed",
        contradiction_status="none",
        liquidity_depth_usd=d("1500.000000"),
    )

    built = report(alpha, beta)
    replayed = report(
        move(
            "market-beta",
            market_title="Will the bill pass?",
            before_price=d("0.620000"),
            after_price=d("0.480000"),
            latest_source_age_hours=d("1.000000"),
            source_events=("official-campaign-statement", "pollster-correction"),
            official_confirmation_status="confirmed",
            contradiction_status="none",
            liquidity_depth_usd=d("1500.000000"),
        ),
        alpha,
    )

    assert built.payload == replayed.payload
    assert built.derived_validation_digest == replayed.derived_validation_digest
    assert built.market_count == d("2.000000")
    assert built.confirmed_count == d("1.000000")
    assert built.contradicted_count == d("1.000000")
    assert built.stale_count == d("0.000000")
    assert built.largest_move_magnitude == d("0.140000")
    assert tuple(row.market_id for row in built.rows) == ("market-beta", "market-alpha")

    first = built.rows[0]
    assert first.rank == d("1.000000")
    assert first.before_price == d("0.620000")
    assert first.after_price == d("0.480000")
    assert first.move_magnitude == d("0.140000")
    assert first.move_direction == "down"
    assert first.move_band == "large"
    assert first.source_events == ("official-campaign-statement", "pollster-correction")
    assert first.source_event_count == d("2.000000")
    assert first.official_confirmation_status == "confirmed"
    assert first.contradiction_status == "none"
    assert first.liquidity_context == "deep"
    assert first.freshness_status == "fresh"
    assert first.reason_codes == (
        "move_large",
        "move_down",
        "sources_multiple",
        "official_confirmed",
        "contradiction_none",
        "liquidity_deep",
        "freshness_fresh",
    )

    second = built.rows[1]
    assert second.move_direction == "up"
    assert second.move_band == "medium"
    assert second.reason_codes == (
        "move_medium",
        "move_up",
        "sources_single",
        "official_unconfirmed",
        "contradiction_material",
        "liquidity_thin",
        "freshness_watch",
    )

    payload = built.payload
    assert payload == api.research_packet_market_probability_move_explainer_v2_payload(built)
    assert payload["generated_at"] == "2026-01-03T12:30:00Z"
    assert payload["rows"][0]["before_price"] == "0.620000"
    assert payload["rows"][0]["source_event_count"] == "2"
    assert payload["rows"][0]["reason_codes"] == list(first.reason_codes)
    assert (
        api.derive_research_packet_market_probability_move_explainer_v2_digest(payload)
        == built.derived_validation_digest
    )
    assert_no_float_values(payload)
    json.dumps(payload, sort_keys=True)


def test_frozen_decimal_only_inputs_and_hard_flags_are_enforced() -> None:
    built = report(move())

    for value in (config(), move(), built.rows[0], built):
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="before_price"):
        move(before_price=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="after_price"):
        move(after_price=0.31)
    with pytest.raises(ValueError, match="latest_source_age_hours"):
        move(latest_source_age_hours=1)
    with pytest.raises(ValueError, match="liquidity_depth_usd"):
        move(liquidity_depth_usd=d("-1.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        move(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(built.rows[0], readonly=False)
    with pytest.raises(ValueError, match="threshold"):
        config(medium_move_threshold=d("0.120000"))


def test_validation_rejects_unsafe_payloads_and_digest_tampering() -> None:
    built = report(move())
    unsafe_word = "wal" + "let"

    with pytest.raises(ValueError, match="unsafe"):
        move(market_title=f"Mentions {unsafe_word}")
    with pytest.raises(ValueError, match="source_events"):
        move(source_events=())
    with pytest.raises(ValueError, match="official_confirmation_status"):
        move(official_confirmation_status="maybe")
    with pytest.raises(ValueError, match="contradiction_status"):
        move(contradiction_status="mixed")

    tampered = built.payload
    tampered["rows"][0]["after_price"] = "0.420000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.research_packet_market_probability_move_explainer_v2_payload(tampered)

    downgraded = built.payload
    downgraded["rows"][0]["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        api.research_packet_market_probability_move_explainer_v2_payload(downgraded)

    with pytest.raises(ValueError, match="float"):
        api.research_packet_market_probability_move_explainer_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "rows": [],
                "derived_validation_digest": built.derived_validation_digest,
                "largest_move_magnitude": 0.1,
            },
        )


def test_payload_validation_rejects_resigned_schema_and_consistency_drift() -> None:
    built = report(move())

    missing_report_field = built.payload
    del missing_report_field["generated_at"]
    resign_payload(missing_report_field)
    with pytest.raises(ValueError, match="payload field is missing"):
        api.research_packet_market_probability_move_explainer_v2_payload(
            missing_report_field,
        )
    with pytest.raises(ValueError, match="payload field is missing"):
        api.derive_research_packet_market_probability_move_explainer_v2_digest(
            missing_report_field,
        )

    count_drift = built.payload
    count_drift["market_count"] = "99"
    resign_payload(count_drift)
    with pytest.raises(ValueError, match="market_count"):
        api.research_packet_market_probability_move_explainer_v2_payload(count_drift)

    row_drift = built.payload
    row_drift["rows"][0]["source_event_count"] = "9"
    resign_payload(row_drift)
    with pytest.raises(ValueError, match="source_event_count"):
        api.research_packet_market_probability_move_explainer_v2_payload(row_drift)


def test_static_module_surface_has_no_side_effect_imports() -> None:
    module_source = Path(api.__file__).read_text(encoding="utf-8").lower()

    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "web3",
        "ccxt",
        "subprocess",
        "pathlib",
        "open(",
    ):
        assert forbidden not in module_source
    for forbidden in (
        "au" + "th",
        "wal" + "let",
        "or" + "der",
        "li" + "ve",
        "tra" + "de",
        "net" + "work",
        "data" + "base",
    ):
        assert forbidden not in module_source

    assert api.__all__ == (
        "DEFAULT_RESEARCH_PACKET_MARKET_PROBABILITY_MOVE_EXPLAINER_V2_CONFIG_VERSION",
        "ResearchPacketMarketProbabilityMoveExplainerV2Config",
        "ResearchPacketMarketProbabilityMoveExplainerV2Input",
        "ResearchPacketMarketProbabilityMoveExplainerV2Report",
        "ResearchPacketMarketProbabilityMoveExplainerV2Row",
        "build_research_packet_market_probability_move_explainer_v2",
        "derive_research_packet_market_probability_move_explainer_v2_digest",
        "research_packet_market_probability_move_explainer_v2_payload",
    )
