from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_gold_volatility_catalyst_digest import (
    DEFAULT_MARKET_RESEARCH_GOLD_VOLATILITY_CATALYST_DIGEST_CONFIG_VERSION,
    MarketResearchGoldVolatilityCatalystDigestConfig,
    MarketResearchGoldVolatilityCatalystDigestInputRow,
    MarketResearchGoldVolatilityCatalystDigestReasonCodeCount,
    MarketResearchGoldVolatilityCatalystDigestReport,
    MarketResearchGoldVolatilityCatalystDigestRow,
    build_market_research_gold_volatility_catalyst_digest,
    market_research_gold_volatility_catalyst_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchGoldVolatilityCatalystDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_GOLD_VOLATILITY_CATALYST_DIGEST_CONFIG_VERSION
        ),
        "max_research_age_seconds": d("7200.000000"),
        "watch_within_seconds": d("86400.000000"),
        "min_reference_count": d("2.000000"),
        "min_atr_move_score": d("0.550000"),
        "min_options_skew_score": d("0.500000"),
        "min_liquidity_score": d("0.650000"),
        "max_realized_volatility_score": d("0.750000"),
        "confidence_decay_per_stale_research": d("0.100000"),
        "confidence_decay_per_elapsed_catalyst": d("0.200000"),
        "confidence_decay_per_thin_references": d("0.080000"),
        "confidence_decay_per_atr_gap": d("0.120000"),
        "confidence_decay_per_options_skew_gap": d("0.100000"),
        "confidence_decay_per_volatility_liquidity_gap": d("0.150000"),
    }
    values.update(overrides)
    return MarketResearchGoldVolatilityCatalystDigestConfig(**values)


