from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_business_inventories_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_BUSINESS_INVENTORIES_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchBusinessInventoriesSurpriseDigestConfig,
    MarketResearchBusinessInventoriesSurpriseDigestReasonCodeCount,
    MarketResearchBusinessInventoriesSurpriseDigestReport,
    MarketResearchBusinessInventoriesSurpriseDigestRow,
    MarketResearchBusinessInventoriesSurpriseDigestSignal,
    build_market_research_business_inventories_surprise_digest,
    market_research_business_inventories_surprise_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 18, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchBusinessInventoriesSurpriseDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_BUSINESS_INVENTORIES_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "max_signal_age_seconds": d("7200.000000"),
        "min_source_count": d("2.000000"),
        "material_surprise_threshold": d("0.030000"),
        "max_revision_ratio": d("0.120000"),
        "min_confirmation_ratio": d("0.700000"),
        "watch_confidence_threshold": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchBusinessInventoriesSurpriseDigestConfig(**values)


def signal(
    condition_id: str = "condition_business_inventories_total",
    *,
    research_key: str = "research.business_inventories.total",
    release_key: str = "business_inventories.census.total",
    inventory_segment: str = "total_business",
    public_signal_reference: str = "public-census-business-inventories",
    observed_at: datetime | None = None,
    expected_inventory_mom: Decimal = d("0.200000"),
    actual_inventory_mom: Decimal = d("0.100000"),
    surprise_score: Decimal = d("0.020000"),
    source_count: Decimal = d("3.000000"),
    revision_ratio: Decimal = d("0.040000"),
    confirmation_ratio: Decimal = d("0.900000"),
    base_confidence: Decimal = d("0.920000"),
    signal_config_version: str = "business-inventories-signal-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchBusinessInventoriesSurpriseDigestSignal:
    return MarketResearchBusinessInventoriesSurpriseDigestSignal(
        condition_id=condition_id,
        research_key=research_key,
        release_key=release_key,
        inventory_segment=inventory_segment,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        expected_inventory_mom=expected_inventory_mom,
        actual_inventory_mom=actual_inventory_mom,
        surprise_score=surprise_score,
        source_count=source_count,
        revision_ratio=revision_ratio,
        confirmation_ratio=confirmation_ratio,
        base_confidence=base_confidence,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchBusinessInventoriesSurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchBusinessInventoriesSurpriseDigestReport:
    return build_market_research_business_inventories_surprise_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_business_inventories_surprise_digest_reduces_and_sorts_deterministically() -> None:
    summary = report(
        (
            signal(
                "condition_retail",
                research_key="research.business_inventories.retail",
                release_key="business_inventories.retail",
                inventory_segment="retail",
                public_signal_reference=(
                    "https://vendor.example/business-inventories?token=secret-123"
                ),
                observed_at=GENERATED_AT - timedelta(hours=3),
                expected_inventory_mom=d("0.400000"),
                actual_inventory_mom=d("-0.100000"),
                surprise_score=d("0.080000"),
                source_count=d("1.000000"),
                revision_ratio=d("0.200000"),
                confirmation_ratio=d("0.520000"),
                base_confidence=d("0.880000"),
            ),
            signal(
                "condition_manufacturing",
                research_key="research.business_inventories.manufacturing",
                release_key="business_inventories.manufacturing",
                inventory_segment="manufacturing",
                public_signal_reference="private-business-inventories-feed",
                observed_at=GENERATED_AT - timedelta(hours=1),
                expected_inventory_mom=d("0.100000"),
                actual_inventory_mom=d("-0.120000"),
                surprise_score=d("0.050000"),
                source_count=d("2.000000"),
                revision_ratio=d("0.100000"),
                confirmation_ratio=d("0.620000"),
                base_confidence=d("0.860000"),
            ),
            signal(
                "condition_total",
                research_key="research.business_inventories.total",
                release_key="business_inventories.total",
                inventory_segment="total",
                public_signal_reference="public-census-business-inventories",
                observed_at=GENERATED_AT - timedelta(minutes=25),
                expected_inventory_mom=d("0.200000"),
                actual_inventory_mom=d("0.100000"),
                surprise_score=d("0.020000"),
                source_count=d("3.000000"),
                revision_ratio=d("0.040000"),
                confirmation_ratio=d("0.900000"),
                base_confidence=d("0.920000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_BUSINESS_INVENTORIES_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_business_inventories_surprise_digest"
    )
    assert summary.signal_count == d("3.000000")
    assert summary.ready_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("1.000000")
    assert summary.blocked_signal_count == d("1.000000")
    assert summary.material_surprise_count == d("2.000000")
    assert summary.stale_signal_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.high_revision_count == d("1.000000")
    assert summary.confirmation_gap_count == d("2.000000")
    assert summary.average_surprise_score == d("0.050000")
    assert summary.max_signal_age_seconds == d("10800.000000")
    assert summary.average_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.release_key for row in summary.rows) == (
        "business_inventories.retail",
        "business_inventories.manufacturing",
        "business_inventories.total",
    )

    retail = summary.rows[0]
    assert retail.digest_status == "blocked"
    assert retail.signal_age_seconds == d("10800.000000")
    assert retail.surprise_delta == d("-0.500000")
    assert retail.confidence_decay_factor == d("0.400000")
    assert retail.final_confidence == d("0.352000")
    assert retail.redacted_public_signal_reference == "sha256:c8f7ceb67c2e"
    assert retail.reason_codes == (
        "market_research_business_inventories_surprise_digest_stale_signal",
        "market_research_business_inventories_surprise_digest_material_surprise",
        "market_research_business_inventories_surprise_digest_thin_sources",
        "market_research_business_inventories_surprise_digest_high_revision",
        "market_research_business_inventories_surprise_digest_confirmation_gap",
    )

    manufacturing = summary.rows[1]
    assert manufacturing.digest_status == "watch"
    assert manufacturing.signal_age_seconds == d("3600.000000")
    assert manufacturing.surprise_delta == d("-0.220000")
    assert manufacturing.confidence_decay_factor == d("0.800000")
    assert manufacturing.final_confidence == d("0.688000")
    assert manufacturing.redacted_public_signal_reference == "sha256:70bd4cb6f6e6"
    assert manufacturing.reason_codes == (
        "market_research_business_inventories_surprise_digest_material_surprise",
        "market_research_business_inventories_surprise_digest_confirmation_gap",
    )

    total = summary.rows[2]
    assert total.digest_status == "ready"
    assert total.signal_age_seconds == d("1500.000000")
    assert total.surprise_delta == d("-0.100000")
    assert total.confidence_decay_factor == d("1.000000")
    assert total.final_confidence == d("0.920000")
    assert total.redacted_public_signal_reference == "public-census-business-inventories"
    assert total.reason_codes == (
        "market_research_business_inventories_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchBusinessInventoriesSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_business_inventories_surprise_digest_"
                "confirmation_gap"
            ),
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchBusinessInventoriesSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_business_inventories_surprise_digest_"
                "material_surprise"
            ),
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchBusinessInventoriesSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_business_inventories_surprise_digest_stale_signal"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchBusinessInventoriesSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_business_inventories_surprise_digest_thin_sources"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchBusinessInventoriesSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_business_inventories_surprise_digest_high_revision"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )

    payload = market_research_business_inventories_surprise_digest_payload(summary)
    assert payload["signal_count"] == "3.000000"
    assert payload["average_surprise_score"] == "0.050000"
    assert payload["rows"][0]["redacted_public_signal_reference"] == "sha256:c8f7ceb67c2e"
    assert "https://vendor.example" not in repr(payload)
    assert ast.literal_eval(repr(payload)) == payload
    assert asdict(summary)["paper_only"] is True


def test_business_inventories_surprise_digest_empty_inputs_block_as_missing_evidence() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_business_inventories_surprise_digest"
    )
    assert summary.reason_codes == (
        "market_research_business_inventories_surprise_digest_no_inputs",
    )
    assert summary.signal_count == ZERO
    assert summary.ready_signal_count == ZERO
    assert summary.watch_signal_count == ZERO
    assert summary.blocked_signal_count == ZERO
    assert summary.material_surprise_count == ZERO
    assert summary.stale_signal_count == ZERO
    assert summary.thin_source_count == ZERO
    assert summary.high_revision_count == ZERO
    assert summary.confirmation_gap_count == ZERO
    assert summary.average_surprise_score == ZERO
    assert summary.max_signal_age_seconds == ZERO
    assert summary.average_source_count == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        MarketResearchBusinessInventoriesSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_business_inventories_surprise_digest_no_inputs"
            ),
            count=d("1.000000"),
            signal_ratio=d("1.000000"),
        ),
    )

    for name, value in asdict(summary).items():
        if name.endswith("_count") or name.endswith("_ratio") or name.startswith("average_"):
            assert type(value) is Decimal


