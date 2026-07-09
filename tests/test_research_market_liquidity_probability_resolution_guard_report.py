from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from importlib import import_module
import json
from types import ModuleType
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_market_liquidity_probability_resolution_guard_report"
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


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(
        unsigned,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def config(**overrides: object) -> object:
    values: dict[str, object] = {
        "watch_min_liquidity_depth_ratio": d("1.000000"),
        "block_min_liquidity_depth_ratio": d("0.400000"),
        "watch_max_quoted_spread_rate": d("0.040000"),
        "block_max_quoted_spread_rate": d("0.100000"),
        "watch_max_probability_dislocation_rate": d("0.080000"),
        "block_max_probability_dislocation_rate": d("0.200000"),
        "watch_max_resolution_rule_ambiguity_rate": d("0.300000"),
        "block_max_resolution_rule_ambiguity_rate": d("0.700000"),
        "watch_min_resolution_evidence_confidence": d("0.700000"),
        "block_min_resolution_evidence_confidence": d("0.400000"),
        "watch_resolution_hours_remaining": d("24.000000"),
        "block_resolution_hours_remaining": d("6.000000"),
    }
    values.update(overrides)
    return api().ResearchMarketLiquidityProbabilityResolutionGuardConfig(**values)


def sample(reference: str, **overrides: object) -> object:
    values: dict[str, object] = {
        "private_research_reference": reference,
        "observed_at": OBSERVED_AT,
        "liquidity_depth_ratio": d("1.500000"),
        "quoted_spread_rate": d("0.010000"),
        "anchor_probability": d("0.500000"),
        "market_probability": d("0.530000"),
        "resolution_hours_remaining": d("72.000000"),
        "resolution_evidence_confidence": d("0.900000"),
        "resolution_rule_ambiguity_rate": d("0.100000"),
    }
    values.update(overrides)
    return api().ResearchMarketLiquidityProbabilityResolutionGuardInput(**values)


def build_report(*inputs: object, cfg: object | None = None) -> object:
    return api().build_research_market_liquidity_probability_resolution_guard_report(
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


def test_guard_scores_sorts_and_summarizes_pass_watch_block() -> None:
    module = api()
    passed = sample(
        "candidate-pass market_id=mid market_slug=slug question=https://example.invalid",
    )
    watched = sample(
        "candidate-watch source_url=https://example.invalid/a source_text",
        liquidity_depth_ratio=d("0.800000"),
        quoted_spread_rate=d("0.050000"),
        market_probability=d("0.610000"),
        resolution_hours_remaining=d("12.000000"),
        resolution_evidence_confidence=d("0.650000"),
        resolution_rule_ambiguity_rate=d("0.350000"),
    )
    blocked = sample(
        "candidate-block dsn=postgres table_name=markets token=secret wallet order trade",
        liquidity_depth_ratio=d("0.300000"),
        quoted_spread_rate=d("0.120000"),
        anchor_probability=d("0.850000"),
        market_probability=d("0.550000"),
        resolution_hours_remaining=d("4.000000"),
        resolution_evidence_confidence=d("0.300000"),
        resolution_rule_ambiguity_rate=d("0.800000"),
    )

    report = build_report(passed, watched, blocked)
    repeated_report = build_report(blocked, passed, watched)

    assert type(report) is module.ResearchMarketLiquidityProbabilityResolutionGuardReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_probability_dislocation_rate == d("0.146667")
    assert report.max_probability_dislocation_rate == d("0.300000")
    assert report.min_liquidity_depth_ratio == d("0.300000")
    assert report.min_resolution_evidence_confidence == d("0.300000")
    assert report.max_resolution_rule_ambiguity_rate == d("0.800000")
    assert report.max_probability_resolution_guard_score == d("0.838889")
    assert report.derived_validation_digest == repeated_report.derived_validation_digest

    block_row, watch_row, pass_row = report.rows
    assert [row.status for row in report.rows] == ["block", "watch", "pass"]
    assert [row.rank for row in report.rows] == [
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    ]

    assert block_row.probability_dislocation_rate == d("0.300000")
    assert block_row.liquidity_stress_score == d("0.850000")
    assert block_row.probability_resolution_guard_score == d("0.838889")
    assert block_row.reason_codes == (
        "liquidity_probability_resolution_guard_block",
        "liquidity_depth_block",
        "spread_block",
        "probability_dislocation_block",
        "resolution_time_block",
        "resolution_evidence_confidence_block",
        "resolution_rule_ambiguity_block",
    )

    assert watch_row.probability_dislocation_rate == d("0.110000")
    assert watch_row.liquidity_stress_score == d("0.350000")
    assert watch_row.probability_resolution_guard_score == d("0.408333")
    assert watch_row.reason_codes == (
        "liquidity_probability_resolution_guard_watch",
        "liquidity_depth_watch",
        "spread_watch",
        "probability_dislocation_watch",
        "resolution_time_watch",
        "resolution_evidence_confidence_watch",
        "resolution_rule_ambiguity_watch",
    )

    assert pass_row.probability_dislocation_rate == d("0.030000")
    assert pass_row.liquidity_stress_score == d("0.050000")
    assert pass_row.probability_resolution_guard_score == d("0.075000")
    assert pass_row.reason_codes == (
        "liquidity_probability_resolution_guard_pass",
    )
    assert len({row.signal_digest for row in report.rows}) == 3
    assert all(len(row.derived_validation_digest) == 64 for row in report.rows)
    assert report.reason_codes == (
        "liquidity_probability_resolution_guard_block",
        "liquidity_probability_resolution_guard_watch",
        "liquidity_probability_resolution_guard_pass",
        "liquidity_depth_block",
        "liquidity_depth_watch",
        "spread_block",
        "spread_watch",
        "probability_dislocation_block",
        "probability_dislocation_watch",
        "resolution_time_block",
        "resolution_time_watch",
        "resolution_evidence_confidence_block",
        "resolution_evidence_confidence_watch",
        "resolution_rule_ambiguity_block",
        "resolution_rule_ambiguity_watch",
    )


def test_public_payload_is_deterministic_sha256_bound_immutable_and_safe() -> None:
    module = api()
    raw_reference = (
        "raw_candidate=alpha candidate_id=cid market_id=mid market_slug=slug "
        "question text source_url=https://example.invalid/a source_text dsn=postgres "
        "table_name=markets token=secret wallet order trade recommendation sizing"
    )
    report = build_report(
        sample(
            raw_reference,
            liquidity_depth_ratio=d("0.300000"),
            quoted_spread_rate=d("0.120000"),
            anchor_probability=d("0.850000"),
            market_probability=d("0.550000"),
            resolution_hours_remaining=d("4.000000"),
            resolution_evidence_confidence=d("0.300000"),
            resolution_rule_ambiguity_rate=d("0.800000"),
        ),
    )
    same_instant_report = build_report(
        sample(
            raw_reference,
            observed_at=OBSERVED_AT.astimezone(timezone(timedelta(hours=-4))),
            liquidity_depth_ratio=d("0.300000"),
            quoted_spread_rate=d("0.120000"),
            anchor_probability=d("0.850000"),
            market_probability=d("0.550000"),
            resolution_hours_remaining=d("4.000000"),
            resolution_evidence_confidence=d("0.300000"),
            resolution_rule_ambiguity_rate=d("0.800000"),
        ),
    )

    payload = module.research_market_liquidity_probability_resolution_guard_report_payload(
        report,
    )
    rendered_payload = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert report.derived_validation_digest == same_instant_report.derived_validation_digest
    assert payload == report.payload
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(report.derived_validation_digest) == 64
    assert set(report.derived_validation_digest) <= set("0123456789abcdef")
    assert payload["generated_at"] == "2026-07-09T19:00:00+00:00"
    assert payload["rows"][0]["signal_digest"] == report.rows[0].signal_digest
    assert payload["rows"][0]["probability_resolution_guard_score"] == "0.838889"
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
        "recommendation",
        "sizing",
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
        module.research_market_liquidity_probability_resolution_guard_report_payload(
            tampered,
        )

    unsafe_payload = dict(payload)
    unsafe_payload["market_id"] = "leaked"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_market_liquidity_probability_resolution_guard_report_payload(
            unsafe_payload,
        )


def test_empty_input_blocks_without_row_leakage() -> None:
    report = build_report()

    assert report.status == "block"
    assert report.input_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_probability_dislocation_rate is None
    assert report.max_probability_dislocation_rate == d("0.000000")
    assert report.min_liquidity_depth_ratio is None
    assert report.min_resolution_evidence_confidence is None
    assert report.max_resolution_rule_ambiguity_rate == d("0.000000")
    assert report.max_probability_resolution_guard_score == d("0.000000")
    assert report.reason_codes == (
        "missing_liquidity_probability_resolution_guard_inputs",
    )
    assert report.reason_code_counts[0].reason_code == (
        "missing_liquidity_probability_resolution_guard_inputs"
    )
    assert report.rows == ()


def test_frozen_decimal_only_flags_and_report_only_contracts() -> None:
    module = api()
    report = build_report(sample("contract-check"))

    for contract in (
        module.ResearchMarketLiquidityProbabilityResolutionGuardConfig,
        module.ResearchMarketLiquidityProbabilityResolutionGuardInput,
        module.ResearchMarketLiquidityProbabilityResolutionGuardReasonCodeCount,
        module.ResearchMarketLiquidityProbabilityResolutionGuardReportRow,
        module.ResearchMarketLiquidityProbabilityResolutionGuardReport,
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

        class BadInput(module.ResearchMarketLiquidityProbabilityResolutionGuardInput):
            pass

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="must be a Decimal"):
        sample("decimal-subclass", anchor_probability=DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="must be a datetime"):
        sample(
            "datetime-subclass",
            observed_at=DateTimeSubclass(2026, 7, 9, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="liquidity_depth_ratio"):
        config(
            watch_min_liquidity_depth_ratio=d("0.300000"),
            block_min_liquidity_depth_ratio=d("0.400000"),
        )
    with pytest.raises(ValueError, match="quoted_spread_rate"):
        config(
            watch_max_quoted_spread_rate=d("0.120000"),
            block_max_quoted_spread_rate=d("0.100000"),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, max_probability_resolution_guard_score=d("0.999999"))

    source = module.__loader__.get_source(module.__name__).lower()
    assert "research_market_liquidity_probability_resolution_guard_report_payload" in (
        module.__all__
    )
    for banned in (
        "api_key",
        "private_key",
        "psycopg",
        "supabase",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "open(",
        ".read(",
        ".write(",
        "place_order",
        "submit_order",
        "cancel_order",
        "sign_order",
        "live_trading",
        "recommendation",
        "sizing",
    ):
        assert banned not in source