def input_row(
    market_research_key: str = "gold.volatility.ready",
    *,
    volatility_catalyst_key: str = "gold.fomc.volatility",
    catalyst_family: str = "macro-rates",
    public_catalyst_reference: str = "cme-fedwatch-public-note",
    catalyst_at: datetime | None = None,
    research_observed_at: datetime | None = None,
    reference_count: Decimal = d("3.000000"),
    atr_move_score: Decimal = d("0.700000"),
    options_skew_score: Decimal = d("0.650000"),
    realized_volatility_score: Decimal = d("0.400000"),
    liquidity_score: Decimal = d("0.850000"),
    base_confidence_score: Decimal = d("0.800000"),
    source_config_version: str = "gold-volatility-catalyst-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchGoldVolatilityCatalystDigestInputRow:
    return MarketResearchGoldVolatilityCatalystDigestInputRow(
        market_research_key=market_research_key,
        volatility_catalyst_key=volatility_catalyst_key,
        catalyst_family=catalyst_family,
        public_catalyst_reference=public_catalyst_reference,
        catalyst_at=catalyst_at or GENERATED_AT + timedelta(hours=10),
        research_observed_at=research_observed_at
        or GENERATED_AT - timedelta(minutes=45),
        reference_count=reference_count,
        atr_move_score=atr_move_score,
        options_skew_score=options_skew_score,
        realized_volatility_score=realized_volatility_score,
        liquidity_score=liquidity_score,
        base_confidence_score=base_confidence_score,
        source_config_version=source_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[MarketResearchGoldVolatilityCatalystDigestInputRow, ...],
    *,
    cfg: MarketResearchGoldVolatilityCatalystDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchGoldVolatilityCatalystDigestReport:
    return build_market_research_gold_volatility_catalyst_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_gold_volatility_catalyst_digest_scores_statuses_counts_and_redacts() -> None:
    summary = report(
        (
            input_row(
                "gold.blocked",
                volatility_catalyst_key="gold.cpi.volatility",
                catalyst_family="inflation",
                public_catalyst_reference=(
                    "https://gold.example/volatility?token=secret-123"
                ),
                catalyst_at=GENERATED_AT - timedelta(minutes=30),
                research_observed_at=GENERATED_AT - timedelta(hours=3),
                reference_count=d("1.000000"),
                atr_move_score=d("0.300000"),
                options_skew_score=d("0.400000"),
                realized_volatility_score=d("0.900000"),
                liquidity_score=d("0.400000"),
                base_confidence_score=d("0.900000"),
            ),
            input_row(
                "gold.watch",
                volatility_catalyst_key="gold.jobs.volatility",
                catalyst_family="labor-market",
                public_catalyst_reference="wallet://private/gold-vol-feed",
                catalyst_at=GENERATED_AT + timedelta(hours=4),
                research_observed_at=GENERATED_AT - timedelta(hours=3),
                reference_count=d("2.000000"),
                atr_move_score=d("0.700000"),
                options_skew_score=d("0.450000"),
                realized_volatility_score=d("0.500000"),
                liquidity_score=d("0.900000"),
                base_confidence_score=d("0.700000"),
            ),
            input_row(
                "gold.ready",
                volatility_catalyst_key="gold.fomc.volatility",
                catalyst_family="macro-rates",
                public_catalyst_reference="cme-fedwatch-public-note",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, MarketResearchGoldVolatilityCatalystDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_GOLD_VOLATILITY_CATALYST_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_gold_volatility_catalyst_digest"
    )
    assert summary.volatility_catalyst_count == d("3.000000")
    assert summary.ready_catalyst_count == d("1.000000")
    assert summary.watch_catalyst_count == d("1.000000")
    assert summary.blocked_catalyst_count == d("1.000000")
    assert summary.upcoming_catalyst_count == d("2.000000")
    assert summary.elapsed_catalyst_count == d("1.000000")
    assert summary.stale_research_count == d("2.000000")
    assert summary.thin_reference_count == d("1.000000")
    assert summary.atr_gap_catalyst_count == d("1.000000")
    assert summary.options_skew_gap_catalyst_count == d("2.000000")
    assert summary.volatility_liquidity_gap_catalyst_count == d("1.000000")
    assert summary.average_confidence_score == d("0.483333")
    assert summary.ready_catalyst_ratio == d("0.333333")
    assert summary.max_observed_research_age_seconds == d("10800.000000")
    assert summary.nearest_seconds_until_catalyst == d("-1800.000000")
    assert tuple(row.volatility_catalyst_key for row in summary.rows) == (
        "gold.cpi.volatility",
        "gold.jobs.volatility",
        "gold.fomc.volatility",
    )

    blocked = summary.rows[0]
    assert blocked.catalyst_status == "blocked"
    assert blocked.seconds_until_catalyst == d("-1800.000000")
    assert blocked.research_age_seconds == d("10800.000000")
    assert blocked.reference_gap_count == d("1.000000")
    assert blocked.confidence_decay_score == d("0.750000")
    assert blocked.confidence_score == d("0.150000")
    assert blocked.redacted_public_catalyst_reference == "sha256:47187c1dab18"
    assert blocked.reason_codes == (
        "market_research_gold_volatility_catalyst_digest_stale_research",
        "market_research_gold_volatility_catalyst_digest_elapsed",
        "market_research_gold_volatility_catalyst_digest_thin_references",
        "market_research_gold_volatility_catalyst_digest_atr_move_gap",
        "market_research_gold_volatility_catalyst_digest_options_skew_gap",
        "market_research_gold_volatility_catalyst_digest_volatility_liquidity_gap",
    )

    watched = summary.rows[1]
    assert watched.catalyst_status == "watch"
    assert watched.confidence_decay_score == d("0.200000")
    assert watched.confidence_score == d("0.500000")
    assert watched.redacted_public_catalyst_reference == "sha256:4f3a5c3bd373"
    assert watched.reason_codes == (
        "market_research_gold_volatility_catalyst_digest_stale_research",
        "market_research_gold_volatility_catalyst_digest_options_skew_gap",
    )

    ready = summary.rows[2]
    assert ready.catalyst_status == "ready"
    assert ready.confidence_score == d("0.800000")
    assert ready.redacted_public_catalyst_reference == "cme-fedwatch-public-note"
    assert ready.reason_codes == (
        "market_research_gold_volatility_catalyst_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchGoldVolatilityCatalystDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_volatility_catalyst_digest_stale_research"
            ),
            count=d("2.000000"),
            catalyst_ratio=d("0.666667"),
        ),
        MarketResearchGoldVolatilityCatalystDigestReasonCodeCount(
            reason_code="market_research_gold_volatility_catalyst_digest_elapsed",
            count=d("1.000000"),
            catalyst_ratio=d("0.333333"),
        ),
        MarketResearchGoldVolatilityCatalystDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_volatility_catalyst_digest_thin_references"
            ),
            count=d("1.000000"),
            catalyst_ratio=d("0.333333"),
        ),
        MarketResearchGoldVolatilityCatalystDigestReasonCodeCount(
            reason_code="market_research_gold_volatility_catalyst_digest_atr_move_gap",
            count=d("1.000000"),
            catalyst_ratio=d("0.333333"),
        ),
        MarketResearchGoldVolatilityCatalystDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_volatility_catalyst_digest_options_skew_gap"
            ),
            count=d("2.000000"),
            catalyst_ratio=d("0.666667"),
        ),
        MarketResearchGoldVolatilityCatalystDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_volatility_catalyst_digest_volatility_liquidity_gap"
            ),
            count=d("1.000000"),
            catalyst_ratio=d("0.333333"),
        ),
        MarketResearchGoldVolatilityCatalystDigestReasonCodeCount(
            reason_code="market_research_gold_volatility_catalyst_digest_ready",
            count=d("1.000000"),
            catalyst_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.source_config_versions == (
        ("gold.cpi.volatility", "gold-volatility-catalyst-source-v0"),
        ("gold.fomc.volatility", "gold-volatility-catalyst-source-v0"),
        ("gold.jobs.volatility", "gold-volatility-catalyst-source-v0"),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    public = repr(asdict(summary)).lower()
    for token in (
        "secret-123",
        "gold.example",
        "wallet://",
        "gold-vol-feed",
        "auth",
        "broker",
        "signing",
        "submit",
        "cancel",
        "account",
        "advice",
    ):
        assert token not in public


def test_gold_volatility_catalyst_digest_empty_inputs_are_report_only() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_gold_volatility_catalyst_digest"
    )
    assert summary.volatility_catalyst_count == ZERO
    assert summary.ready_catalyst_count == ZERO
    assert summary.watch_catalyst_count == ZERO
    assert summary.blocked_catalyst_count == ZERO
    assert summary.average_confidence_score == ZERO
    assert summary.ready_catalyst_ratio == ZERO
    assert summary.max_observed_research_age_seconds == ZERO
    assert summary.nearest_seconds_until_catalyst is None
    assert summary.rows == ()
    assert summary.source_config_versions == ()
    assert summary.reason_codes == (
        "market_research_gold_volatility_catalyst_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchGoldVolatilityCatalystDigestReasonCodeCount(
            reason_code="market_research_gold_volatility_catalyst_digest_no_inputs",
            count=d("1.000000"),
            catalyst_ratio=ZERO,
        ),
    )


