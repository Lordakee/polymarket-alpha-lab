from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_orderbook_reliability_drift_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def sample(
    sample_ref: str = "private-book-pass",
    *,
    observed_at: datetime | None = None,
    depth_decay_ratio: Decimal = d("0.100000"),
    spread_instability_ratio: Decimal = d("0.020000"),
    stale_book_age_seconds: Decimal = d("60.000000"),
    imbalance_volatility_ratio: Decimal = d("0.050000"),
    fee_drag_ratio: Decimal = d("0.010000"),
    settlement_friction_ratio: Decimal = d("0.050000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketOrderbookReliabilityDriftSample(
        sample_ref=sample_ref,
        observed_at=observed_at or GENERATED_AT - timedelta(seconds=60),
        depth_decay_ratio=depth_decay_ratio,
        spread_instability_ratio=spread_instability_ratio,
        stale_book_age_seconds=stale_book_age_seconds,
        imbalance_volatility_ratio=imbalance_volatility_ratio,
        fee_drag_ratio=fee_drag_ratio,
        settlement_friction_ratio=settlement_friction_ratio,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_ORDERBOOK_RELIABILITY_DRIFT_REPORT_CONFIG_VERSION
        ),
    }
    values.update(overrides)
    return module.ResearchMarketOrderbookReliabilityDriftConfig(**values)


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_orderbook_reliability_drift_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_empty_input_blocks_report_only_book_reliability_drift_review() -> None:
    module = api()
    drift_report = report()

    assert module.ORDERBOOK_RELIABILITY_DRIFT_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "ORDERBOOK_RELIABILITY_DRIFT_STATUSES",
        "DEFAULT_RESEARCH_MARKET_ORDERBOOK_RELIABILITY_DRIFT_REPORT_CONFIG_VERSION",
        "ResearchMarketOrderbookReliabilityDriftConfig",
        "ResearchMarketOrderbookReliabilityDriftReasonCodeCount",
        "ResearchMarketOrderbookReliabilityDriftReport",
        "ResearchMarketOrderbookReliabilityDriftRow",
        "ResearchMarketOrderbookReliabilityDriftSample",
        "build_research_market_orderbook_reliability_drift_report",
        "research_market_orderbook_reliability_drift_report_digest",
        "research_market_orderbook_reliability_drift_report_payload",
    )
    assert type(drift_report) is module.ResearchMarketOrderbookReliabilityDriftReport
    assert is_dataclass(drift_report)
    assert drift_report.__dataclass_params__.frozen
    assert drift_report.generated_at == GENERATED_AT
    assert drift_report.config_version == "research-book-reliability-drift-report-v0"
    assert drift_report.input_count == ZERO
    assert drift_report.pass_count == ZERO
    assert drift_report.watch_count == ZERO
    assert drift_report.block_count == ZERO
    assert drift_report.depth_decay_count == ZERO
    assert drift_report.spread_instability_count == ZERO
    assert drift_report.stale_book_count == ZERO
    assert drift_report.imbalance_volatility_count == ZERO
    assert drift_report.fee_drag_count == ZERO
    assert drift_report.settlement_friction_count == ZERO
    assert drift_report.average_reliability_score is None
    assert drift_report.max_depth_decay_ratio == ZERO
    assert drift_report.max_spread_instability_ratio == ZERO
    assert drift_report.max_stale_book_age_seconds == ZERO
    assert drift_report.max_imbalance_volatility_ratio == ZERO
    assert drift_report.max_fee_drag_ratio == ZERO
    assert drift_report.max_settlement_friction_ratio == ZERO
    assert drift_report.status == "block"
    assert drift_report.reason_codes == ("no_book_reliability_samples",)
    assert drift_report.reason_code_counts == (
        module.ResearchMarketOrderbookReliabilityDriftReasonCodeCount(
            reason_code="no_book_reliability_samples",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert drift_report.rows == ()
    assert drift_report.paper_only is True
    assert drift_report.report_only is True
    assert drift_report.readonly is True


def test_scores_pass_watch_and_block_reliability_drift_samples() -> None:
    drift_report = report(
        sample(
            "private-watch",
            depth_decay_ratio=d("0.300000"),
            spread_instability_ratio=d("0.120000"),
            stale_book_age_seconds=d("300.000000"),
            imbalance_volatility_ratio=d("0.220000"),
            fee_drag_ratio=d("0.030000"),
            settlement_friction_ratio=d("0.180000"),
        ),
        sample(
            "private-block",
            observed_at=GENERATED_AT - timedelta(seconds=1200),
            depth_decay_ratio=d("0.800000"),
            spread_instability_ratio=d("0.400000"),
            stale_book_age_seconds=d("1200.000000"),
            imbalance_volatility_ratio=d("0.600000"),
            fee_drag_ratio=d("0.080000"),
            settlement_friction_ratio=d("0.500000"),
            reason_codes=("manual_drift_review",),
        ),
        sample("private-pass"),
    )

    assert drift_report.status == "block"
    assert drift_report.input_count == d("3.000000")
    assert drift_report.pass_count == d("1.000000")
    assert drift_report.watch_count == d("1.000000")
    assert drift_report.block_count == d("1.000000")
    assert drift_report.depth_decay_count == d("2.000000")
    assert drift_report.spread_instability_count == d("2.000000")
    assert drift_report.stale_book_count == d("2.000000")
    assert drift_report.imbalance_volatility_count == d("2.000000")
    assert drift_report.fee_drag_count == d("2.000000")
    assert drift_report.settlement_friction_count == d("2.000000")
    assert drift_report.average_reliability_score == d("0.420106")
    assert drift_report.max_depth_decay_ratio == d("0.800000")
    assert drift_report.max_spread_instability_ratio == d("0.400000")
    assert drift_report.max_stale_book_age_seconds == d("1200.000000")
    assert drift_report.max_imbalance_volatility_ratio == d("0.600000")
    assert drift_report.max_fee_drag_ratio == d("0.080000")
    assert drift_report.max_settlement_friction_ratio == d("0.500000")

    block_row, pass_row, watch_row = drift_report.rows
    assert tuple(row.row_ref for row in drift_report.rows) == (
        "book_reliability_group_001",
        "book_reliability_group_002",
        "book_reliability_group_003",
    )
    assert tuple(row.status for row in drift_report.rows) == ("block", "pass", "watch")
    assert block_row.reliability_score == ZERO
    assert block_row.drift_pressure == d("1.000000")
    assert block_row.reason_codes == (
        "depth_decay_block",
        "spread_instability_block",
        "stale_book_age_block",
        "imbalance_volatility_block",
        "fee_drag_block",
        "settlement_friction_block",
        "input_manual_drift_review",
        "book_reliability_drift_block",
    )
    assert pass_row.depth_decay_score == d("0.800000")
    assert pass_row.spread_instability_score == d("0.900000")
    assert pass_row.stale_book_score == d("0.900000")
    assert pass_row.imbalance_volatility_score == d("0.857143")
    assert pass_row.fee_drag_score == d("0.800000")
    assert pass_row.settlement_friction_score == d("0.833333")
    assert pass_row.reliability_score == d("0.848413")
    assert pass_row.drift_pressure == d("0.151587")
    assert pass_row.reason_codes == (
        "depth_decay_pass",
        "spread_instability_pass",
        "stale_book_age_pass",
        "imbalance_volatility_pass",
        "fee_drag_pass",
        "settlement_friction_pass",
        "book_reliability_drift_pass",
    )
    assert watch_row.reliability_score == d("0.411905")
    assert watch_row.drift_pressure == d("0.588095")
    assert "book_reliability_drift_watch" in watch_row.reason_codes


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    module = api()
    first = report(
        sample("zzz-https://example.invalid/raw_candidate/market_id/token"),
        sample(
            "aaa-postgres://dsn/table/wallet/order/trade/live",
            fee_drag_ratio=d("0.030000"),
            reason_codes=("manual_drift_review",),
        ),
    )
    second = report(
        sample(
            "aaa-postgres://dsn/table/wallet/order/trade/live",
            fee_drag_ratio=d("0.030000"),
            reason_codes=("manual_drift_review",),
        ),
        sample("zzz-https://example.invalid/raw_candidate/market_id/token"),
    )

    first_payload = module.research_market_orderbook_reliability_drift_report_payload(first)
    second_payload = module.research_market_orderbook_reliability_drift_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_market_orderbook_reliability_drift_report_digest(first) == (
        first.derived_validation_digest
    )
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert len(first.derived_validation_digest) == 64
    int(first.derived_validation_digest, 16)
    assert first_payload["rows"][0]["row_ref"] == "book_reliability_group_001"
    assert first_payload["rows"][0]["fee_drag_ratio"] == "0.030000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert ": 0." not in encoded
    assert not any(
        raw_fragment in encoded.lower()
        for raw_fragment in (
            "https",
            "raw_candidate",
            "market_id",
            "token",
            "postgres",
            "dsn",
            "table",
            "wallet",
            "order",
            "trade",
            "live",
        )
    )
    assert not any(
        _has_forbidden_public_surface_key(key)
        for key in _walk_payload_keys(first_payload)
    )

    tampered = report(sample())
    object.__setattr__(tampered, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_orderbook_reliability_drift_report_payload(tampered)


def test_validation_rejects_bad_types_flags_statuses_and_runtime_surfaces() -> None:
    module = api()
    drift_report = report(sample())

    for value in (config(), sample(), drift_report, *drift_report.rows, *drift_report.reason_code_counts):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        drift_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        drift_report.rows[0].reliability_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="depth_decay_ratio"):
        sample(depth_decay_ratio=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fee_drag_ratio"):
        sample(fee_drag_ratio=DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="observed_at"):
        sample(observed_at=datetime(2026, 7, 8, 11, 59))
    with pytest.raises(ValueError, match="generated_at"):
        report(sample(), generated_at=DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        report(sample(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="reason_codes"):
        sample(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="unsafe public"):
        sample(reason_codes=("market_id",))
    with pytest.raises(ValueError, match="paper_only"):
        sample(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(drift_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(drift_report, derived_validation_digest="0" * 64)
    pressure_report = report(sample("private-pressure", depth_decay_ratio=d("0.300000")))
    with pytest.raises(ValueError, match="depth_decay_count must match rows"):
        replace(pressure_report, depth_decay_count=ZERO)
    with pytest.raises(ValueError, match="max_depth_decay_ratio must match rows"):
        replace(pressure_report, max_depth_decay_ratio=ZERO)
    with pytest.raises(ValueError, match="reason_codes must match rows"):
        replace(pressure_report, reason_codes=("book_reliability_drift_pass",))
    with pytest.raises(ValueError, match="reason_code_counts must match rows"):
        replace(pressure_report, reason_code_counts=())
    tampered_decimal_report = report(sample())
    object.__setattr__(
        tampered_decimal_report,
        "average_reliability_score",
        DecimalSubclass("0.848413"),
    )
    with pytest.raises(ValueError, match="payload Decimal value"):
        module.research_market_orderbook_reliability_drift_report_digest(
            tampered_decimal_report,
        )
    tampered_flag_report = report(sample())
    object.__setattr__(tampered_flag_report.rows[0], "readonly", False)
    object.__setattr__(
        tampered_flag_report,
        "derived_validation_digest",
        module._derived_report_digest(tampered_flag_report),
    )
    with pytest.raises(ValueError, match="readonly must be True"):
        module.research_market_orderbook_reliability_drift_report_payload(
            tampered_flag_report,
        )

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_orderbook_reliability_drift_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "sqlite",
        "postgres",
        "psycopg",
        "private_key",
        "auth",
        "place_order",
        "cancel_order",
        "order_size",
        "live_trading",
        "trade_recommendation",
        "sizing",
        "buy_",
        "sell_",
        "connect(",
        "open(",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)


def _walk_payload_keys(value: object) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(str(key))
            keys.extend(_walk_payload_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_payload_keys(item))
    return tuple(keys)


def _has_forbidden_public_surface_key(key: str) -> bool:
    normalized = key.lower()
    forbidden_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "size",
        "sizing",
        "recommendation",
    )
    return any(fragment in normalized for fragment in forbidden_fragments)