def test_business_inventories_surprise_digest_dataclasses_are_frozen_and_normalize_utc() -> None:
    local_observed_at = datetime(
        2026,
        7,
        3,
        10,
        30,
        tzinfo=timezone(timedelta(hours=-6)),
    )
    row = signal(observed_at=local_observed_at)
    summary = report((row,))
    reason_count = MarketResearchBusinessInventoriesSurpriseDigestReasonCodeCount(
        reason_code="market_research_business_inventories_surprise_digest_material_surprise",
        count=d("1.000000"),
        signal_ratio=d("1.000000"),
    )

    assert row.observed_at == datetime(2026, 7, 3, 16, 30, tzinfo=UTC)
    assert row.observed_at.tzinfo is UTC
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC

    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        config().config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.condition_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].digest_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        reason_count.count = d("2.000000")  # type: ignore[misc]

    replaced = replace(row, source_count=d("4.000000"))
    assert replaced.source_count == d("4.000000")
    assert replaced.observed_at.tzinfo is UTC


def test_business_inventories_surprise_digest_rejects_unsafe_or_non_decimal_public_surface() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="research_key"):
        signal(research_key="research.business_inventories.secret")
    with pytest.raises(TypeError, match="Decimal"):
        signal(source_count=2)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="datetime"):
        signal(observed_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC))
    with pytest.raises(TypeError, match="str"):
        signal(research_key=_StringSubclass("research.business_inventories.subclass"))
    with pytest.raises(ValueError, match="public_signal_reference"):
        signal(public_signal_reference="https://example.com/live?wallet=0xabc")
    with pytest.raises(TypeError, match="input signal"):
        report((object(),))
    with pytest.raises(TypeError, match="config"):
        build_market_research_business_inventories_surprise_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )


def test_business_inventories_surprise_digest_rejects_each_false_report_only_flag() -> None:
    summary = report((signal(source_count=d("1.000000")),))
    row = summary.rows[0]
    reason_count = summary.reason_code_counts[0]

    false_flag_cases = (
        lambda: config(paper_only=False),
        lambda: config(report_only=False),
        lambda: config(readonly=False),
        lambda: signal(paper_only=False),
        lambda: signal(report_only=False),
        lambda: signal(readonly=False),
        lambda: replace(row, paper_only=False),
        lambda: replace(row, report_only=False),
        lambda: replace(row, readonly=False),
        lambda: replace(reason_count, paper_only=False),
        lambda: replace(reason_count, report_only=False),
        lambda: replace(reason_count, readonly=False),
        lambda: replace(summary, paper_only=False),
        lambda: replace(summary, report_only=False),
        lambda: replace(summary, readonly=False),
    )

    for make_invalid_record in false_flag_cases:
        with pytest.raises(ValueError, match="must be True"):
            make_invalid_record()


def test_business_inventories_surprise_digest_rejects_incoherent_manual_constructors() -> None:
    summary = report(
        (
            signal(
                "condition_retail",
                research_key="research.business_inventories.retail",
                release_key="business_inventories.retail",
                inventory_segment="retail",
                observed_at=GENERATED_AT - timedelta(hours=3),
                expected_inventory_mom=d("0.400000"),
                actual_inventory_mom=d("-0.100000"),
                surprise_score=d("0.080000"),
                source_count=d("1.000000"),
                revision_ratio=d("0.200000"),
                confirmation_ratio=d("0.520000"),
                base_confidence=d("0.880000"),
            ),
            signal(
                "condition_total",
                research_key="research.business_inventories.total",
                release_key="business_inventories.total",
                inventory_segment="total",
            ),
        ),
    )
    ready = summary.rows[1]

    with pytest.raises(ValueError, match="surprise_delta"):
        replace(ready, surprise_delta=d("9.000000"))
    with pytest.raises(ValueError, match="digest_status"):
        replace(ready, digest_status="blocked")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_business_inventories_surprise_digest_ready",
                "market_research_business_inventories_surprise_digest_material_surprise",
            ),
        )
    with pytest.raises(ValueError, match="redacted_public_signal_reference"):
        replace(
            ready,
            redacted_public_signal_reference="https://host.example/feed?token=secret",
        )

    with pytest.raises(ValueError, match="ready_signal_count"):
        replace(summary, ready_signal_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        replace(summary, rows=tuple(reversed(summary.rows)))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            summary,
            reason_code_counts=tuple(reversed(summary.reason_code_counts)),
        )


def test_business_inventories_surprise_digest_has_no_durable_or_live_trading_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_business_inventories_surprise_digest.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))

    forbidden_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "web3",
        "clob_client",
    }
    forbidden_attr_names = {
        "open",
        "connect",
        "request",
        "get",
        "post",
        "put",
        "delete",
        "wallet",
        "auth",
        "order",
        "trade",
        "submit",
        "cancel",
        "replace",
    }
    forbidden_text_fragments = (
        "wallet",
        "auth",
        "order",
        "trade",
        "submit",
        "cancel",
        "replace",
        "network",
        "database",
        "persist",
        "durable",
        "postgres",
        "sqlite",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
        if isinstance(node, ast.Attribute):
            assert node.attr.lower() not in forbidden_attr_names
        if isinstance(node, ast.Name):
            assert node.id.lower() not in forbidden_attr_names
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
            if isinstance(node.value, str):
                lowered = node.value.lower()
                for fragment in forbidden_text_fragments:
                    assert fragment not in lowered
