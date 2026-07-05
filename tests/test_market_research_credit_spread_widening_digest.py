from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 3, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _MissingOffsetTZ(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_credit_spread_widening_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_MARKET_RESEARCH_CREDIT_SPREAD_WIDENING_DIGEST_CONFIG_VERSION
        ),
        "max_signal_age_seconds": d("7200.000000"),
        "watch_widening_bps": d("25.000000"),
        "block_widening_bps": d("75.000000"),
        "min_source_family_count": d("3.000000"),
        "max_stale_source_ratio": d("0.250000"),
        "confidence_decay_per_gap": d("0.100000"),
        "watch_confidence_threshold": d("0.650000"),
    }
    values.update(overrides)
    return module.MarketResearchCreditSpreadWideningDigestConfig(**values)


def spread_signal(
    condition_id: str = "condition.credit.ready",
    *,
    credit_spread_key: str = "credit.ig.ready",
    issuer_or_index: str = "IG CDX",
    public_signal_reference: str = "public-credit-spread-note",
    observed_at: datetime | None = None,
    current_spread_bps: Decimal = d("118.000000"),
    prior_spread_bps: Decimal = d("105.000000"),
    spread_widening_bps: Decimal = d("13.000000"),
    source_family_count: Decimal = d("4.000000"),
    stale_source_ratio: Decimal = d("0.100000"),
    base_confidence: Decimal = d("0.860000"),
    signal_config_version: str = "credit-spread-widening-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.MarketResearchCreditSpreadWideningDigestSignal(
        condition_id=condition_id,
        credit_spread_key=credit_spread_key,
        issuer_or_index=issuer_or_index,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        current_spread_bps=current_spread_bps,
        prior_spread_bps=prior_spread_bps,
        spread_widening_bps=spread_widening_bps,
        source_family_count=source_family_count,
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
    return module.build_market_research_credit_spread_widening_digest(
        signals,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_credit_spread_widening_digest_reduces_signals_deterministically() -> None:
    module = api()
    summary = report(
        (
            spread_signal(
                "condition.watch",
                credit_spread_key="credit.hy.energy",
                issuer_or_index="HY Energy",
                public_signal_reference="wallet://private/credit-spread-note",
                spread_widening_bps=d("40.000000"),
                current_spread_bps=d("440.000000"),
                prior_spread_bps=d("400.000000"),
                source_family_count=d("3.000000"),
                stale_source_ratio=d("0.100000"),
                base_confidence=d("0.760000"),
            ),
            spread_signal(
                "condition.ready",
                credit_spread_key="credit.ig.ready",
                issuer_or_index="IG CDX",
            ),
            spread_signal(
                "condition.blocked",
                credit_spread_key="credit.hy.retail",
                issuer_or_index="HY Retail",
                public_signal_reference="https://credit.example/spreads?token=secret-123",
                observed_at=GENERATED_AT - timedelta(hours=3),
                current_spread_bps=d("520.000000"),
                prior_spread_bps=d("420.000000"),
                spread_widening_bps=d("100.000000"),
                source_family_count=d("2.000000"),
                stale_source_ratio=d("0.400000"),
                base_confidence=d("0.900000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )

    assert isinstance(summary, module.MarketResearchCreditSpreadWideningDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        module.DEFAULT_MARKET_RESEARCH_CREDIT_SPREAD_WIDENING_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_credit_spread_widening_digest"
    )
    assert summary.signal_count == d("3.000000")
    assert summary.ready_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("1.000000")
    assert summary.blocked_signal_count == d("1.000000")
    assert summary.stale_signal_count == d("1.000000")
    assert summary.watch_widening_signal_count == d("1.000000")
    assert summary.block_widening_signal_count == d("1.000000")
    assert summary.source_family_gap_signal_count == d("1.000000")
    assert summary.stale_source_signal_count == d("1.000000")
    assert summary.total_confidence_decay == d("0.500000")
    assert summary.average_final_confidence == d("0.673333")
    assert summary.average_spread_widening_bps == d("51.000000")
    assert summary.max_observed_signal_age_seconds == d("10800.000000")
    assert tuple(row.credit_spread_key for row in summary.rows) == (
        "credit.hy.retail",
        "credit.hy.energy",
        "credit.ig.ready",
    )

    blocked = summary.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.signal_age_seconds == d("10800.000000")
    assert blocked.confidence_decay_factor == d("0.400000")
    assert blocked.final_confidence == d("0.500000")
    assert blocked.redacted_public_signal_reference == "sha256:a4531e4a561c"
    assert blocked.reason_codes == (
        "market_research_credit_spread_widening_digest_stale_signal",
        "market_research_credit_spread_widening_digest_block_widening",
        "market_research_credit_spread_widening_digest_source_family_gap",
        "market_research_credit_spread_widening_digest_stale_source_ratio",
    )

    watched = summary.rows[1]
    assert watched.digest_status == "watch"
    assert watched.confidence_decay_factor == d("0.100000")
    assert watched.final_confidence == d("0.660000")
    assert watched.redacted_public_signal_reference == "sha256:94663de8aa66"
    assert watched.reason_codes == (
        "market_research_credit_spread_widening_digest_watch_widening",
    )

    ready = summary.rows[2]
    assert ready.digest_status == "ready"
    assert ready.final_confidence == d("0.860000")
    assert ready.redacted_public_signal_reference == "public-credit-spread-note"
    assert ready.reason_codes == (
        "market_research_credit_spread_widening_digest_ready",
    )

    assert summary.reason_code_counts == (
        module.MarketResearchCreditSpreadWideningDigestReasonCodeCount(
            reason_code="market_research_credit_spread_widening_digest_stale_signal",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchCreditSpreadWideningDigestReasonCodeCount(
            reason_code="market_research_credit_spread_widening_digest_block_widening",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchCreditSpreadWideningDigestReasonCodeCount(
            reason_code="market_research_credit_spread_widening_digest_watch_widening",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchCreditSpreadWideningDigestReasonCodeCount(
            reason_code="market_research_credit_spread_widening_digest_source_family_gap",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchCreditSpreadWideningDigestReasonCodeCount(
            reason_code="market_research_credit_spread_widening_digest_stale_source_ratio",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchCreditSpreadWideningDigestReasonCodeCount(
            reason_code="market_research_credit_spread_widening_digest_ready",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        row.reason_code for row in summary.reason_code_counts
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    public = repr(asdict(summary)).lower()
    for token in (
        "wallet://",
        "https://",
        "token=",
        "secret",
        "private",
        "market_slug",
        "question",
        "order",
    ):
        assert token not in public


def test_empty_digest_is_blocked_report_only_with_decimal_zeroes() -> None:
    module = api()
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_credit_spread_widening_digest"
    )
    assert summary.signal_count == ZERO
    assert summary.ready_signal_count == ZERO
    assert summary.watch_signal_count == ZERO
    assert summary.blocked_signal_count == ZERO
    assert summary.average_final_confidence == ZERO
    assert summary.average_spread_widening_bps == ZERO
    assert summary.max_observed_signal_age_seconds == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        module.MarketResearchCreditSpreadWideningDigestReasonCodeCount(
            reason_code="market_research_credit_spread_widening_digest_no_inputs",
            count=d("1.000000"),
            signal_ratio=d("0.000000"),
        ),
    )
    assert summary.reason_codes == (
        "market_research_credit_spread_widening_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_credit_spread_widening_digest_validates_decimal_datetime_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="spread_widening_bps must be a Decimal"):
        spread_signal(spread_widening_bps=50)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="base_confidence must be a Decimal"):
        spread_signal(base_confidence=0.7)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report((spread_signal(),), generated_at=datetime(2026, 7, 3, 16, 0))

    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        spread_signal(observed_at=_DatetimeSubclass(2026, 7, 3, 15, 30, tzinfo=UTC))

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        spread_signal(observed_at=datetime(2026, 7, 3, 15, 30, tzinfo=_MissingOffsetTZ()))

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report((spread_signal(observed_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        report(
            (
                spread_signal("condition.duplicate"),
                spread_signal("condition.duplicate"),
            ),
        )

    with pytest.raises(ValueError, match="spread_widening_bps must match"):
        spread_signal(
            current_spread_bps=d("125.000000"),
            prior_spread_bps=d("100.000000"),
            spread_widening_bps=d("20.000000"),
        )

    row = spread_signal()
    with pytest.raises(FrozenInstanceError):
        row.spread_widening_bps = d("99.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        module.MarketResearchCreditSpreadWideningDigestConfig(readonly=False)


def test_reason_code_count_rejects_manual_zero_count() -> None:
    module = api()

    with pytest.raises(ValueError, match="count must be positive"):
        module.MarketResearchCreditSpreadWideningDigestReasonCodeCount(
            reason_code="market_research_credit_spread_widening_digest_ready",
            count=ZERO,
            signal_ratio=ZERO,
        )


def test_public_dataclasses_are_frozen_and_reject_subclassing() -> None:
    module = api()

    for public_type in (
        module.MarketResearchCreditSpreadWideningDigestConfig,
        module.MarketResearchCreditSpreadWideningDigestSignal,
        module.MarketResearchCreditSpreadWideningDigestRow,
        module.MarketResearchCreditSpreadWideningDigestReasonCodeCount,
        module.MarketResearchCreditSpreadWideningDigestReport,
    ):
        assert is_dataclass(public_type)
        assert public_type.__dataclass_params__.frozen
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Sub{public_type.__name__}", (public_type,), {})


def test_constructors_reject_noncanonical_ordering() -> None:
    module = api()
    summary = report(
        (
            spread_signal(
                "condition.blocked",
                credit_spread_key="credit.hy.retail",
                observed_at=GENERATED_AT - timedelta(hours=3),
                current_spread_bps=d("520.000000"),
                prior_spread_bps=d("420.000000"),
                spread_widening_bps=d("100.000000"),
                source_family_count=d("2.000000"),
                stale_source_ratio=d("0.400000"),
            ),
            spread_signal(
                "condition.watch",
                credit_spread_key="credit.hy.energy",
                current_spread_bps=d("440.000000"),
                prior_spread_bps=d("400.000000"),
                spread_widening_bps=d("40.000000"),
            ),
            spread_signal("condition.ready"),
        ),
    )

    with pytest.raises(ValueError, match="reason_codes must be deterministic"):
        replace(summary.rows[0], reason_codes=tuple(reversed(summary.rows[0].reason_codes)))

    with pytest.raises(ValueError, match="reason_code_counts must use deterministic"):
        replace(
            summary,
            reason_code_counts=tuple(reversed(summary.reason_code_counts)),
        )

    with pytest.raises(ValueError, match="reason_codes must be deterministic"):
        replace(summary, reason_codes=tuple(reversed(summary.reason_codes)))

    with pytest.raises(ValueError, match="rows must use deterministic sort"):
        replace(summary, rows=tuple(reversed(summary.rows)))


def test_all_public_records_reject_false_report_only_flags() -> None:
    summary = report((spread_signal(),))

    for record in (
        config(),
        spread_signal("condition.flags"),
        summary.rows[0],
        summary.reason_code_counts[0],
        summary,
    ):
        for flag_name in ("paper_only", "report_only", "readonly"):
            with pytest.raises(ValueError, match=f"{flag_name} must be True"):
                replace(record, **{flag_name: False})


def test_public_numeric_fields_are_decimal_only_and_payload_has_no_floats() -> None:
    module = api()
    summary = report((spread_signal(),))
    payload = module.market_research_credit_spread_widening_digest_payload(summary)

    for value in payload.values():
        assert not isinstance(value, float)
    for public_type in (
        module.MarketResearchCreditSpreadWideningDigestConfig,
        module.MarketResearchCreditSpreadWideningDigestSignal,
        module.MarketResearchCreditSpreadWideningDigestRow,
        module.MarketResearchCreditSpreadWideningDigestReasonCodeCount,
        module.MarketResearchCreditSpreadWideningDigestReport,
    ):
        for field_name, field in public_type.__dataclass_fields__.items():
            if field_name in {
                "paper_only",
                "report_only",
                "readonly",
                "reason_code_counts",
            }:
                continue
            if any(
                fragment in field_name
                for fragment in (
                    "count",
                    "ratio",
                    "bps",
                    "confidence",
                    "decay",
                    "seconds",
                )
            ):
                assert field.type in {Decimal, "Decimal"}

    with pytest.raises(ValueError, match="watch_widening_bps must be a Decimal"):
        config(watch_widening_bps=_DecimalSubclass("25.000000"))

    with pytest.raises(ValueError, match="condition_id must be a string"):
        spread_signal(condition_id=_StringSubclass("condition.bad"))


def test_payload_serializes_public_numerics_as_six_decimal_strings() -> None:
    module = api()
    summary = report(
        (
            spread_signal(),
            spread_signal(
                "condition.watch",
                credit_spread_key="credit.hy.energy",
                current_spread_bps=d("440.000000"),
                prior_spread_bps=d("400.000000"),
                spread_widening_bps=d("40.000000"),
            ),
        ),
    )
    payload = module.market_research_credit_spread_widening_digest_payload(summary)

    numeric_key_fragments = (
        "count",
        "ratio",
        "bps",
        "confidence",
        "decay",
        "seconds",
    )

    def assert_six_decimal_string(value: object) -> None:
        assert type(value) is str
        assert "." in value
        assert len(value.rsplit(".", maxsplit=1)[1]) == 6
        assert Decimal(value) == Decimal(value).quantize(d("0.000001"))

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if any(fragment in key for fragment in numeric_key_fragments) and not isinstance(
                    child,
                    (dict, list),
                ):
                    assert_six_decimal_string(child)
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)

    walk_payload(payload)


def test_payload_rejects_tampered_nested_public_values() -> None:
    module = api()
    summary = report((spread_signal(),))

    object.__setattr__(summary.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        module.market_research_credit_spread_widening_digest_payload(summary)
    object.__setattr__(summary.rows[0], "readonly", True)

    object.__setattr__(summary.reason_code_counts[0], "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        module.market_research_credit_spread_widening_digest_payload(summary)
    object.__setattr__(summary.reason_code_counts[0], "report_only", True)

    object.__setattr__(summary.rows[0], "final_confidence", d("0.8600001"))
    with pytest.raises(ValueError, match="six decimals"):
        module.market_research_credit_spread_widening_digest_payload(summary)


def test_module_scope_has_no_network_durable_or_live_trading_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_research_credit_spread_widening_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "order",
        "trade",
        "cancel",
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
        "fast",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
