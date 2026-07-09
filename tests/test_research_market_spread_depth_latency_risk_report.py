from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 21, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_spread_depth_latency_risk_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_SPREAD_DEPTH_LATENCY_RISK_REPORT_CONFIG_VERSION
        ),
        "maximum_pass_spread_width_ratio": d("0.030000"),
        "maximum_watch_spread_width_ratio": d("0.080000"),
        "minimum_pass_depth_coverage_ratio": d("0.800000"),
        "minimum_watch_depth_coverage_ratio": d("0.400000"),
        "maximum_pass_latency_haircut_ratio": d("0.020000"),
        "maximum_watch_latency_haircut_ratio": d("0.100000"),
        "maximum_pass_book_age_seconds": d("60.000000"),
        "maximum_watch_book_age_seconds": d("300.000000"),
        "maximum_pass_liquidity_concentration_ratio": d("0.500000"),
        "maximum_watch_liquidity_concentration_ratio": d("0.800000"),
        "spread_width_weight": d("0.250000"),
        "depth_coverage_weight": d("0.250000"),
        "latency_haircut_weight": d("0.200000"),
        "book_age_weight": d("0.150000"),
        "liquidity_concentration_weight": d("0.150000"),
        "maximum_pass_risk_score": d("0.250000"),
        "maximum_watch_risk_score": d("0.550000"),
    }
    values.update(overrides)
    return module.ResearchMarketSpreadDepthLatencyRiskConfig(**values)


