from __future__ import annotations

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
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_resolution_liquidity_watch_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_RESOLUTION_LIQUIDITY_WATCH_REPORT_CONFIG_VERSION
        ),
        "pass_max_resolution_pressure_score": d("0.250000"),
        "watch_max_resolution_pressure_score": d("0.550000"),
        "pass_min_liquidity_quality_score": d("0.750000"),
        "watch_min_liquidity_quality_score": d("0.450000"),
        "watch_joint_pressure_score": d("0.350000"),
        "block_joint_pressure_score": d("0.650000"),
        "hard_resolution_uncertainty_floor": d("0.850000"),
        "hard_liquidity_quality_ceiling": d("0.200000"),
        "resolution_uncertainty_weight": d("0.500000"),
        "resolution_source_conflict_weight": d("0.250000"),
        "resolution_rule_ambiguity_weight": d("0.250000"),
        "liquidity_quality_gap_weight": d("0.400000"),
        "liquidity_staleness_weight": d("0.200000"),
        "liquidity_depth_fragility_weight": d("0.200000"),
        "spread_pressure_weight": d("0.200000"),
        "joint_resolution_pressure_weight": d("0.450000"),
        "joint_liquidity_pressure_weight": d("0.350000"),
        "joint_interaction_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchMarketResolutionLiquidityWatchConfig(**values)


