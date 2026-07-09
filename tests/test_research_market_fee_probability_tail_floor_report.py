from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from importlib import import_module
import json
from types import ModuleType

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_market_fee_probability_tail_floor_report"
)
GENERATED_AT = datetime(2026, 7, 9, 19, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 18, 45, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


class DateTimeSubclass(datetime):
    pass


def api() -> ModuleType:
    try:
        return import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"{MODULE_NAME} must exist")
        raise


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> object:
    values: dict[str, object] = {
        "watch_tail_distance_floor": d("0.050000"),
        "block_tail_distance_floor": d("0.010000"),
        "watch_fee_adjusted_tail_floor": d("0.025000"),
        "block_fee_adjusted_tail_floor": d("0.005000"),
        "watch_fee_probability_drag_rate": d("0.020000"),
        "block_fee_probability_drag_rate": d("0.050000"),
    }
    values.update(overrides)
    return api().ResearchMarketFeeProbabilityTailFloorConfig(**values)


def sample(reference: str, **overrides: object) -> object:
    values: dict[str, object] = {
        "private_research_reference": reference,
        "observed_at": OBSERVED_AT,
        "market_probability": d("0.500000"),
        "taker_fee_rate": d("0.005000"),
        "quoted_spread_rate": d("0.004000"),
        "slippage_buffer_rate": d("0.001000"),
    }
    values.update(overrides)
    return api().ResearchMarketFeeProbabilityTailFloorInput(**values)


