from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_fed_balance_sheet_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_FED_BALANCE_SHEET_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchFedBalanceSheetSurpriseDigestConfig,
    MarketResearchFedBalanceSheetSurpriseDigestObservation,
    MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount,
    MarketResearchFedBalanceSheetSurpriseDigestReport,
    MarketResearchFedBalanceSheetSurpriseDigestRow,
    build_market_research_fed_balance_sheet_surprise_digest,
    market_research_fed_balance_sheet_surprise_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketResearchFedBalanceSheetSurpriseDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_FED_BALANCE_SHEET_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "max_observation_age_seconds": d("86400.000000"),
        "min_source_count": d("2.000000"),
        "material_surprise_threshold": d("0.015000"),
        "watch_probability_delta_threshold": d("0.040000"),
        "max_revision_ratio": d("0.150000"),
        "min_confirmation_ratio": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchFedBalanceSheetSurpriseDigestConfig(**values)


def observation(
    condition_id: str = "condition_fed_balance_sheet",
    *,
    research_key: str = "research.fed_balance_sheet.total_assets",
    release_key: str = "fed.h41.total_assets",
    balance_sheet_metric: str = "total_assets",
    public_observation_reference: str = "public-fed-h41-total-assets",
    observed_at: datetime | None = None,
    expected_change: Decimal = d("-10.000000"),
    actual_change: Decimal = d("-12.000000"),
    surprise_ratio: Decimal = d("0.010000"),
    source_count: Decimal = d("3.000000"),
    revision_ratio: Decimal = d("0.040000"),
    confirmation_ratio: Decimal = d("0.880000"),
    market_probability_before: Decimal = d("0.420000"),
    market_probability_after: Decimal = d("0.450000"),
    base_confidence: Decimal = d("0.900000"),
    signal_config_version: str = "fed-balance-sheet-surprise-signal-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchFedBalanceSheetSurpriseDigestObservation:
    return MarketResearchFedBalanceSheetSurpriseDigestObservation(
        condition_id=condition_id,
        research_key=research_key,
        release_key=release_key,
        balance_sheet_metric=balance_sheet_metric,
        public_observation_reference=public_observation_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(hours=2),
        expected_change=expected_change,
        actual_change=actual_change,
        surprise_ratio=surprise_ratio,
        source_count=source_count,
        revision_ratio=revision_ratio,
        confirmation_ratio=confirmation_ratio,
        market_probability_before=market_probability_before,
        market_probability_after=market_probability_after,
        base_confidence=base_confidence,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchFedBalanceSheetSurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchFedBalanceSheetSurpriseDigestReport:
    return build_market_research_fed_balance_sheet_surprise_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_fed_balance_sheet_surprise_digest_reduces_and_sorts_deterministically() -> None:
    summary = report(
        (
            observation(
                "condition_reserves",
                research_key="research.fed_balance_sheet.reserves",
                release_key="fed.h41.reserves",
                balance_sheet_metric="reserve_balances",
                public_observation_reference=(
                    "https://vendor.example/fed-h41?token=secret-123"
                ),
                observed_at=GENERATED_AT - timedelta(days=2),
                expected_change=d("-20.000000"),
                actual_change=d("5.000000"),
                surprise_ratio=d("0.080000"),
                source_count=d("1.000000"),
                revision_ratio=d("0.240000"),
                confirmation_ratio=d("0.500000"),
                market_probability_before=d("0.350000"),
                market_probability_after=d("0.480000"),
                base_confidence=d("0.860000"),
            ),
            observation(
                "condition_rrp",
                research_key="research.fed_balance_sheet.rrp",
                release_key="fed.h41.reverse_repo",
                balance_sheet_metric="reverse_repo",
                public_observation_reference="private-rrp-feed",
                observed_at=GENERATED_AT - timedelta(hours=10),
                expected_change=d("-35.000000"),
                actual_change=d("-60.000000"),
                surprise_ratio=d("0.030000"),
                source_count=d("2.000000"),
                revision_ratio=d("0.080000"),
                confirmation_ratio=d("0.650000"),
                market_probability_before=d("0.510000"),
                market_probability_after=d("0.540000"),
                base_confidence=d("0.840000"),
            ),
            observation(
                "condition_assets",
                research_key="research.fed_balance_sheet.total_assets",
                release_key="fed.h41.total_assets",
                balance_sheet_metric="total_assets",
                public_observation_reference="public-fed-h41-total-assets",
                observed_at=GENERATED_AT - timedelta(hours=2),
                expected_change=d("-10.000000"),
                actual_change=d("-12.000000"),
                surprise_ratio=d("0.010000"),
                source_count=d("3.000000"),
                revision_ratio=d("0.040000"),
                confirmation_ratio=d("0.880000"),
                market_probability_before=d("0.420000"),
                market_probability_after=d("0.450000"),
                base_confidence=d("0.900000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_FED_BALANCE_SHEET_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_fed_balance_sheet_surprise_digest"
    )
    assert summary.observation_count == d("3.000000")
    assert summary.ready_observation_count == d("1.000000")
    assert summary.watch_observation_count == d("1.000000")
    assert summary.blocked_observation_count == d("1.000000")
    assert summary.material_surprise_count == d("2.000000")
    assert summary.stale_observation_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.high_revision_count == d("1.000000")
    assert summary.confirmation_gap_count == d("2.000000")
    assert summary.probability_repricing_count == d("1.000000")
    assert summary.average_surprise_ratio == d("0.040000")
    assert summary.max_observation_age_seconds == d("172800.000000")
    assert summary.average_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.release_key for row in summary.rows) == (
        "fed.h41.reserves",
        "fed.h41.reverse_repo",
        "fed.h41.total_assets",
    )

    reserves = summary.rows[0]
    assert reserves.digest_status == "blocked"
    assert reserves.observation_age_seconds == d("172800.000000")
    assert reserves.surprise_delta == d("25.000000")
    assert reserves.probability_delta == d("0.130000")
    assert reserves.confidence_decay_factor == d("0.400000")
    assert reserves.final_confidence == d("0.344000")
    assert reserves.redacted_public_observation_reference == "sha256:4b62b069dab5"
    assert reserves.reason_codes == (
        "market_research_fed_balance_sheet_surprise_digest_stale_observation",
        "market_research_fed_balance_sheet_surprise_digest_material_surprise",
        "market_research_fed_balance_sheet_surprise_digest_thin_sources",
        "market_research_fed_balance_sheet_surprise_digest_high_revision",
        "market_research_fed_balance_sheet_surprise_digest_confirmation_gap",
        "market_research_fed_balance_sheet_surprise_digest_probability_repricing",
    )

    rrp = summary.rows[1]
    assert rrp.digest_status == "watch"
    assert rrp.observation_age_seconds == d("36000.000000")
    assert rrp.surprise_delta == d("-25.000000")
    assert rrp.probability_delta == d("0.030000")
    assert rrp.confidence_decay_factor == d("1.000000")
    assert rrp.final_confidence == d("0.840000")
    assert rrp.redacted_public_observation_reference == "sha256:ac58cb763b1f"
    assert rrp.reason_codes == (
        "market_research_fed_balance_sheet_surprise_digest_material_surprise",
        "market_research_fed_balance_sheet_surprise_digest_confirmation_gap",
    )

    assets = summary.rows[2]
    assert assets.digest_status == "ready"
    assert assets.observation_age_seconds == d("7200.000000")
    assert assets.surprise_delta == d("-2.000000")
    assert assets.probability_delta == d("0.030000")
    assert assets.confidence_decay_factor == d("1.000000")
    assert assets.final_confidence == d("0.900000")
    assert assets.redacted_public_observation_reference == "public-fed-h41-total-assets"
    assert assets.reason_codes == (
        "market_research_fed_balance_sheet_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_fed_balance_sheet_surprise_digest_confirmation_gap"
            ),
            count=d("2.000000"),
            observation_ratio=d("0.666667"),
        ),
        MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_fed_balance_sheet_surprise_digest_material_surprise"
            ),
            count=d("2.000000"),
            observation_ratio=d("0.666667"),
        ),
        MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_fed_balance_sheet_surprise_digest_stale_observation"
            ),
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount(
            reason_code="market_research_fed_balance_sheet_surprise_digest_thin_sources",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount(
            reason_code="market_research_fed_balance_sheet_surprise_digest_high_revision",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_fed_balance_sheet_surprise_digest_probability_repricing"
            ),
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount(
            reason_code="market_research_fed_balance_sheet_surprise_digest_ready",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        row.reason_code for row in summary.reason_code_counts
    )

    public = repr(asdict(summary)).lower()
    for token in (
        "secret-123",
        "vendor.example",
        "https://",
        "private-rrp-feed",
        "auth",
        "wallet",
        "account",
        "order",
        "cancel",
        "replace",
    ):
        assert token not in public


def test_fed_balance_sheet_digest_empty_inputs_are_blocked_with_decimal_counts() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.observation_count == ZERO
    assert summary.rows == ()
    assert summary.average_surprise_ratio is None
    assert summary.max_observation_age_seconds is None
    assert summary.average_source_count is None
    assert summary.reason_code_counts == (
        MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount(
            reason_code="market_research_fed_balance_sheet_surprise_digest_no_inputs",
            count=d("1.000000"),
            observation_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_fed_balance_sheet_surprise_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_fed_balance_sheet_digest_dataclasses_are_frozen_and_decimal_only() -> None:
    cfg = config()
    source = observation(observed_at=datetime(2026, 7, 3, 10, 0, tzinfo=timezone.utc))
    summary = report((source,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        cfg.min_source_count = d("4.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source.source_count = d("4.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].final_confidence = d("0.500000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("2.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.observation_count = d("2.000000")  # type: ignore[misc]

    assert source.observed_at.tzinfo is UTC
    assert summary.rows[0].observed_at.tzinfo is UTC
    assert summary.generated_at.tzinfo is UTC

    assert replace(source, observed_at=_DatetimeSubclass(2026, 7, 3, 8)).observed_at == (
        datetime(2026, 7, 3, 8, tzinfo=UTC)
    )

    for value in asdict(summary).values():
        assert not isinstance(value, float)

    def assert_decimal_public_surface(value: object) -> None:
        if is_dataclass(value):
            for field_name, field_value in value.__dict__.items():
                if field_name.endswith("_code_counts"):
                    assert isinstance(field_value, tuple)
                elif any(
                    token in field_name
                    for token in (
                        "count",
                        "ratio",
                        "probability",
                        "confidence",
                        "change",
                        "delta",
                        "seconds",
                    )
                ):
                    assert field_value is None or type(field_value) is Decimal
                assert_decimal_public_surface(field_value)
        elif isinstance(value, tuple):
            for item in value:
                assert_decimal_public_surface(item)
        else:
            assert not isinstance(value, float)

    assert_decimal_public_surface(cfg)
    assert_decimal_public_surface(source)
    assert_decimal_public_surface(summary)

    for cls in (
        MarketResearchFedBalanceSheetSurpriseDigestConfig,
        MarketResearchFedBalanceSheetSurpriseDigestObservation,
        MarketResearchFedBalanceSheetSurpriseDigestRow,
        MarketResearchFedBalanceSheetSurpriseDigestReport,
        MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount,
    ):
        with pytest.raises(TypeError):
            type(f"Sub{cls.__name__}", (cls,), {})

    with pytest.raises(TypeError):
        observation(source_count=2)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        observation(surprise_ratio=0.1)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        config(min_source_count=2)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        observation(research_key=_StringSubclass("research.subclass"))  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        observation(source_count=_DecimalSubclass("2.000000"))


def test_fed_balance_sheet_digest_payload_is_json_ready_stable_and_redacted() -> None:
    summary = report(
        (
            observation(public_observation_reference="public-fed-h41-total-assets"),
            observation(
                "condition_reserves",
                research_key="research.fed_balance_sheet.reserves",
                release_key="fed.h41.reserves",
                balance_sheet_metric="reserve_balances",
                public_observation_reference="private-reserves-feed",
                observed_at=GENERATED_AT - timedelta(days=3),
                surprise_ratio=d("0.090000"),
                confirmation_ratio=d("0.450000"),
            ),
        ),
    )

    payload = market_research_fed_balance_sheet_surprise_digest_payload(summary)

    assert payload["generated_at"] == "2026-07-03T16:00:00+00:00"
    assert payload["observation_count"] == "2.000000"
    assert payload["average_surprise_ratio"] == "0.050000"
    assert payload["rows"][0]["release_key"] == "fed.h41.reserves"
    assert payload["rows"][0]["redacted_public_observation_reference"] == (
        "sha256:1838021f2d9b"
    )
    assert payload["rows"][1]["redacted_public_observation_reference"] == (
        "public-fed-h41-total-assets"
    )

    public = repr(payload).lower()
    for token in (
        "private-reserves-feed",
        "wallet",
        "auth",
        "database",
        "order",
        "trade",
    ):
        assert token not in public


def test_fed_balance_sheet_digest_validates_report_only_scope_and_static_guardrails() -> None:
    for kwargs in (
        {"paper_only": False},
        {"report_only": False},
        {"readonly": False},
    ):
        with pytest.raises(ValueError, match="paper_only/report_only/readonly"):
            config(**kwargs)
        with pytest.raises(ValueError, match="paper_only/report_only/readonly"):
            observation(**kwargs)

    summary = report((observation(),))
    for guarded in (
        config(),
        observation(),
        summary.rows[0],
        summary.reason_code_counts[0],
        summary,
    ):
        for flag in ("paper_only", "report_only", "readonly"):
            with pytest.raises(ValueError, match="paper_only/report_only/readonly"):
                replace(guarded, **{flag: False})

    with pytest.raises(ValueError, match="config_version"):
        config(config_version="fed-balance-sheet-v1")
    with pytest.raises(ValueError, match="public_observation_reference"):
        observation(public_observation_reference="wallet-linked-fed-feed")
    with pytest.raises(ValueError, match="confirmation_ratio"):
        observation(confirmation_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(),), generated_at=_DatetimeSubclass(2026, 7, 3))

    source = Path("src/polymarket_alpha_lab/market_research_fed_balance_sheet_surprise_digest.py")
    text = source.read_text()
    tree = ast.parse(text)

    banned_import_roots = {
        "asyncio",
        "httpx",
        "json",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned_import_roots
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_import_roots

    lowered = text.lower()
    for token in (
        "urlopen",
        "request(",
        "post(",
        "connect(",
        "execute(",
        "wallet",
        "auth",
        "private_key",
        "order placement",
        "cancel_order",
        "replace_order",
        "live trading",
    ):
        assert token not in lowered