def candidate(
    candidate_id: str,
    *,
    observed_at: datetime = GENERATED_AT - timedelta(minutes=10),
    resolution_uncertainty_score: Decimal = d("0.100000"),
    resolution_source_conflict_score: Decimal = d("0.100000"),
    resolution_rule_ambiguity_score: Decimal = d("0.100000"),
    liquidity_quality_score: Decimal = d("0.900000"),
    liquidity_staleness_score: Decimal = d("0.100000"),
    liquidity_depth_fragility_score: Decimal = d("0.100000"),
    spread_pressure_score: Decimal = d("0.100000"),
    market_id: str | None = "private-market-id",
    market_slug: str | None = "private-market-slug",
    market_question: str | None = "Will the private market resolve?",
    source_url: str | None = "https://example.invalid/private-source",
    source_text: str | None = "private source text",
    dsn: str | None = "postgres://private/db",
    table_name: str | None = "private_table",
    private_token: str | None = "private-token",
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketResolutionLiquidityWatchCandidate(
        candidate_id=candidate_id,
        observed_at=observed_at,
        resolution_uncertainty_score=resolution_uncertainty_score,
        resolution_source_conflict_score=resolution_source_conflict_score,
        resolution_rule_ambiguity_score=resolution_rule_ambiguity_score,
        liquidity_quality_score=liquidity_quality_score,
        liquidity_staleness_score=liquidity_staleness_score,
        liquidity_depth_fragility_score=liquidity_depth_fragility_score,
        spread_pressure_score=spread_pressure_score,
        market_id=market_id,
        market_slug=market_slug,
        market_question=market_question,
        source_url=source_url,
        source_text=source_text,
        dsn=dsn,
        table_name=table_name,
        private_token=private_token,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_resolution_liquidity_watch_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_with_public_report_only_flags() -> None:
    module = api()
    watch_report = report()

    assert module.RESOLUTION_LIQUIDITY_WATCH_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "RESOLUTION_LIQUIDITY_WATCH_STATUSES",
        "DEFAULT_RESEARCH_MARKET_RESOLUTION_LIQUIDITY_WATCH_REPORT_CONFIG_VERSION",
        "ResearchMarketResolutionLiquidityWatchCandidate",
        "ResearchMarketResolutionLiquidityWatchConfig",
        "ResearchMarketResolutionLiquidityWatchReasonCodeCount",
        "ResearchMarketResolutionLiquidityWatchReport",
        "ResearchMarketResolutionLiquidityWatchRow",
        "build_research_market_resolution_liquidity_watch_report",
        "research_market_resolution_liquidity_watch_report_digest",
        "research_market_resolution_liquidity_watch_report_payload",
    )
    assert type(watch_report) is module.ResearchMarketResolutionLiquidityWatchReport
    assert is_dataclass(watch_report)
    assert watch_report.generated_at == GENERATED_AT
    assert watch_report.config_version == (
        "research-market-resolution-liquidity-watch-report-v0"
    )
    assert watch_report.candidate_count == ZERO
    assert watch_report.pass_count == ZERO
    assert watch_report.watch_count == ZERO
    assert watch_report.block_count == ZERO
    assert watch_report.mean_joint_pressure_score == ZERO
    assert watch_report.max_resolution_pressure_score == ZERO
    assert watch_report.min_liquidity_quality_score == ZERO
    assert watch_report.status == "block"
    assert watch_report.reason_codes == ("no_resolution_liquidity_candidates_block",)
    assert watch_report.reason_code_counts == (
        module.ResearchMarketResolutionLiquidityWatchReasonCodeCount(
            reason_code="no_resolution_liquidity_candidates_block",
            count=ONE,
            row_ratio=ZERO,
        ),
    )
    assert watch_report.rows == ()
    assert watch_report.paper_only is True
    assert watch_report.report_only is True
    assert watch_report.readonly is True


def test_scores_pass_watch_and_block_joint_resolution_liquidity_pressure() -> None:
    watch_report = report(
        candidate(
            "candidate-watch",
            resolution_uncertainty_score=d("0.450000"),
            resolution_source_conflict_score=d("0.500000"),
            resolution_rule_ambiguity_score=d("0.400000"),
            liquidity_quality_score=d("0.550000"),
            liquidity_staleness_score=d("0.500000"),
            liquidity_depth_fragility_score=d("0.450000"),
            spread_pressure_score=d("0.400000"),
        ),
        candidate(
            "candidate-block",
            resolution_uncertainty_score=d("0.900000"),
            resolution_source_conflict_score=d("0.900000"),
            resolution_rule_ambiguity_score=d("0.900000"),
            liquidity_quality_score=d("0.100000"),
            liquidity_staleness_score=d("0.900000"),
            liquidity_depth_fragility_score=d("0.900000"),
            spread_pressure_score=d("0.900000"),
            reason_codes=("manual_resolution_liquidity_review",),
        ),
        candidate("candidate-pass"),
    )

    assert watch_report.candidate_count == d("3.000000")
    assert watch_report.pass_count == ONE
    assert watch_report.watch_count == ONE
    assert watch_report.block_count == ONE
    assert watch_report.mean_joint_pressure_score == d("0.454833")
    assert watch_report.max_resolution_pressure_score == d("0.900000")
    assert watch_report.min_liquidity_quality_score == d("0.100000")
    assert watch_report.status == "block"

    block_row, pass_row, watch_row = watch_report.rows
    assert tuple(row.public_row_ref for row in watch_report.rows) == (
        "resolution_liquidity_watch_row_001",
        "resolution_liquidity_watch_row_002",
        "resolution_liquidity_watch_row_003",
    )
    assert tuple(row.status for row in watch_report.rows) == ("block", "pass", "watch")
    assert block_row.resolution_pressure_score == d("0.900000")
    assert block_row.liquidity_pressure_score == d("0.900000")
    assert block_row.joint_pressure_score == d("0.882000")
    assert block_row.hard_flags == (
        "liquidity_quality_hard_block",
        "resolution_uncertainty_hard_block",
    )
    assert block_row.reason_codes == (
        "input_manual_resolution_liquidity_review",
        "joint_resolution_liquidity_pressure_block",
        "liquidity_depth_fragility_high",
        "liquidity_quality_block",
        "liquidity_quality_hard_block",
        "liquidity_staleness_high",
        "resolution_rule_ambiguity_high",
        "resolution_source_conflict_high",
        "resolution_uncertainty_hard_block",
        "resolution_uncertainty_high",
        "spread_pressure_high",
    )
    assert pass_row.resolution_pressure_score == d("0.100000")
    assert pass_row.liquidity_pressure_score == d("0.100000")
    assert pass_row.joint_pressure_score == d("0.082000")
    assert pass_row.reason_codes == (
        "joint_resolution_liquidity_pressure_pass",
        "liquidity_depth_fragility_low",
        "liquidity_quality_pass",
        "liquidity_staleness_low",
        "resolution_rule_ambiguity_low",
        "resolution_source_conflict_low",
        "resolution_uncertainty_low",
        "spread_pressure_low",
    )
    assert watch_row.resolution_pressure_score == d("0.450000")
    assert watch_row.liquidity_pressure_score == d("0.450000")
    assert watch_row.joint_pressure_score == d("0.400500")
    assert "joint_resolution_liquidity_pressure_watch" in watch_row.reason_codes
    assert watch_report.reason_codes == (
        "liquidity_quality_hard_block",
        "manual_resolution_liquidity_review_present",
        "resolution_liquidity_watch_report_block",
        "resolution_uncertainty_hard_block",
    )


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    module = api()
    first = report(
        candidate(
            "raw-candidate-secret-001",
            reason_codes=("zeta_note", "alpha_note"),
            market_id="market-secret-id-001",
            market_slug="market-secret-slug",
            market_question="Will this private question resolve yes?",
            source_url="https://example.invalid/source-secret-url",
            source_text=(
                "source secret text with dsn postgres://host/db table fills "
                "token abc wallet order trade buy sell recommendation sizing"
            ),
            dsn="postgres://host/db",
            table_name="private_fills",
            private_token="token-abc",
        ),
        candidate("candidate-public-safe"),
    )
    second = report(
        candidate("candidate-public-safe"),
        candidate(
            "raw-candidate-secret-001",
            reason_codes=("alpha_note", "zeta_note"),
            market_id="market-secret-id-001",
            market_slug="market-secret-slug",
            market_question="Will this private question resolve yes?",
            source_url="https://example.invalid/source-secret-url",
            source_text=(
                "source secret text with dsn postgres://host/db table fills "
                "token abc wallet order trade buy sell recommendation sizing"
            ),
            dsn="postgres://host/db",
            table_name="private_fills",
            private_token="token-abc",
        ),
    )

    first_payload = module.research_market_resolution_liquidity_watch_report_payload(first)
    second_payload = module.research_market_resolution_liquidity_watch_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert module.research_market_resolution_liquidity_watch_report_digest(first) == (
        module.research_market_resolution_liquidity_watch_report_digest(second)
    )
    assert len(module.research_market_resolution_liquidity_watch_report_digest(first)) == 64
    int(module.research_market_resolution_liquidity_watch_report_digest(first), 16)
    assert first_payload["public_report_digest"] == first.public_report_digest
    assert first_payload["rows"][0]["public_row_ref"] == (
        "resolution_liquidity_watch_row_001"
    )
    assert first_payload["rows"][0]["joint_pressure_score"] == "0.082000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert ": 0." not in encoded
    for sensitive_value in (
        "raw-candidate-secret-001",
        "market-secret-id-001",
        "market-secret-slug",
        "Will this private question resolve yes?",
        "https://example.invalid/source-secret-url",
        "source secret text",
        "postgres://host/db",
        "private_fills",
        "token-abc",
    ):
        assert sensitive_value not in encoded
    assert not any(
        _has_forbidden_public_surface_key(key)
        for key in _walk_payload_keys(first_payload)
    )


def test_validation_rejects_non_decimal_values_bad_flags_and_digest_tampering() -> None:
    module = api()
    populated = report(candidate("candidate-valid"))

    for value in (config(), candidate("candidate-valid-2"), populated, *populated.rows):
        assert is_dataclass(value)
    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].joint_pressure_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="resolution_uncertainty_score"):
        candidate("bad-float", resolution_uncertainty_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="liquidity_quality_score"):
        candidate("bad-subclass", liquidity_quality_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="observed_at"):
        candidate("bad-time", observed_at=datetime(2026, 7, 8, 11, 45))
    with pytest.raises(ValueError, match="generated_at"):
        report(candidate("ok-time"), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            candidate("subclass-time"),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        report(candidate("future-time", observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="reason_codes"):
        candidate("bad-reason", reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="unsafe public"):
        candidate("bad-reason-leak", reason_codes=("market_id",))
    with pytest.raises(ValueError, match="paper_only"):
        candidate("bad-flag", paper_only=False)
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="public_report_digest"):
        replace(populated, public_report_digest="0" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(populated.rows[0], status="blocked")
    with pytest.raises(TypeError):
        type("ConfigSubclass", (module.ResearchMarketResolutionLiquidityWatchConfig,), {})


def test_owned_module_has_no_network_db_wallet_order_or_recommendation_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_resolution_liquidity_watch_report.py"
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
        "private_key",
        "wallet",
        "auth",
        "place_order",
        "cancel_order",
        "order_size",
        "live_trading",
        "trade_recommendation",
        "sizing",
        "recommendation",
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
        "condition_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "source_text",
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