def test_gold_volatility_catalyst_digest_validates_contracts_and_payload() -> None:
    assert MarketResearchGoldVolatilityCatalystDigestConfig.__dataclass_params__.frozen
    assert MarketResearchGoldVolatilityCatalystDigestInputRow.__dataclass_params__.frozen
    assert MarketResearchGoldVolatilityCatalystDigestRow.__dataclass_params__.frozen
    assert (
        MarketResearchGoldVolatilityCatalystDigestReasonCodeCount
        .__dataclass_params__
        .frozen
    )
    assert MarketResearchGoldVolatilityCatalystDigestReport.__dataclass_params__.frozen

    frozen_summary = report((input_row(),))
    with pytest.raises(FrozenInstanceError):
        config().paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        input_row().atr_move_score = d("0.900000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        frozen_summary.rows[0].paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        frozen_summary.reason_code_counts[0].paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        frozen_summary.paper_only = False  # type: ignore[misc]
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("gold-volatility-v0"))
    with pytest.raises(ValueError, match="max_research_age_seconds"):
        config(max_research_age_seconds=_DecimalSubclass("7200.000000"))
    with pytest.raises(ValueError, match="min_atr_move_score"):
        config(min_atr_move_score=0.55)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="market_research_key"):
        input_row(_StringSubclass("gold.bad"))
    with pytest.raises(ValueError, match="catalyst_family"):
        input_row(catalyst_family="broker-feed")
    with pytest.raises(ValueError, match="public_catalyst_reference"):
        input_row(public_catalyst_reference=" ")
    with pytest.raises(ValueError, match="research_observed_at"):
        input_row(research_observed_at=datetime(2026, 7, 3, 10, 0))
    with pytest.raises(ValueError, match="catalyst_at"):
        input_row(catalyst_at=_DateTimeSubclass(2026, 7, 3, 10, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="reference_count"):
        input_row(reference_count=d("1.500000"))
    with pytest.raises(ValueError, match="atr_move_score"):
        input_row(atr_move_score=d("1.100000"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(TypeError, match="does not support subclassing"):
        type(
            "BadConfig",
            (MarketResearchGoldVolatilityCatalystDigestConfig,),
            {},
        )

    base = input_row()
    with pytest.raises(ValueError, match="input rows"):
        build_market_research_gold_volatility_catalyst_digest(
            [base, base],
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_market_research_gold_volatility_catalyst_digest(
            (base,),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_gold_volatility_catalyst_digest(
            (base,),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 3, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="research_observed_at"):
        report((input_row(research_observed_at=GENERATED_AT + timedelta(seconds=1)),))

    summary = report((base,))
    payload = market_research_gold_volatility_catalyst_digest_payload(summary)
    assert payload["generated_at"] == "2026-07-03T12:00:00+00:00"
    assert payload["volatility_catalyst_count"] == "1.000000"
    assert payload["average_confidence_score"] == "0.800000"
    assert payload["rows"][0]["reference_count"] == "3.000000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert isinstance(payload["rows"], list)

    public = repr(payload).lower()
    assert "datetime." not in public
    assert "decimal(" not in public
    assert "auth" not in public
    assert "wallet" not in public


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_gold_volatility_catalyst_digest_rejects_false_phase1_flags(
    flag_name: str,
) -> None:
    with pytest.raises(ValueError, match=flag_name):
        config(**{flag_name: False})

    with pytest.raises(ValueError, match=flag_name):
        input_row(**{flag_name: False})

    valid_report = report((input_row(),))
    with pytest.raises(ValueError, match=flag_name):
        replace(valid_report.rows[0], **{flag_name: False})

    with pytest.raises(ValueError, match=flag_name):
        replace(valid_report.reason_code_counts[0], **{flag_name: False})

    with pytest.raises(ValueError, match=flag_name):
        replace(valid_report, **{flag_name: False})


def test_gold_volatility_catalyst_digest_has_no_io_auth_wallet_or_trading_surface() -> None:
    module = __import__(
        "polymarket_alpha_lab.market_research_gold_volatility_catalyst_digest",
        fromlist=["__file__"],
    )
    source = open(module.__file__, encoding="utf-8").read()
    tree = ast.parse(source)

    forbidden_calls = {
        "open",
        "connect",
        "request",
        "urlopen",
        "run",
        "Popen",
    }
    forbidden_import_roots = {
        "asyncio",
        "http",
        "json",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_text = (
        "private_key",
        "secret",
        "wallet",
        "order",
        "trade",
        "cancel",
        "replace",
        "exchange",
        "mutation",
        "auth",
        "token",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls

    lowered_source = source.lower()
    for token in forbidden_text:
        assert token not in lowered_source