def build_report(*inputs: object, cfg: object | None = None) -> object:
    return api().build_research_market_fee_probability_tail_floor_report(
        inputs,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def walk_json(value: object):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_json(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            yield from walk_json(item)
        return
    yield value


def self_consistent_payload_digest(payload: dict[str, object]) -> str:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def test_tail_floor_report_scores_sorts_and_summarizes_pass_watch_block() -> None:
    module = api()
    passed = sample("tail-floor-pass")
    watched = sample(
        "tail-floor-watch",
        market_probability=d("0.960000"),
        taker_fee_rate=d("0.006000"),
        quoted_spread_rate=d("0.008000"),
        slippage_buffer_rate=d("0.005000"),
    )
    blocked = sample(
        "tail-floor-block",
        market_probability=d("0.995000"),
        taker_fee_rate=d("0.030000"),
        quoted_spread_rate=d("0.040000"),
        slippage_buffer_rate=d("0.010000"),
    )

    report = build_report(passed, watched, blocked)
    repeated_report = build_report(blocked, passed, watched)

    assert type(report) is module.ResearchMarketFeeProbabilityTailFloorReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_probability_tail_distance == d("0.181667")
    assert report.average_fee_adjusted_tail_floor == d("0.172333")
    assert report.min_fee_adjusted_tail_floor == d("0.000000")
    assert report.max_fee_probability_drag_rate == d("0.060000")
    assert report.derived_validation_digest == repeated_report.derived_validation_digest

    block_row, watch_row, pass_row = report.rows
    assert [row.status for row in report.rows] == ["block", "watch", "pass"]
    assert [row.rank for row in report.rows] == [
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    ]

    assert block_row.probability_tail_distance == d("0.005000")
    assert block_row.fee_probability_drag_rate == d("0.060000")
    assert block_row.fee_adjusted_tail_floor == d("0.000000")
    assert block_row.tail_floor_gap_rate == d("0.045000")
    assert block_row.reason_codes == (
        "fee_probability_tail_floor_block",
        "probability_tail_floor_block",
        "fee_adjusted_tail_floor_block",
        "fee_probability_drag_block",
        "fee_drag_applied",
        "spread_drag_applied",
        "slippage_buffer_applied",
    )

    assert watch_row.probability_tail_distance == d("0.040000")
    assert watch_row.fee_probability_drag_rate == d("0.015000")
    assert watch_row.fee_adjusted_tail_floor == d("0.025000")
    assert watch_row.tail_floor_gap_rate == d("0.010000")
    assert watch_row.reason_codes == (
        "fee_probability_tail_floor_watch",
        "probability_tail_floor_watch",
        "fee_adjusted_tail_floor_watch",
        "fee_drag_applied",
        "spread_drag_applied",
        "slippage_buffer_applied",
    )

    assert pass_row.probability_tail_distance == d("0.500000")
    assert pass_row.fee_probability_drag_rate == d("0.008000")
    assert pass_row.fee_adjusted_tail_floor == d("0.492000")
    assert pass_row.tail_floor_gap_rate == d("0.000000")
    assert pass_row.reason_codes == (
        "fee_probability_tail_floor_pass",
        "fee_drag_applied",
        "spread_drag_applied",
        "slippage_buffer_applied",
    )
    assert len({row.signal_digest for row in report.rows}) == 3
    assert all(len(row.derived_validation_digest) == 64 for row in report.rows)


def test_public_payload_is_deterministic_sha256_bound_immutable_and_safe() -> None:
    module = api()
    raw_reference = (
        "raw_candidate=alpha candidate_id=cid market_id=mid market_slug=slug "
        "question text source_url=https://example.invalid/a source_text dsn=postgres "
        "table_name=markets token=secret wallet order trade"
    )
    report = build_report(
        sample(
            raw_reference,
            market_probability=d("0.995000"),
            taker_fee_rate=d("0.030000"),
            quoted_spread_rate=d("0.040000"),
            slippage_buffer_rate=d("0.010000"),
        ),
    )
    same_instant_report = build_report(
        sample(
            raw_reference,
            observed_at=OBSERVED_AT.astimezone(timezone(timedelta(hours=-4))),
            market_probability=d("0.995000"),
            taker_fee_rate=d("0.030000"),
            quoted_spread_rate=d("0.040000"),
            slippage_buffer_rate=d("0.010000"),
        ),
    )

    payload = module.research_market_fee_probability_tail_floor_report_payload(report)
    rendered_payload = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert report.derived_validation_digest == same_instant_report.derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["derived_validation_digest"] == (
        module.research_market_fee_probability_tail_floor_report_digest(report)
    )
    assert len(report.derived_validation_digest) == 64
    assert set(report.derived_validation_digest) <= set("0123456789abcdef")
    assert payload["generated_at"] == "2026-07-09T19:00:00+00:00"
    assert payload["rows"][0]["signal_digest"] == report.rows[0].signal_digest
    assert payload["rows"][0]["fee_adjusted_tail_floor"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) in (int, float) for value in walk_json(payload))

    for forbidden in (
        raw_reference,
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question text",
        "source_url",
        "source_text",
        "https://example.invalid/a",
        "dsn=postgres",
        "table_name",
        "token=secret",
        "wallet",
        "order",
        "trade",
        "private_research_reference",
    ):
        assert forbidden.lower() not in rendered_payload.lower()

    with pytest.raises(TypeError, match="payload is immutable"):
        payload["status"] = "pass"
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["rows"].append({})  # type: ignore[attr-defined]

    tampered = dict(payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_fee_probability_tail_floor_report_payload(tampered)

    unsafe_payload = dict(payload)
    unsafe_payload["market_id"] = "leaked"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_market_fee_probability_tail_floor_report_payload(
            unsafe_payload,
        )

    nested_flag_payload = json.loads(json.dumps(payload, allow_nan=False, sort_keys=True))
    nested_flag_payload["rows"][0]["readonly"] = False
    nested_flag_payload["derived_validation_digest"] = self_consistent_payload_digest(
        nested_flag_payload,
    )
    with pytest.raises(ValueError, match="readonly"):
        module.research_market_fee_probability_tail_floor_report_payload(
            nested_flag_payload,
        )


def test_empty_input_blocks_without_row_leakage() -> None:
    report = build_report()

    assert report.status == "block"
    assert report.input_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_probability_tail_distance is None
    assert report.average_fee_adjusted_tail_floor is None
    assert report.min_fee_adjusted_tail_floor is None
    assert report.max_fee_probability_drag_rate == d("0.000000")
    assert report.reason_codes == ("missing_fee_probability_tail_floor_inputs",)
    assert report.reason_code_counts[0].reason_code == (
        "missing_fee_probability_tail_floor_inputs"
    )
    assert report.rows == ()


def test_frozen_decimal_only_flags_and_validation_contracts() -> None:
    module = api()
    report = build_report(sample("contract-check"))

    for contract in (
        module.ResearchMarketFeeProbabilityTailFloorConfig,
        module.ResearchMarketFeeProbabilityTailFloorInput,
        module.ResearchMarketFeeProbabilityTailFloorReasonCodeCount,
        module.ResearchMarketFeeProbabilityTailFloorReportRow,
        module.ResearchMarketFeeProbabilityTailFloorReport,
    ):
        assert contract.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        assert all(field.type not in (int, float) for field in fields(contract))

    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadConfig(module.ResearchMarketFeeProbabilityTailFloorConfig):
            pass

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="must be a Decimal"):
        sample("decimal-subclass", market_probability=DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="must be a datetime"):
        sample(
            "datetime-subclass",
            observed_at=DateTimeSubclass(2026, 7, 9, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="tail_distance_floor"):
        config(
            watch_tail_distance_floor=d("0.005000"),
            block_tail_distance_floor=d("0.010000"),
        )
    with pytest.raises(ValueError, match="fee_probability_drag_rate"):
        config(
            watch_fee_probability_drag_rate=d("0.060000"),
            block_fee_probability_drag_rate=d("0.050000"),
        )
    with pytest.raises(ValueError, match="signal digests must be unique"):
        build_report(sample("duplicate"), sample("duplicate"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, max_fee_probability_drag_rate=d("0.999999"))


def test_owned_module_has_no_db_network_wallet_or_execution_surface() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__).lower()

    assert "research_market_fee_probability_tail_floor_report_payload" in module.__all__
    assert "research_market_fee_probability_tail_floor_report_digest" in module.__all__
    for banned in (
        "api_key",
        "private_key",
        "wallet",
        "psycopg",
        "supabase",
        "sqlalchemy",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "open(",
        ".read(",
        ".write(",
        "place_order",
        "submit_order",
        "cancel_order",
        "sign_order",
        "live_trading",
    ):
        assert banned not in source
