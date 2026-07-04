from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_gold_vault_flow_digest.py",
)
MODULE_NAME = "polymarket_alpha_lab.market_research_gold_vault_flow_digest"
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_MARKET_RESEARCH_GOLD_VAULT_FLOW_DIGEST_CONFIG_VERSION
        ),
        "max_flow_age_seconds": d("7200.000000"),
        "min_flow_tonnage_abs": d("3.000000"),
        "min_confirmation_source_count": d("2.000000"),
        "min_inventory_pressure_score": d("0.550000"),
        "min_delivery_alignment_score": d("0.500000"),
        "max_stale_source_ratio": d("0.250000"),
        "watch_confidence_threshold": d("0.650000"),
        "confidence_decay_per_gap": d("0.100000"),
    }
    values.update(overrides)
    return module.MarketResearchGoldVaultFlowDigestConfig(**values)


def signal(
    vault_flow_key: str = "gold.vault.ready",
    *,
    condition_id: str = "condition_gold_vault_ready",
    vault_venue: str = "comex",
    flow_direction: str = "inflow",
    public_signal_reference: str = "vault-flow-public-note",
    observed_at: datetime | None = None,
    flow_tonnage_abs: Decimal = d("8.000000"),
    confirmation_source_count: Decimal = d("3.000000"),
    inventory_pressure_score: Decimal = d("0.780000"),
    delivery_alignment_score: Decimal = d("0.760000"),
    stale_source_ratio: Decimal = d("0.050000"),
    base_confidence: Decimal = d("0.840000"),
    signal_config_version: str = "gold-vault-flow-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.MarketResearchGoldVaultFlowDigestSignal(
        vault_flow_key=vault_flow_key,
        condition_id=condition_id,
        vault_venue=vault_venue,
        flow_direction=flow_direction,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        flow_tonnage_abs=flow_tonnage_abs,
        confirmation_source_count=confirmation_source_count,
        inventory_pressure_score=inventory_pressure_score,
        delivery_alignment_score=delivery_alignment_score,
        stale_source_ratio=stale_source_ratio,
        base_confidence=base_confidence,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    signals: tuple[object, ...],
    *,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_market_research_gold_vault_flow_digest(
        signals,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_public_float_or_int(value: Any) -> None:
    if type(value) in (float, int):
        pytest.fail(f"found public numeric that is not a Decimal string: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_float_or_int(item)


def test_gold_vault_flow_digest_reduces_signals_redacts_and_sorts() -> None:
    module = api()

    summary = report(
        (
            signal(
                "gold.vault.comex.blocked",
                condition_id="condition_gold_vault_blocked",
                vault_venue="comex",
                public_signal_reference=(
                    "https://gold.example/vault-flow?token=secret-123"
                ),
                observed_at=GENERATED_AT - timedelta(hours=3),
                flow_tonnage_abs=d("1.500000"),
                confirmation_source_count=d("1.000000"),
                inventory_pressure_score=d("0.300000"),
                delivery_alignment_score=d("0.400000"),
                stale_source_ratio=d("0.400000"),
                base_confidence=d("0.900000"),
            ),
            signal(
                "gold.vault.lbma.watch",
                condition_id="condition_gold_vault_watch",
                vault_venue="lbma",
                flow_direction="outflow",
                public_signal_reference="wallet://private/lbma-vault-flow-note",
                flow_tonnage_abs=d("5.000000"),
                confirmation_source_count=d("3.000000"),
                inventory_pressure_score=d("0.500000"),
                delivery_alignment_score=d("0.700000"),
                stale_source_ratio=d("0.100000"),
                base_confidence=d("0.760000"),
            ),
            signal(
                "gold.vault.etf.ready",
                condition_id="condition_gold_vault_ready",
                vault_venue="etf",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, module.MarketResearchGoldVaultFlowDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        module.DEFAULT_MARKET_RESEARCH_GOLD_VAULT_FLOW_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_gold_vault_flow_digest"
    )
    assert summary.signal_count == d("3.000000")
    assert summary.ready_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("1.000000")
    assert summary.blocked_signal_count == d("1.000000")
    assert summary.stale_vault_flow_signal_count == d("1.000000")
    assert summary.thin_confirmation_signal_count == d("1.000000")
    assert summary.low_flow_tonnage_signal_count == d("1.000000")
    assert summary.inventory_pressure_gap_signal_count == d("2.000000")
    assert summary.delivery_alignment_gap_signal_count == d("1.000000")
    assert summary.stale_source_signal_count == d("1.000000")
    assert summary.total_confidence_decay == d("0.700000")
    assert summary.average_final_confidence == d("0.600000")
    assert summary.average_flow_tonnage_abs == d("4.833333")
    assert summary.average_inventory_pressure_score == d("0.526667")
    assert summary.average_delivery_alignment_score == d("0.620000")
    assert summary.max_observed_signal_age_seconds == d("10800.000000")
    assert tuple(row.vault_flow_key for row in summary.rows) == (
        "gold.vault.comex.blocked",
        "gold.vault.lbma.watch",
        "gold.vault.etf.ready",
    )

    blocked = summary.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.signal_age_seconds == d("10800.000000")
    assert blocked.confidence_decay_factor == d("0.600000")
    assert blocked.final_confidence == d("0.300000")
    assert blocked.redacted_public_signal_reference.startswith("sha256:")
    assert blocked.reason_codes == (
        "market_research_gold_vault_flow_digest_stale_vault_flow_signal",
        "market_research_gold_vault_flow_digest_thin_confirmation",
        "market_research_gold_vault_flow_digest_low_flow_tonnage",
        "market_research_gold_vault_flow_digest_inventory_pressure_gap",
        "market_research_gold_vault_flow_digest_delivery_alignment_gap",
        "market_research_gold_vault_flow_digest_stale_source_ratio",
    )

    watched = summary.rows[1]
    assert watched.digest_status == "watch"
    assert watched.confidence_decay_factor == d("0.100000")
    assert watched.final_confidence == d("0.660000")
    assert watched.redacted_public_signal_reference.startswith("sha256:")
    assert watched.reason_codes == (
        "market_research_gold_vault_flow_digest_inventory_pressure_gap",
    )

    ready = summary.rows[2]
    assert ready.digest_status == "ready"
    assert ready.final_confidence == d("0.840000")
    assert ready.redacted_public_signal_reference == "vault-flow-public-note"
    assert ready.reason_codes == ("market_research_gold_vault_flow_digest_ready",)

    assert summary.reason_code_counts == (
        module.MarketResearchGoldVaultFlowDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_vault_flow_digest_inventory_pressure_gap"
            ),
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        module.MarketResearchGoldVaultFlowDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_vault_flow_digest_stale_vault_flow_signal"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchGoldVaultFlowDigestReasonCodeCount(
            reason_code="market_research_gold_vault_flow_digest_thin_confirmation",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchGoldVaultFlowDigestReasonCodeCount(
            reason_code="market_research_gold_vault_flow_digest_low_flow_tonnage",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchGoldVaultFlowDigestReasonCodeCount(
            reason_code="market_research_gold_vault_flow_digest_delivery_alignment_gap",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchGoldVaultFlowDigestReasonCodeCount(
            reason_code="market_research_gold_vault_flow_digest_stale_source_ratio",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchGoldVaultFlowDigestReasonCodeCount(
            reason_code="market_research_gold_vault_flow_digest_ready",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.signal_config_versions == (
        ("gold.vault.comex.blocked", "gold-vault-flow-source-v0"),
        ("gold.vault.etf.ready", "gold-vault-flow-source-v0"),
        ("gold.vault.lbma.watch", "gold-vault-flow-source-v0"),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    public = repr(asdict(summary)).lower()
    for token in (
        "secret-123",
        "gold.example",
        "https://",
        "wallet://",
        "private/lbma-vault-flow-note",
        "auth",
        "broker",
        "signing",
        "submit",
        "cancel",
        "account",
        "advice",
        "network",
        "database",
        "token",
        "secret",
        "private",
    ):
        assert token not in public


def test_gold_vault_flow_empty_inputs_are_report_only_blocked() -> None:
    module = api()

    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_gold_vault_flow_digest"
    )
    assert summary.signal_count == ZERO
    assert summary.ready_signal_count == ZERO
    assert summary.watch_signal_count == ZERO
    assert summary.blocked_signal_count == ZERO
    assert summary.average_final_confidence == ZERO
    assert summary.average_flow_tonnage_abs == ZERO
    assert summary.average_inventory_pressure_score == ZERO
    assert summary.average_delivery_alignment_score == ZERO
    assert summary.max_observed_signal_age_seconds == ZERO
    assert summary.rows == ()
    assert summary.signal_config_versions == ()
    assert summary.reason_code_counts == (
        module.MarketResearchGoldVaultFlowDigestReasonCodeCount(
            reason_code="market_research_gold_vault_flow_digest_no_inputs",
            count=d("1.000000"),
            signal_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_gold_vault_flow_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_gold_vault_flow_validates_contracts_payload_and_no_io() -> None:
    module = api()

    assert module.MarketResearchGoldVaultFlowDigestConfig.__dataclass_params__.frozen
    assert module.MarketResearchGoldVaultFlowDigestSignal.__dataclass_params__.frozen
    assert module.MarketResearchGoldVaultFlowDigestRow.__dataclass_params__.frozen
    assert (
        module.MarketResearchGoldVaultFlowDigestReasonCodeCount
        .__dataclass_params__
        .frozen
    )
    assert module.MarketResearchGoldVaultFlowDigestReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        signal().paper_only = False  # type: ignore[misc]
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("gold-vault-flow-v0"))
    with pytest.raises(ValueError, match="max_flow_age_seconds"):
        config(max_flow_age_seconds=_DecimalSubclass("7200.000000"))
    with pytest.raises(ValueError, match="min_inventory_pressure_score"):
        config(min_inventory_pressure_score=0.55)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_confirmation_source_count"):
        config(min_confirmation_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="vault_flow_key"):
        signal(_StringSubclass("gold.vault.bad"))
    with pytest.raises(ValueError, match="vault_venue"):
        signal(vault_venue="broker-feed")
    with pytest.raises(ValueError, match="flow_direction"):
        signal(flow_direction="accumulation")
    with pytest.raises(ValueError, match="public_signal_reference"):
        signal(public_signal_reference=" ")
    with pytest.raises(ValueError, match="observed_at"):
        signal(observed_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (signal(),),
            generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="flow_tonnage_abs"):
        signal(flow_tonnage_abs=Decimal("NaN"))
    with pytest.raises(ValueError, match="confirmation_source_count"):
        signal(confirmation_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="inventory_pressure_score"):
        signal(inventory_pressure_score=d("1.100000"))
    with pytest.raises(ValueError, match="paper_only"):
        signal(paper_only=False)
    with pytest.raises(TypeError, match="does not support subclassing"):
        type("BadConfig", (module.MarketResearchGoldVaultFlowDigestConfig,), {})

    base = signal()
    with pytest.raises(ValueError, match="duplicate vault_flow_key"):
        module.build_market_research_gold_vault_flow_digest(
            (base, base),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        module.build_market_research_gold_vault_flow_digest(
            (base,),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="future"):
        report((signal(observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="report"):
        module.market_research_gold_vault_flow_digest_payload(object())

    payload = module.market_research_gold_vault_flow_digest_payload(report((base,)))
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["signal_count"] == "1.000000"
    assert payload["rows"][0]["final_confidence"] == "0.840000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_float_or_int(payload)

    public = repr(payload).lower()
    assert "datetime." not in public
    assert "decimal(" not in public
    assert "auth" not in public
    assert "wallet" not in public

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source.lower()
    for token in (
        "live_trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "exchange",
        "mutation",
        "private_key",
        "secret",
        "token",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
        "psycopg",
        "supabase",
        "web3",
    ):
        assert token not in lowered_source

    tree = ast.parse(source)
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
        "web3",
    }
    forbidden_calls = {"open", "connect", "request", "urlopen", "run", "Popen"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
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


def test_gold_vault_flow_validates_direct_report_consistency() -> None:
    summary = report((signal(),))

    with pytest.raises(ValueError, match="ready_signal_count"):
        replace(summary, ready_signal_count=d("2.000000"))
    with pytest.raises(ValueError, match="rows"):
        replace(summary, rows=())
    with pytest.raises(ValueError, match="reason_codes"):
        replace(summary, reason_codes=())
    with pytest.raises(ValueError, match="signal_count"):
        replace(summary, signal_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="report_only"):
        replace(summary, report_only=False)