def mechanics_input(
    bucket_label: str = "mechanics-pass",
    *,
    observed_at: datetime | None = None,
    spread_width_ratio: Decimal = d("0.010000"),
    depth_coverage_ratio: Decimal = d("0.900000"),
    latency_haircut_ratio: Decimal = d("0.005000"),
    liquidity_concentration_ratio: Decimal = d("0.300000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketSpreadDepthLatencyRiskInput(
        bucket_label=bucket_label,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(seconds=30)
        ),
        spread_width_ratio=spread_width_ratio,
        depth_coverage_ratio=depth_coverage_ratio,
        latency_haircut_ratio=latency_haircut_ratio,
        liquidity_concentration_ratio=liquidity_concentration_ratio,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_spread_depth_latency_risk_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_spread_depth_latency_risk_review() -> None:
    module = api()
    empty = report()

    assert module.SPREAD_DEPTH_LATENCY_RISK_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "SPREAD_DEPTH_LATENCY_RISK_STATUSES",
        "DEFAULT_RESEARCH_MARKET_SPREAD_DEPTH_LATENCY_RISK_REPORT_CONFIG_VERSION",
        "ResearchMarketSpreadDepthLatencyRiskConfig",
        "ResearchMarketSpreadDepthLatencyRiskInput",
        "ResearchMarketSpreadDepthLatencyRiskReasonCodeCount",
        "ResearchMarketSpreadDepthLatencyRiskReport",
        "ResearchMarketSpreadDepthLatencyRiskRow",
        "build_research_market_spread_depth_latency_risk_report",
        "research_market_spread_depth_latency_risk_report_digest",
        "research_market_spread_depth_latency_risk_report_payload",
    )
    assert type(empty) is module.ResearchMarketSpreadDepthLatencyRiskReport
    assert is_dataclass(empty)
    assert empty.generated_at == GENERATED_AT
    assert empty.config_version == "research-market-spread-depth-latency-risk-report-v0"
    assert empty.input_count == ZERO
    assert empty.pass_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.block_count == ZERO
    assert empty.wide_spread_count == ZERO
    assert empty.thin_depth_count == ZERO
    assert empty.latency_haircut_count == ZERO
    assert empty.aged_book_count == ZERO
    assert empty.concentrated_liquidity_count == ZERO
    assert empty.average_risk_score is None
    assert empty.max_spread_width_ratio == ZERO
    assert empty.min_depth_coverage_ratio == ZERO
    assert empty.max_latency_haircut_ratio == ZERO
    assert empty.max_book_age_seconds == ZERO
    assert empty.max_liquidity_concentration_ratio == ZERO
    assert empty.status == "block"
    assert empty.rows == ()
    assert empty.reason_codes == ("no_spread_depth_latency_risk_inputs",)
    assert empty.reason_code_counts == (
        module.ResearchMarketSpreadDepthLatencyRiskReasonCodeCount(
            reason_code="no_spread_depth_latency_risk_inputs",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert len(empty.derived_validation_digest) == 64
    int(empty.derived_validation_digest, 16)
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def test_scores_pass_watch_and_block_market_mechanics_risk_inputs() -> None:
    mechanics = report(
        mechanics_input(
            "alpha-block",
            observed_at=GENERATED_AT - timedelta(seconds=600),
            spread_width_ratio=d("0.120000"),
            depth_coverage_ratio=d("0.250000"),
            latency_haircut_ratio=d("0.150000"),
            liquidity_concentration_ratio=d("0.900000"),
            reason_codes=("manual_microstructure_check",),
        ),
        mechanics_input("beta-pass"),
        mechanics_input(
            "gamma-watch",
            observed_at=GENERATED_AT - timedelta(seconds=180),
            spread_width_ratio=d("0.050000"),
            depth_coverage_ratio=d("0.650000"),
            latency_haircut_ratio=d("0.050000"),
            liquidity_concentration_ratio=d("0.650000"),
        ),
    )

    assert mechanics.input_count == d("3.000000")
    assert mechanics.pass_count == d("1.000000")
    assert mechanics.watch_count == d("1.000000")
    assert mechanics.block_count == d("1.000000")
    assert mechanics.wide_spread_count == d("2.000000")
    assert mechanics.thin_depth_count == d("2.000000")
    assert mechanics.latency_haircut_count == d("2.000000")
    assert mechanics.aged_book_count == d("2.000000")
    assert mechanics.concentrated_liquidity_count == d("2.000000")
    assert mechanics.average_risk_score == d("0.526667")
    assert mechanics.max_spread_width_ratio == d("0.120000")
    assert mechanics.min_depth_coverage_ratio == d("0.250000")
    assert mechanics.max_latency_haircut_ratio == d("0.150000")
    assert mechanics.max_book_age_seconds == d("600.000000")
    assert mechanics.max_liquidity_concentration_ratio == d("0.900000")
    assert mechanics.status == "block"
    assert mechanics.reason_codes == (
        "spread_depth_latency_risk_block",
        "spread_width_block",
        "depth_coverage_block",
        "latency_haircut_block",
        "book_age_block",
        "liquidity_concentration_block",
        "spread_width_watch",
        "depth_coverage_watch",
        "latency_haircut_watch",
        "book_age_watch",
        "liquidity_concentration_watch",
    )

    block_row, pass_row, watch_row = mechanics.rows
    assert tuple(row.public_row_ref for row in mechanics.rows) == (
        "mechanics_risk_group_001",
        "mechanics_risk_group_002",
        "mechanics_risk_group_003",
    )
    assert tuple(row.status for row in mechanics.rows) == ("block", "pass", "watch")
    assert block_row.spread_width_risk_score == d("1.000000")
    assert block_row.depth_coverage_risk_score == d("0.750000")
    assert block_row.latency_haircut_risk_score == d("1.000000")
    assert block_row.book_age_risk_score == d("1.000000")
    assert block_row.liquidity_concentration_risk_score == d("0.900000")
    assert block_row.book_age_seconds == d("600.000000")
    assert block_row.risk_score == d("0.922500")
    assert block_row.reason_codes == (
        "book_age_block",
        "depth_coverage_block",
        "input_manual_microstructure_check",
        "latency_haircut_block",
        "liquidity_concentration_block",
        "spread_depth_latency_risk_block",
        "spread_width_block",
    )
    assert pass_row.risk_score == d("0.126250")
    assert pass_row.status == "pass"
    assert "spread_width_pass" in pass_row.reason_codes
    assert watch_row.risk_score == d("0.531250")
    assert watch_row.status == "watch"
    assert "spread_width_watch" in watch_row.reason_codes
    assert "depth_coverage_watch" in watch_row.reason_codes
    assert "latency_haircut_watch" in watch_row.reason_codes
    assert "book_age_watch" in watch_row.reason_codes
    assert "liquidity_concentration_watch" in watch_row.reason_codes


def test_custom_risk_weights_build_valid_report() -> None:
    weighted = report(
        mechanics_input(
            observed_at=GENERATED_AT - timedelta(seconds=180),
            spread_width_ratio=d("0.040000"),
            depth_coverage_ratio=d("0.700000"),
            latency_haircut_ratio=d("0.030000"),
            liquidity_concentration_ratio=d("0.550000"),
        ),
        cfg=config(
            spread_width_weight=d("0.100000"),
            depth_coverage_weight=d("0.300000"),
            latency_haircut_weight=d("0.250000"),
            book_age_weight=d("0.200000"),
            liquidity_concentration_weight=d("0.150000"),
        ),
    )

    assert weighted.input_count == d("1.000000")
    assert weighted.rows[0].risk_score == d("0.417500")
    assert weighted.average_risk_score == d("0.417500")
    assert weighted.rows[0].status == "watch"
    assert weighted.status == "watch"


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    module = api()
    first = report(
        mechanics_input("zulu-risk", reason_codes=("zeta", "alpha")),
        mechanics_input("alpha-risk"),
    )
    second = report(
        mechanics_input("alpha-risk"),
        mechanics_input("zulu-risk", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_market_spread_depth_latency_risk_report_payload(first)
    second_payload = module.research_market_spread_depth_latency_risk_report_payload(second)
    digest_payload = dict(first_payload)
    digest_payload.pop("derived_validation_digest")
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    public_encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_market_spread_depth_latency_risk_report_digest(first) == digest
    assert first.derived_validation_digest == digest
    assert first_payload["derived_validation_digest"] == digest
    assert first_payload["rows"][0]["public_row_ref"] == "mechanics_risk_group_001"
    assert first_payload["rows"][0]["spread_width_ratio"] == "0.010000"
    assert first_payload["rows"][0]["risk_score"] == "0.126250"
    assert "alpha-risk" not in public_encoded
    assert "zulu-risk" not in public_encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert ": 0." not in public_encoded
    assert "buy" not in public_encoded.lower()
    assert "sell" not in public_encoded.lower()
    assert "recommend" not in public_encoded.lower()
    assert "sizing" not in public_encoded.lower()
    assert "trade" not in public_encoded.lower()
    assert "order" not in public_encoded.lower()
    assert not any(
        _has_forbidden_public_surface(value)
        for value in _walk_payload_keys(first_payload) + _walk_payload_strings(first_payload)
    )


def test_validation_rejects_non_decimal_values_bad_flags_and_digest_tampering() -> None:
    module = api()
    populated = report(mechanics_input())

    for value in (config(), mechanics_input(), populated, *populated.rows, *populated.reason_code_counts):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item_value is None:
                continue
            if item.name.endswith(
                (
                    "_age_seconds",
                    "_concentration_ratio",
                    "_count",
                    "_coverage_ratio",
                    "_haircut_ratio",
                    "_ratio",
                    "_score",
                    "_weight",
                ),
            ):
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].risk_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="maximum_pass_spread_width_ratio"):
        config(maximum_pass_spread_width_ratio=DecimalSubclass("0.030000"))
    with pytest.raises(ValueError, match="maximum_watch_spread_width_ratio"):
        config(maximum_watch_spread_width_ratio=0.08)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="weights"):
        config(liquidity_concentration_weight=d("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(mechanics_input(), generated_at=datetime(2026, 7, 8, 21, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            mechanics_input(),
            generated_at=DatetimeSubclass(2026, 7, 8, 21, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        report(mechanics_input(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="bucket_label"):
        mechanics_input(" market-id")
    with pytest.raises(ValueError, match="bucket_label"):
        mechanics_input("market_id_alpha")
    with pytest.raises(ValueError, match="bucket_label"):
        mechanics_input("market_slug_alpha")
    with pytest.raises(ValueError, match="spread_width_ratio"):
        mechanics_input(spread_width_ratio=100)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at"):
        mechanics_input(observed_at=datetime(2026, 7, 8, 21, 0))
    with pytest.raises(ValueError, match="depth_coverage_ratio"):
        mechanics_input(depth_coverage_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="latency_haircut_ratio"):
        mechanics_input(latency_haircut_ratio=-d("0.100000"))
    with pytest.raises(ValueError, match="liquidity_concentration_ratio"):
        mechanics_input(liquidity_concentration_ratio=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        mechanics_input(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="reason_codes"):
        mechanics_input(reason_codes=("source_url_seen",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(mechanics_input(), paper_only=False)
    with pytest.raises(ValueError, match="risk_score"):
        replace(populated.rows[0], risk_score=d("0.900000"))
    with pytest.raises(ValueError, match="status"):
        replace(populated, status="watch")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="report"):
        module.research_market_spread_depth_latency_risk_report_payload(object())
    with pytest.raises(ValueError, match="readonly"):
        replace(populated, readonly=False)


def test_owned_module_has_no_raw_market_decision_or_execution_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_spread_depth_latency_risk_report.py"
    )
    text = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "database",
        "network",
        "wallet",
        "auth",
        "candidate_id",
        "condition_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token_id",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recommend",
        "sizing",
    )

    assert all(term not in text for term in forbidden_terms)


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
            keys.append(key)
            keys.extend(_walk_payload_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_payload_keys(item))
    return tuple(keys)


def _walk_payload_strings(value: object) -> tuple[str, ...]:
    strings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            strings.append(str(key))
            strings.extend(_walk_payload_strings(item))
    elif isinstance(value, list):
        for item in value:
            strings.extend(_walk_payload_strings(item))
    elif isinstance(value, str):
        strings.append(value)
    return tuple(strings)


def _has_forbidden_public_surface(value: str) -> bool:
    lowered = value.lower()
    return any(
        term in lowered
        for term in (
            "candidate_id",
            "condition_id",
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
        )
    )
