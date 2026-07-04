from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.market_research_bank_stress_credit_digest"
GENERATED_AT = datetime(2026, 7, 3, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_MARKET_RESEARCH_BANK_STRESS_CREDIT_DIGEST_CONFIG_VERSION
        ),
        "max_signal_age_seconds": d("7200.000000"),
        "deposit_outflow_watch_ratio": d("0.030000"),
        "deposit_outflow_block_ratio": d("0.080000"),
        "credit_spread_watch_bps": d("50.000000"),
        "credit_spread_block_bps": d("125.000000"),
        "min_capital_buffer_ratio": d("0.070000"),
        "funding_pressure_watch_ratio": d("0.650000"),
        "min_source_count": d("2.000000"),
        "confidence_decay_per_reason": d("0.100000"),
    }
    values.update(overrides)
    return module.MarketResearchBankStressCreditDigestConfig(**values)


def signal(
    condition_id: str = "condition.bank.ready",
    *,
    research_key: str = "research.bank_stress.ready",
    bank_segment: str = "regional_banks",
    public_signal_reference: str = "public-bank-stress-note",
    observed_at: datetime | None = None,
    deposit_outflow_ratio: Decimal = d("0.010000"),
    credit_spread_widening_bps: Decimal = d("15.000000"),
    capital_buffer_ratio: Decimal = d("0.120000"),
    funding_pressure_ratio: Decimal = d("0.250000"),
    source_count: Decimal = d("3.000000"),
    base_confidence: Decimal = d("0.850000"),
    signal_config_version: str = "bank-stress-credit-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.MarketResearchBankStressCreditDigestSignal(
        condition_id=condition_id,
        research_key=research_key,
        bank_segment=bank_segment,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        deposit_outflow_ratio=deposit_outflow_ratio,
        credit_spread_widening_bps=credit_spread_widening_bps,
        capital_buffer_ratio=capital_buffer_ratio,
        funding_pressure_ratio=funding_pressure_ratio,
        source_count=source_count,
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
) -> Any:
    module = api()
    return module.build_market_research_bank_stress_credit_digest(
        signals,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_bank_stress_credit_digest_reduces_and_sorts_deterministically() -> None:
    module = api()
    summary = report(
        (
            signal(
                "condition.watch",
                research_key="research.bank_stress.money_center",
                bank_segment="money_center",
                public_signal_reference="public-money-center-note",
                deposit_outflow_ratio=d("0.040000"),
                credit_spread_widening_bps=d("75.000000"),
                capital_buffer_ratio=d("0.090000"),
                funding_pressure_ratio=d("0.300000"),
                source_count=d("3.000000"),
                base_confidence=d("0.780000"),
            ),
            signal("condition.ready"),
            signal(
                "condition.blocked",
                research_key="research.bank_stress.regional",
                bank_segment="regional_bank_stress",
                public_signal_reference="https://credit.example/banks?token=secret-123",
                observed_at=GENERATED_AT - timedelta(hours=3),
                deposit_outflow_ratio=d("0.100000"),
                credit_spread_widening_bps=d("150.000000"),
                capital_buffer_ratio=d("0.050000"),
                funding_pressure_ratio=d("0.800000"),
                source_count=d("1.000000"),
                base_confidence=d("0.900000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, module.MarketResearchBankStressCreditDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        module.DEFAULT_MARKET_RESEARCH_BANK_STRESS_CREDIT_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_bank_stress_credit_digest"
    )
    assert summary.signal_count == d("3.000000")
    assert summary.ready_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("0.000000")
    assert summary.blocked_signal_count == d("2.000000")
    assert summary.deposit_flight_signal_count == d("2.000000")
    assert summary.credit_stress_signal_count == d("2.000000")
    assert summary.capital_buffer_thin_signal_count == d("1.000000")
    assert summary.funding_pressure_signal_count == d("1.000000")
    assert summary.stale_signal_count == d("1.000000")
    assert summary.thin_source_signal_count == d("1.000000")
    assert summary.average_deposit_outflow_ratio == d("0.050000")
    assert summary.average_credit_spread_widening_bps == d("80.000000")
    assert summary.min_capital_buffer_ratio == d("0.050000")
    assert summary.max_funding_pressure_ratio == d("0.800000")
    assert summary.average_final_confidence == d("0.576667")
    assert summary.max_signal_age_seconds == d("10800.000000")
    assert tuple(row.condition_id for row in summary.rows) == (
        "condition.blocked",
        "condition.watch",
        "condition.ready",
    )

    blocked = summary.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.signal_age_seconds == d("10800.000000")
    assert blocked.confidence_decay_factor == d("0.600000")
    assert blocked.final_confidence == d("0.300000")
    assert blocked.redacted_public_signal_reference == "sha256:a1991b3d6d24"
    assert blocked.reason_codes == (
        "market_research_bank_stress_credit_digest_deposit_flight",
        "market_research_bank_stress_credit_digest_credit_stress",
        "market_research_bank_stress_credit_digest_capital_buffer_thin",
        "market_research_bank_stress_credit_digest_funding_pressure",
        "market_research_bank_stress_credit_digest_stale_signal",
        "market_research_bank_stress_credit_digest_thin_sources",
    )

    watched = summary.rows[1]
    assert watched.digest_status == "blocked"
    assert watched.confidence_decay_factor == d("0.200000")
    assert watched.final_confidence == d("0.580000")
    assert watched.reason_codes == (
        "market_research_bank_stress_credit_digest_deposit_flight",
        "market_research_bank_stress_credit_digest_credit_stress",
    )

    ready = summary.rows[2]
    assert ready.digest_status == "ready"
    assert ready.final_confidence == d("0.850000")
    assert ready.redacted_public_signal_reference == "public-bank-stress-note"
    assert ready.reason_codes == ("market_research_bank_stress_credit_digest_ready",)

    assert summary.reason_code_counts == (
        module.MarketResearchBankStressCreditDigestReasonCodeCount(
            reason_code="market_research_bank_stress_credit_digest_deposit_flight",
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        module.MarketResearchBankStressCreditDigestReasonCodeCount(
            reason_code="market_research_bank_stress_credit_digest_credit_stress",
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        module.MarketResearchBankStressCreditDigestReasonCodeCount(
            reason_code="market_research_bank_stress_credit_digest_capital_buffer_thin",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchBankStressCreditDigestReasonCodeCount(
            reason_code="market_research_bank_stress_credit_digest_funding_pressure",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchBankStressCreditDigestReasonCodeCount(
            reason_code="market_research_bank_stress_credit_digest_stale_signal",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchBankStressCreditDigestReasonCodeCount(
            reason_code="market_research_bank_stress_credit_digest_thin_sources",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchBankStressCreditDigestReasonCodeCount(
            reason_code="market_research_bank_stress_credit_digest_ready",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        count.reason_code for count in summary.reason_code_counts
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    public = repr(asdict(summary)).lower()
    for token in (
        "https://",
        "token=",
        "secret",
        "credit.example",
        "wallet",
        "account",
        "order",
        "cancel",
        "replace",
    ):
        assert token not in public


def test_empty_digest_is_blocked_report_only_with_decimal_zeroes() -> None:
    module = api()
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_bank_stress_credit_digest"
    )
    assert summary.signal_count == ZERO
    assert summary.rows == ()
    assert summary.average_deposit_outflow_ratio is None
    assert summary.average_credit_spread_widening_bps is None
    assert summary.min_capital_buffer_ratio is None
    assert summary.max_funding_pressure_ratio is None
    assert summary.average_final_confidence is None
    assert summary.max_signal_age_seconds is None
    assert summary.reason_code_counts == (
        module.MarketResearchBankStressCreditDigestReasonCodeCount(
            reason_code="market_research_bank_stress_credit_digest_no_inputs",
            count=ZERO,
            signal_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == ("market_research_bank_stress_credit_digest_no_inputs",)
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_dataclasses_are_frozen_hard_flagged_and_decimal_only() -> None:
    module = api()
    cfg = config()
    source = signal(observed_at=datetime(2026, 7, 3, 11, 30, tzinfo=timezone.utc))
    summary = report((source,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        source.source_count = d("4.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].final_confidence = d("0.500000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.signal_count = d("2.000000")  # type: ignore[misc]

    assert source.observed_at.tzinfo is UTC
    assert summary.rows[0].observed_at.tzinfo is UTC
    assert summary.generated_at.tzinfo is UTC

    for public_type in (
        module.MarketResearchBankStressCreditDigestConfig,
        module.MarketResearchBankStressCreditDigestSignal,
        module.MarketResearchBankStressCreditDigestRow,
        module.MarketResearchBankStressCreditDigestReasonCodeCount,
        module.MarketResearchBankStressCreditDigestReport,
    ):
        assert is_dataclass(public_type)
        assert all("float" not in str(field.type) for field in fields(public_type))
        assert all("int" not in str(field.type) and field.type is not int for field in fields(public_type))

    numeric_public_fragments = {
        "seconds",
        "ratio",
        "bps",
        "count",
        "confidence",
    }
    for item in (cfg, source, summary, summary.rows[0], summary.reason_code_counts[0]):
        for field_name, value in asdict(item).items():
            if field_name in {"reason_code_counts", "reason_codes", "rows"}:
                continue
            if any(fragment in field_name for fragment in numeric_public_fragments) and value is not None:
                assert type(value) is Decimal, (field_name, type(value))
                assert value.as_tuple().exponent == -6

    with pytest.raises(ValueError, match="paper_only"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)


@pytest.mark.parametrize(
    ("factory", "message"),
    (
        (lambda: config(max_signal_age_seconds=_DecimalSubclass("1.000000")), "Decimal"),
        (lambda: config(min_source_count=2), "Decimal"),
        (lambda: config(deposit_outflow_block_ratio=d("0.010000")), "exceed"),
        (lambda: signal(deposit_outflow_ratio=d("1.500000")), "deposit_outflow_ratio"),
        (lambda: signal(credit_spread_widening_bps=50), "credit_spread_widening_bps"),
        (lambda: signal(source_count=d("-1.000000")), "source_count"),
        (lambda: signal(bank_segment=_StringSubclass("regional")), "bank_segment"),
        (lambda: signal(observed_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC)), "observed_at"),
        (lambda: signal(public_signal_reference="wallet source"), "public_signal_reference"),
    ),
)
def test_validates_inputs(factory: object, message: str) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        factory()


def test_rejects_subclasses_duplicates_future_rows_and_inconsistent_reports() -> None:
    module = api()

    with pytest.raises(TypeError, match="subclassing"):
        type("ConfigSubclass", (module.MarketResearchBankStressCreditDigestConfig,), {})
    with pytest.raises(TypeError, match="subclassing"):
        type("SignalSubclass", (module.MarketResearchBankStressCreditDigestSignal,), {})

    with pytest.raises(ValueError, match="timezone-aware"):
        report((signal(),), generated_at=datetime(2026, 7, 3, 16, 0))

    with pytest.raises(ValueError, match="after generated_at"):
        report((signal(observed_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="duplicate"):
        report((signal("condition.duplicate"), signal("condition.duplicate")))

    good = report((signal(),))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(good, reason_codes=("unexpected",))
    with pytest.raises(ValueError, match="signal_count"):
        replace(good, signal_count=d("99.000000"))


def test_payload_uses_decimal_strings_iso_datetimes_and_no_float_values() -> None:
    module = api()
    summary = report(
        (
            signal(
                observed_at=datetime(2026, 7, 3, 15, 59, 59, 500000, tzinfo=UTC),
            ),
        ),
    )
    payload = module.market_research_bank_stress_credit_digest_payload(summary)

    assert payload == module.market_research_bank_stress_credit_digest_payload(summary)
    assert payload["generated_at"] == "2026-07-03T16:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["signal_count"] == "1.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-03T15:59:59.500000+00:00"
    assert payload["rows"][0]["signal_age_seconds"] == "0.500000"
    assert_no_float_values(payload)
    assert module.market_research_bank_stress_credit_digest_payload(payload) == payload

    with pytest.raises(ValueError, match="report"):
        module.market_research_bank_stress_credit_digest_payload(object())


def test_module_scope_is_pure_report_only_and_has_no_forbidden_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_research_bank_stress_credit_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "order",
        "cancel",
        "replace",
        "exchange mutation",
        "private_key",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite",
        "database",
        "durable",
        "store",
        "open(",
        "live trading",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_import_roots = {
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "supabase",
        "web3",
        "pathlib",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
        "float",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            call = node.func
            if isinstance(call, ast.Name):
                assert call.id not in forbidden_call_names
            elif isinstance(call, ast.Attribute):
                assert call.attr not in forbidden_call_names


def assert_no_float_values(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"float found in payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)
