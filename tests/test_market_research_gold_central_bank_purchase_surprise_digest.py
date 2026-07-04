from __future__ import annotations

import ast
import hashlib
import importlib
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def module() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_gold_central_bank_purchase_surprise_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def redacted(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()[:12]}"


def config(**overrides: object) -> object:
    mod = module()
    values = {
        "config_version": (
            mod
            .DEFAULT_MARKET_RESEARCH_GOLD_CENTRAL_BANK_PURCHASE_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "max_report_age_seconds": d("7200.000000"),
        "max_reporting_lag_seconds": d("86400.000000"),
        "min_purchase_surprise_tonnage_abs": d("5.000000"),
        "min_reserve_revision_tonnage_abs": d("1.000000"),
        "min_confirmation_source_count": d("2.000000"),
        "min_fx_reserve_share_pressure": d("0.050000"),
        "min_commodity_event_alignment_score": d("0.550000"),
        "watch_confidence_threshold": d("0.650000"),
        "confidence_decay_per_gap": d("0.100000"),
    }
    values.update(overrides)
    return mod.MarketResearchGoldCentralBankPurchaseSurpriseDigestConfig(**values)


def signal(
    surprise_key: str = "gold.purchase.nbpl.ready",
    *,
    condition_id: str = "condition_gold_purchase_ready",
    central_bank: str = "nbpl",
    public_report_reference: str = "official-sector-public-gold-reserve-note",
    observed_at: datetime | None = None,
    reporting_lag_seconds: Decimal = d("3600.000000"),
    reported_purchase_tonnage: Decimal = d("14.000000"),
    expected_purchase_tonnage: Decimal = d("8.000000"),
    reserve_revision_tonnage_abs: Decimal = d("1.500000"),
    confirmation_source_count: Decimal = d("3.000000"),
    fx_reserve_share_pressure: Decimal = d("0.090000"),
    commodity_event_alignment_score: Decimal = d("0.750000"),
    base_confidence: Decimal = d("0.840000"),
    signal_config_version: str = "gold-purchase-surprise-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> object:
    mod = module()
    return mod.MarketResearchGoldCentralBankPurchaseSurpriseDigestSignal(
        surprise_key=surprise_key,
        condition_id=condition_id,
        central_bank=central_bank,
        public_report_reference=public_report_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        reporting_lag_seconds=reporting_lag_seconds,
        reported_purchase_tonnage=reported_purchase_tonnage,
        expected_purchase_tonnage=expected_purchase_tonnage,
        reserve_revision_tonnage_abs=reserve_revision_tonnage_abs,
        confirmation_source_count=confirmation_source_count,
        fx_reserve_share_pressure=fx_reserve_share_pressure,
        commodity_event_alignment_score=commodity_event_alignment_score,
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
) -> object:
    mod = module()
    return mod.build_market_research_gold_central_bank_purchase_surprise_digest(
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


def test_gold_central_bank_purchase_surprise_reduces_signals_redacts_and_sorts() -> None:
    mod = module()

    summary = report(
        (
            signal(
                "gold.purchase.pboc.blocked",
                condition_id="condition_gold_purchase_blocked",
                central_bank="pboc",
                public_report_reference=(
                    "https://gold.example/central-bank-purchase?token=secret-123"
                ),
                observed_at=GENERATED_AT - timedelta(hours=3),
                reporting_lag_seconds=d("200000.000000"),
                reported_purchase_tonnage=d("4.000000"),
                expected_purchase_tonnage=d("6.000000"),
                reserve_revision_tonnage_abs=d("0.500000"),
                confirmation_source_count=d("1.000000"),
                fx_reserve_share_pressure=d("0.010000"),
                commodity_event_alignment_score=d("0.400000"),
                base_confidence=d("0.900000"),
            ),
            signal(
                "gold.purchase.snb.watch",
                condition_id="condition_gold_purchase_watch",
                central_bank="snb",
                public_report_reference="wallet://private/snb-gold-purchase-note",
                reported_purchase_tonnage=d("15.000000"),
                expected_purchase_tonnage=d("6.000000"),
                reserve_revision_tonnage_abs=d("1.200000"),
                confirmation_source_count=d("3.000000"),
                fx_reserve_share_pressure=d("0.080000"),
                commodity_event_alignment_score=d("0.500000"),
                base_confidence=d("0.760000"),
            ),
            signal(
                "gold.purchase.nbpl.ready",
                condition_id="condition_gold_purchase_ready",
                central_bank="nbpl",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert isinstance(
        summary,
        mod.MarketResearchGoldCentralBankPurchaseSurpriseDigestReport,
    )
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        mod
        .DEFAULT_MARKET_RESEARCH_GOLD_CENTRAL_BANK_PURCHASE_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_gold_central_bank_purchase_surprise_digest"
    )
    assert summary.signal_count == d("3.000000")
    assert summary.ready_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("1.000000")
    assert summary.blocked_signal_count == d("1.000000")
    assert summary.stale_report_signal_count == d("1.000000")
    assert summary.reporting_lag_signal_count == d("1.000000")
    assert summary.confirmation_source_gap_signal_count == d("1.000000")
    assert summary.purchase_surprise_gap_signal_count == d("1.000000")
    assert summary.reserve_revision_gap_signal_count == d("1.000000")
    assert summary.fx_reserve_share_pressure_gap_signal_count == d("1.000000")
    assert summary.commodity_alignment_gap_signal_count == d("2.000000")
    assert summary.total_confidence_decay == d("0.800000")
    assert summary.average_final_confidence == d("0.566667")
    assert summary.average_purchase_surprise_tonnage_abs == d("5.666667")
    assert summary.average_reserve_revision_tonnage_abs == d("1.066667")
    assert summary.average_fx_reserve_share_pressure == d("0.060000")
    assert summary.average_commodity_event_alignment_score == d("0.550000")
    assert summary.max_observed_signal_age_seconds == d("10800.000000")
    assert tuple(row.surprise_key for row in summary.rows) == (
        "gold.purchase.pboc.blocked",
        "gold.purchase.snb.watch",
        "gold.purchase.nbpl.ready",
    )

    blocked = summary.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.signal_age_seconds == d("10800.000000")
    assert blocked.purchase_surprise_direction == "below_consensus"
    assert blocked.purchase_surprise_tonnage_abs == d("2.000000")
    assert blocked.confidence_decay_factor == d("0.700000")
    assert blocked.final_confidence == d("0.200000")
    assert blocked.redacted_public_report_reference == redacted(
        "https://gold.example/central-bank-purchase?token=secret-123",
    )
    assert blocked.reason_codes == (
        "market_research_gold_central_bank_purchase_surprise_digest_"
        "stale_report_signal",
        "market_research_gold_central_bank_purchase_surprise_digest_"
        "reporting_lag",
        "market_research_gold_central_bank_purchase_surprise_digest_"
        "confirmation_source_gap",
        "market_research_gold_central_bank_purchase_surprise_digest_"
        "purchase_surprise_gap",
        "market_research_gold_central_bank_purchase_surprise_digest_"
        "reserve_revision_gap",
        "market_research_gold_central_bank_purchase_surprise_digest_"
        "fx_reserve_share_pressure_gap",
        "market_research_gold_central_bank_purchase_surprise_digest_"
        "commodity_alignment_gap",
    )

    watched = summary.rows[1]
    assert watched.digest_status == "watch"
    assert watched.purchase_surprise_direction == "above_consensus"
    assert watched.purchase_surprise_tonnage_abs == d("9.000000")
    assert watched.confidence_decay_factor == d("0.100000")
    assert watched.final_confidence == d("0.660000")
    assert watched.redacted_public_report_reference == redacted(
        "wallet://private/snb-gold-purchase-note",
    )
    assert watched.reason_codes == (
        "market_research_gold_central_bank_purchase_surprise_digest_"
        "commodity_alignment_gap",
    )

    ready = summary.rows[2]
    assert ready.digest_status == "ready"
    assert ready.purchase_surprise_direction == "above_consensus"
    assert ready.final_confidence == d("0.840000")
    assert ready.redacted_public_report_reference == (
        "official-sector-public-gold-reserve-note"
    )
    assert ready.reason_codes == (
        "market_research_gold_central_bank_purchase_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        mod.MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_central_bank_purchase_surprise_digest_"
                "fx_reserve_share_pressure_gap"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        mod.MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_central_bank_purchase_surprise_digest_"
                "commodity_alignment_gap"
            ),
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        mod.MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_central_bank_purchase_surprise_digest_"
                "stale_report_signal"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        mod.MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_central_bank_purchase_surprise_digest_"
                "reporting_lag"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        mod.MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_central_bank_purchase_surprise_digest_"
                "confirmation_source_gap"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        mod.MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_central_bank_purchase_surprise_digest_"
                "purchase_surprise_gap"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        mod.MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_central_bank_purchase_surprise_digest_"
                "reserve_revision_gap"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        mod.MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_central_bank_purchase_surprise_digest_ready"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.signal_config_versions == (
        ("gold.purchase.nbpl.ready", "gold-purchase-surprise-source-v0"),
        ("gold.purchase.pboc.blocked", "gold-purchase-surprise-source-v0"),
        ("gold.purchase.snb.watch", "gold-purchase-surprise-source-v0"),
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
        "private/snb-gold-purchase-note",
        "auth",
        "broker",
        "order",
        "cancel",
        "replace",
        "exchange",
        "token",
        "secret",
        "private",
    ):
        assert token not in public


def test_gold_central_bank_purchase_surprise_empty_inputs_are_blocked() -> None:
    mod = module()

    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_gold_central_bank_purchase_surprise_digest"
    )
    assert summary.signal_count == ZERO
    assert summary.ready_signal_count == ZERO
    assert summary.watch_signal_count == ZERO
    assert summary.blocked_signal_count == ZERO
    assert summary.average_final_confidence == ZERO
    assert summary.average_purchase_surprise_tonnage_abs == ZERO
    assert summary.average_reserve_revision_tonnage_abs == ZERO
    assert summary.average_fx_reserve_share_pressure == ZERO
    assert summary.average_commodity_event_alignment_score == ZERO
    assert summary.max_observed_signal_age_seconds == ZERO
    assert summary.rows == ()
    assert summary.signal_config_versions == ()
    assert summary.reason_code_counts == (
        mod.MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_central_bank_purchase_surprise_digest_no_inputs"
            ),
            count=d("1.000000"),
            signal_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_gold_central_bank_purchase_surprise_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_gold_central_bank_purchase_surprise_validates_contracts_payload_and_no_io() -> None:
    mod = module()

    assert (
        mod.MarketResearchGoldCentralBankPurchaseSurpriseDigestConfig
        .__dataclass_params__
        .frozen
    )
    assert (
        mod.MarketResearchGoldCentralBankPurchaseSurpriseDigestSignal
        .__dataclass_params__
        .frozen
    )
    assert (
        mod.MarketResearchGoldCentralBankPurchaseSurpriseDigestRow
        .__dataclass_params__
        .frozen
    )
    assert (
        mod.MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount
        .__dataclass_params__
        .frozen
    )
    assert (
        mod.MarketResearchGoldCentralBankPurchaseSurpriseDigestReport
        .__dataclass_params__
        .frozen
    )

    with pytest.raises(FrozenInstanceError):
        signal().paper_only = False  # type: ignore[misc]
    with pytest.raises(ValueError, match="config_version"):
        config(
            config_version=_StringSubclass(
                mod
                .DEFAULT_MARKET_RESEARCH_GOLD_CENTRAL_BANK_PURCHASE_SURPRISE_DIGEST_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="max_report_age_seconds"):
        config(max_report_age_seconds=_DecimalSubclass("7200.000000"))
    with pytest.raises(ValueError, match="min_fx_reserve_share_pressure"):
        config(min_fx_reserve_share_pressure=0.05)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_confirmation_source_count"):
        config(min_confirmation_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="surprise_key"):
        signal(_StringSubclass("gold.purchase.bad"))
    with pytest.raises(ValueError, match="central_bank"):
        signal(central_bank="broker-feed")
    with pytest.raises(ValueError, match="public_report_reference"):
        signal(public_report_reference=" ")
    with pytest.raises(ValueError, match="observed_at"):
        signal(observed_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (signal(),),
            generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="reported_purchase_tonnage"):
        signal(reported_purchase_tonnage=Decimal("NaN"))
    with pytest.raises(ValueError, match="confirmation_source_count"):
        signal(confirmation_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="fx_reserve_share_pressure"):
        signal(fx_reserve_share_pressure=d("1.100000"))
    with pytest.raises(ValueError, match="paper_only"):
        signal(paper_only=False)

    with pytest.raises(TypeError, match="does not support subclassing"):
        type(
            "BadConfig",
            (mod.MarketResearchGoldCentralBankPurchaseSurpriseDigestConfig,),
            {},
        )

    base = signal()
    with pytest.raises(ValueError, match="duplicate surprise_key"):
        mod.build_market_research_gold_central_bank_purchase_surprise_digest(
            (base, base),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        mod.build_market_research_gold_central_bank_purchase_surprise_digest(
            (base,),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="future"):
        report((signal(observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="report"):
        mod.market_research_gold_central_bank_purchase_surprise_digest_payload(
            object(),
        )

    ready = report((base,)).rows[0]
    with pytest.raises(ValueError, match="final_confidence"):
        replace(ready, final_confidence=d("0.500000"))
    with pytest.raises(ValueError, match="redacted_public_report_reference"):
        replace(
            ready,
            redacted_public_report_reference="https://host?token=secret",
        )
    unordered = report((signal("gold.purchase.z"), signal("gold.purchase.a")))
    with pytest.raises(ValueError, match="rows"):
        replace(unordered, rows=tuple(reversed(unordered.rows)))
    with pytest.raises(ValueError, match="signal_config_versions"):
        replace(
            report((base,)),
            signal_config_versions=(
                (
                    "gold.purchase.other",
                    "gold-purchase-surprise-source-v0",
                ),
            ),
        )

    payload = mod.market_research_gold_central_bank_purchase_surprise_digest_payload(
        report((base,)),
    )
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["signal_count"] == "1.000000"
    assert payload["rows"][0]["purchase_surprise_tonnage_abs"] == "6.000000"
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

    source = mod.__loader__.get_source(mod.__name__)
    assert source is not None
    lowered_source = source.lower()
    for token in (
        "live_trading",
        "auth",
        "keys",
        "private_key",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "exchange",
        "requests",
        "http",
        "socket",
        "subprocess",
        "pathlib",
        "psycopg",
        "supabase",
    ):
        assert token not in lowered_source

    tree = ast.parse(source)
    forbidden_import_roots = {
        "asyncio",
        "http",
        "httpx",
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
    forbidden_calls = {
        "__import__",
        "compile",
        "connect",
        "eval",
        "exec",
        "open",
        "request",
        "run",
        "urlopen",
        "Popen",
    }
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


def test_gold_central_bank_purchase_surprise_public_numeric_fields_are_decimals() -> None:
    mod = module()
    summary = report((signal(),))

    assert_decimal_numeric_fields(config())
    assert_decimal_numeric_fields(signal())
    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(
        mod.MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_central_bank_purchase_surprise_digest_ready"
            ),
            count=d("1.000000"),
            signal_ratio=d("1.000000"),
        ),
    )


def assert_decimal_numeric_fields(value: object) -> None:
    numeric_name_fragments = (
        "age",
        "alignment",
        "confidence",
        "count",
        "expected",
        "lag",
        "pressure",
        "reported",
        "revision",
        "score",
        "share",
        "tonnage",
    )
    for field in fields(value):
        if any(fragment in field.name for fragment in numeric_name_fragments):
            field_value = getattr(value, field.name)
            if isinstance(field_value, datetime):
                continue
            if isinstance(field_value, tuple):
                continue
            if field_value is None:
                continue
            assert type(field_value) is Decimal, field.name
