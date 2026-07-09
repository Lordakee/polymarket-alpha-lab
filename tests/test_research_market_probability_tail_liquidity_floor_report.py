from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_market_probability_tail_liquidity_floor_report"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "tail_probability_watch_distance": d("0.100000"),
        "tail_probability_block_distance": d("0.030000"),
        "pass_liquidity_floor_units": d("100.000000"),
        "watch_liquidity_floor_units": d("50.000000"),
        "block_liquidity_floor_units": d("20.000000"),
        "spread_pressure_watch_threshold": d("0.350000"),
        "spread_pressure_block_threshold": d("0.700000"),
        "tail_pressure_weight": d("0.400000"),
        "liquidity_pressure_weight": d("0.400000"),
        "spread_pressure_weight": d("0.200000"),
        "pressure_watch_threshold": d("0.400000"),
        "pressure_block_threshold": d("0.700000"),
    }
    values.update(overrides)
    return module.ResearchMarketProbabilityTailLiquidityFloorConfig(**values)


def observation(
    private_reference: str = "private-ref",
    *,
    probability: object = d("0.400000"),
    liquidity_depth_units: object = d("150.000000"),
    spread_pressure_score: object = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketProbabilityTailLiquidityFloorObservation(
        private_reference=private_reference,
        probability=probability,
        liquidity_depth_units=liquidity_depth_units,
        spread_pressure_score=spread_pressure_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: Any, cfg: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_research_market_probability_tail_liquidity_floor_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_numeric_objects(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_numeric_objects(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_numeric_objects(item)
        return
    assert type(value) not in (Decimal, float, int)


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    core = dict(payload)
    core.pop("derived_validation_digest", None)
    payload["derived_validation_digest"] = hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    return payload


def unsafe_terms() -> tuple[str, ...]:
    return (
        "raw-candidate-alpha",
        "market_id=hidden",
        "market_slug=secret",
        "question=private",
        "https://example.com/private",
        "source_text=verbatim",
        "dsn=postgres",
        "table_name=private_table",
        "token=secret",
        "wallet=private",
        "order=private",
        "trade=private",
    )


def test_report_classifies_tail_liquidity_floor_pressure_deterministically() -> None:
    blocked = observation(
        "raw-candidate-alpha market_id=hidden market_slug=secret "
        "question=private https://example.com/private source_text=verbatim "
        "dsn=postgres table_name=private_table token=secret wallet=private "
        "order=private trade=private",
        probability=d("0.010000"),
        liquidity_depth_units=d("10.000000"),
        spread_pressure_score=d("0.800000"),
    )
    watched = observation(
        "private-watch-ref",
        probability=d("0.060000"),
        liquidity_depth_units=d("60.000000"),
        spread_pressure_score=d("0.200000"),
    )
    passed = observation(
        "private-pass-ref",
        probability=d("0.400000"),
        liquidity_depth_units=d("150.000000"),
        spread_pressure_score=d("0.100000"),
    )

    forward = build_report(
        watched,
        passed,
        blocked,
        generated_at=datetime(2026, 7, 9, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    reverse = build_report(blocked, passed, watched)

    assert is_dataclass(forward)
    assert type(forward) is api().ResearchMarketProbabilityTailLiquidityFloorReport
    assert forward.generated_at == GENERATED_AT
    assert forward.payload == reverse.payload
    assert forward.derived_validation_digest == reverse.derived_validation_digest
    assert forward.status == "block"
    assert forward.observation_count == d("3.000000")
    assert forward.pass_count == d("1.000000")
    assert forward.watch_count == d("1.000000")
    assert forward.block_count == d("1.000000")
    assert forward.tail_observation_count == d("2.000000")
    assert forward.floor_breach_count == d("2.000000")
    assert forward.average_tail_distance == d("0.156667")
    assert forward.minimum_tail_distance == d("0.010000")
    assert forward.average_liquidity_depth_units == d("73.333333")
    assert forward.minimum_liquidity_depth_units == d("10.000000")
    assert forward.maximum_floor_gap_ratio == d("0.900000")
    assert forward.reason_codes == (
        "tail_liquidity_floor_block_present",
        "tail_liquidity_floor_watch_present",
        "tail_liquidity_floor_pass_present",
    )
    assert forward.paper_only is True
    assert forward.report_only is True
    assert forward.readonly is True

    assert tuple(row.status for row in forward.rows) == ("block", "watch", "pass")
    assert tuple(row.rank for row in forward.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    block_row, watch_row, pass_row = forward.rows
    assert block_row.analysis_digest.startswith("sha256:")
    assert block_row.probability == d("0.010000")
    assert block_row.tail_distance == d("0.010000")
    assert block_row.liquidity_floor_gap_units == d("90.000000")
    assert block_row.liquidity_floor_gap_ratio == d("0.900000")
    assert block_row.tail_pressure_score == d("1.000000")
    assert block_row.tail_liquidity_pressure_score == d("0.920000")
    assert block_row.reason_codes == (
        "tail_probability_block",
        "liquidity_floor_block",
        "spread_pressure_block",
        "tail_liquidity_pressure_block",
    )

    assert watch_row.tail_distance == d("0.060000")
    assert watch_row.liquidity_floor_gap_ratio == d("0.400000")
    assert watch_row.tail_pressure_score == d("0.571429")
    assert watch_row.tail_liquidity_pressure_score == d("0.428572")
    assert watch_row.reason_codes == (
        "tail_probability_watch",
        "tail_liquidity_pressure_watch",
    )

    assert pass_row.reason_codes == ("tail_liquidity_floor_pass",)
    assert pass_row.tail_liquidity_pressure_score == d("0.020000")

    payload = api().research_market_probability_tail_liquidity_floor_report_payload(
        forward,
    )
    assert payload["rows"][0]["rank"] == "1.000000"
    assert payload["rows"][0]["tail_liquidity_pressure_score"] == "0.920000"
    assert payload["derived_validation_digest"] == forward.derived_validation_digest
    assert_no_numeric_objects(payload)
    encoded = json.dumps(payload, sort_keys=True)
    for term in unsafe_terms():
        assert term not in encoded
    assert "raw-candidate-alpha" not in encoded
    assert "private-watch-ref" not in encoded
    json.dumps(payload, sort_keys=True)


def test_empty_report_is_pass_readonly_json_ready_and_digest_validated() -> None:
    module = api()
    report = build_report()

    assert report.status == "pass"
    assert report.observation_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.tail_observation_count == d("0.000000")
    assert report.floor_breach_count == d("0.000000")
    assert report.average_tail_distance == d("0.000000")
    assert report.minimum_tail_distance == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("probability_tail_liquidity_floor_empty",)
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    assert module.validate_research_market_probability_tail_liquidity_floor_report_digest(
        report,
    )
    payload = report.payload
    assert payload == module.research_market_probability_tail_liquidity_floor_report_payload(
        report,
    )
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["rows"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_numeric_objects(payload)
    json.dumps(payload, sort_keys=True)


def test_payload_and_digest_validation_reject_tampering_and_unsafe_public_surface() -> None:
    module = api()
    report = build_report(
        observation(
            "private-block-ref",
            probability=d("0.010000"),
            liquidity_depth_units=d("10.000000"),
            spread_pressure_score=d("0.800000"),
        ),
    )
    payload = report.payload

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    tampered_count = dict(payload)
    tampered_count["pass_count"] = "99.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_probability_tail_liquidity_floor_report_payload(
            tampered_count,
        )

    internally_inconsistent = dict(payload)
    internally_inconsistent["pass_count"] = "99.000000"
    resign_payload(internally_inconsistent)
    with pytest.raises(ValueError, match="pass_count"):
        module.research_market_probability_tail_liquidity_floor_report_payload(
            internally_inconsistent,
        )

    downgraded = dict(payload)
    downgraded["readonly"] = False
    resign_payload(downgraded)
    with pytest.raises(ValueError, match="readonly"):
        module.research_market_probability_tail_liquidity_floor_report_payload(
            downgraded,
        )

    unsafe = dict(payload)
    unsafe["market_id"] = "raw-private-id"
    resign_payload(unsafe)
    with pytest.raises(ValueError, match="unsafe"):
        module.research_market_probability_tail_liquidity_floor_report_payload(
            unsafe,
        )

    numeric_public = dict(payload)
    numeric_public["observation_count"] = d("1.000000")
    with pytest.raises(ValueError, match="Decimal-derived strings|numeric"):
        module.research_market_probability_tail_liquidity_floor_report_payload(
            numeric_public,
        )


def test_frozen_decimal_only_datetime_and_hard_flag_guards() -> None:
    module = api()
    built = build_report(observation("private-ref"))

    for value in (config(), observation("private-ref"), built.rows[0], built):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="probability"):
        observation("private-ref", probability=_DecimalSubclass("0.400000"))
    with pytest.raises(ValueError, match="liquidity_depth_units"):
        observation("private-ref", liquidity_depth_units=1)
    with pytest.raises(ValueError, match="spread_pressure_score"):
        observation("private-ref", spread_pressure_score=0.1)
    with pytest.raises(ValueError, match="paper_only"):
        observation("private-ref", paper_only=False)
    with pytest.raises(ValueError, match="generated_at"):
        build_report(observation("private-ref"), generated_at=datetime(2026, 7, 9))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            observation("private-ref"),
            generated_at=_DatetimeSubclass(2026, 7, 9, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="ready")
    with pytest.raises(ValueError, match="weights"):
        config(spread_pressure_weight=d("0.300000"))
    with pytest.raises(ValueError, match="threshold|distance"):
        config(tail_probability_block_distance=d("0.200000"))

    for value in (config(), observation("private-ref"), built.rows[0], built):
        for field in fields(value):
            item = getattr(value, field.name)
            if isinstance(item, Decimal):
                assert type(item) is Decimal

    with pytest.raises(TypeError):
        class Child(module.ResearchMarketProbabilityTailLiquidityFloorReport):
            pass


def test_static_module_surface_is_report_only_and_public_payload_fields_are_identifier_free() -> None:
    module = api()
    source = Path(module.__file__).read_text(encoding="utf-8").lower()
    forbidden_imports = (
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
    )
    for forbidden in forbidden_imports:
        assert forbidden not in source
    assert "def buy" not in source
    assert "def sell" not in source
    assert "place_order" not in source
    assert "execute_trade" not in source

    payload = build_report(
        observation(
            "market_id=hidden market_slug=private question=secret source_url=https://example.com token=secret",
            probability=d("0.020000"),
            liquidity_depth_units=d("5.000000"),
            spread_pressure_score=d("0.900000"),
        ),
    ).payload
    public_keys = json.dumps(sorted(payload.keys()) + sorted(payload["rows"][0].keys()))
    for forbidden in (
        "candidate_id",
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
    ):
        assert forbidden not in public_keys
