from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_ism_prices_paid_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_ISM_PRICES_PAID_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchIsmPricesPaidSurpriseDigestConfig,
    MarketResearchIsmPricesPaidSurpriseDigestReasonCodeCount,
    MarketResearchIsmPricesPaidSurpriseDigestReport,
    MarketResearchIsmPricesPaidSurpriseDigestRow,
    MarketResearchIsmPricesPaidSurpriseDigestSignal,
    build_market_research_ism_prices_paid_surprise_digest,
    market_research_ism_prices_paid_surprise_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 14, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None

    def tzname(self, dt: datetime | None) -> str:
        return "none-offset"


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> MarketResearchIsmPricesPaidSurpriseDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_ISM_PRICES_PAID_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "max_signal_age_seconds": d("7200.000000"),
        "min_source_count": d("2.000000"),
        "material_surprise_threshold": d("2.000000"),
        "max_revision_ratio": d("0.200000"),
        "min_confirmation_ratio": d("0.650000"),
        "watch_confidence_threshold": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchIsmPricesPaidSurpriseDigestConfig(**values)


def signal(
    condition_id: str = "condition_ism_prices_paid",
    *,
    research_id: str = "research.ism.manufacturing.prices_paid",
    release_id: str = "ism.manufacturing.prices_paid",
    sector: str = "manufacturing",
    public_signal_reference: str = "official-ism-prices-paid-release",
    observed_at: datetime | None = None,
    expected_prices_paid_index: Decimal = d("55.000000"),
    actual_prices_paid_index: Decimal = d("55.400000"),
    source_count: Decimal = d("3.000000"),
    revision_ratio: Decimal = d("0.050000"),
    confirmation_ratio: Decimal = d("0.850000"),
    base_confidence: Decimal = d("0.900000"),
    signal_config_version: str = "ism-prices-paid-signal-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchIsmPricesPaidSurpriseDigestSignal:
    return MarketResearchIsmPricesPaidSurpriseDigestSignal(
        condition_id=condition_id,
        research_id=research_id,
        release_id=release_id,
        sector=sector,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=45),
        expected_prices_paid_index=expected_prices_paid_index,
        actual_prices_paid_index=actual_prices_paid_index,
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
    rows: tuple[MarketResearchIsmPricesPaidSurpriseDigestSignal, ...],
    *,
    config: MarketResearchIsmPricesPaidSurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchIsmPricesPaidSurpriseDigestReport:
    return build_market_research_ism_prices_paid_surprise_digest(
        rows,
        config=config or cfg(),
        generated_at=generated_at,
    )


def _walk_payload(value: object) -> None:
    if isinstance(value, dict):
        for child in value.values():
            _walk_payload(child)
    elif isinstance(value, list):
        for child in value:
            _walk_payload(child)
    else:
        assert not isinstance(value, (Decimal, datetime, float))


def _assert_six_decimal_string(value: object) -> None:
    assert isinstance(value, str)
    before, separator, after = value.partition(".")
    assert before
    assert separator == "."
    assert len(after) == 6
    Decimal(value)


def _assert_public_numeric_fields_are_exact_decimals(instance: object) -> None:
    numeric_suffixes = (
        "_count",
        "_ratio",
        "_index",
        "_seconds",
        "_confidence",
        "_threshold",
        "_surprise",
    )
    for field in fields(instance):
        value = getattr(instance, field.name)
        if field.name.endswith(numeric_suffixes):
            assert type(value) is Decimal, (field.name, type(value))
            assert value.as_tuple().exponent == -6, (field.name, value)


def test_ism_prices_paid_surprise_digest_reduces_and_sorts_deterministically() -> None:
    summary = report(
        (
            signal(
                "condition_ready",
                release_id="ism.prices_paid.ready",
                public_signal_reference="official-ready-prices-paid",
                observed_at=(GENERATED_AT - timedelta(minutes=45)).astimezone(
                    timezone(timedelta(hours=2)),
                ),
            ),
            signal(
                "condition_watch",
                release_id="ism.prices_paid.watch",
                public_signal_reference="vendor-internal-prices-paid",
                observed_at=GENERATED_AT - timedelta(minutes=30),
                expected_prices_paid_index=d("55.000000"),
                actual_prices_paid_index=d("58.500000"),
                source_count=d("3.000000"),
                revision_ratio=d("0.050000"),
                confirmation_ratio=d("0.850000"),
                base_confidence=d("0.850000"),
            ),
            signal(
                "condition_blocked",
                release_id="ism.prices_paid.blocked",
                public_signal_reference="public-blocked-prices-paid",
                observed_at=GENERATED_AT - timedelta(hours=3),
                expected_prices_paid_index=d("56.000000"),
                actual_prices_paid_index=d("62.500000"),
                source_count=d("1.000000"),
                revision_ratio=d("0.300000"),
                confirmation_ratio=d("0.400000"),
                base_confidence=d("0.700000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_ISM_PRICES_PAID_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_ism_prices_paid_surprise_digest"
    )
    assert summary.signal_count == d("3.000000")
    assert summary.ready_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("1.000000")
    assert summary.blocked_signal_count == d("1.000000")
    assert summary.material_surprise_count == d("2.000000")
    assert summary.stale_signal_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.high_revision_count == d("1.000000")
    assert summary.confirmation_gap_count == d("1.000000")
    assert summary.average_abs_surprise_index == d("3.466667")
    assert summary.max_abs_surprise_index == d("6.500000")
    assert summary.average_final_confidence == d("0.648333")
    assert summary.max_observed_signal_age_seconds == d("10800.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.digest_status, row.release_id) for row in summary.rows) == (
        ("blocked", "ism.prices_paid.blocked"),
        ("watch", "ism.prices_paid.watch"),
        ("ready", "ism.prices_paid.ready"),
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, MarketResearchIsmPricesPaidSurpriseDigestRow)
    assert blocked.observed_at == GENERATED_AT - timedelta(hours=3)
    assert blocked.observed_at.tzinfo is UTC
    assert blocked.signal_age_seconds == d("10800.000000")
    assert blocked.surprise_index == d("6.500000")
    assert blocked.abs_surprise_index == d("6.500000")
    assert blocked.confidence_decay_factor == d("0.400000")
    assert blocked.final_confidence == d("0.280000")
    assert blocked.reason_codes == (
        "market_research_ism_prices_paid_surprise_digest_stale_signal",
        "market_research_ism_prices_paid_surprise_digest_material_surprise",
        "market_research_ism_prices_paid_surprise_digest_thin_sources",
        "market_research_ism_prices_paid_surprise_digest_high_revision",
        "market_research_ism_prices_paid_surprise_digest_confirmation_gap",
    )

    watched = summary.rows[1]
    assert watched.signal_age_seconds == d("1800.000000")
    assert watched.surprise_index == d("3.500000")
    assert watched.confidence_decay_factor == d("0.900000")
    assert watched.final_confidence == d("0.765000")
    assert watched.redacted_public_signal_reference == "sha256:cf1ef1f58af9"
    assert watched.reason_codes == (
        "market_research_ism_prices_paid_surprise_digest_material_surprise",
    )

    ready = summary.rows[2]
    assert ready.observed_at == GENERATED_AT - timedelta(minutes=45)
    assert ready.surprise_index == d("0.400000")
    assert ready.confidence_decay_factor == d("1.000000")
    assert ready.final_confidence == d("0.900000")
    assert ready.redacted_public_signal_reference == "official-ready-prices-paid"
    assert ready.reason_codes == (
        "market_research_ism_prices_paid_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchIsmPricesPaidSurpriseDigestReasonCodeCount(
            reason_code="market_research_ism_prices_paid_surprise_digest_material_surprise",
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchIsmPricesPaidSurpriseDigestReasonCodeCount(
            reason_code="market_research_ism_prices_paid_surprise_digest_stale_signal",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchIsmPricesPaidSurpriseDigestReasonCodeCount(
            reason_code="market_research_ism_prices_paid_surprise_digest_thin_sources",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchIsmPricesPaidSurpriseDigestReasonCodeCount(
            reason_code="market_research_ism_prices_paid_surprise_digest_high_revision",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchIsmPricesPaidSurpriseDigestReasonCodeCount(
            reason_code="market_research_ism_prices_paid_surprise_digest_confirmation_gap",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchIsmPricesPaidSurpriseDigestReasonCodeCount(
            reason_code="market_research_ism_prices_paid_surprise_digest_ready",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )

    for instance in (
        cfg(),
        signal(),
        summary,
        summary.rows[0],
        summary.reason_code_counts[0],
    ):
        _assert_public_numeric_fields_are_exact_decimals(instance)


def test_ism_prices_paid_surprise_empty_inputs_block_as_missing_evidence() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_ism_prices_paid_surprise_digest"
    )
    assert summary.signal_count == d("0.000000")
    assert summary.ready_signal_count == d("0.000000")
    assert summary.watch_signal_count == d("0.000000")
    assert summary.blocked_signal_count == d("0.000000")
    assert summary.average_abs_surprise_index == d("0.000000")
    assert summary.max_abs_surprise_index == d("0.000000")
    assert summary.average_final_confidence == d("0.000000")
    assert summary.max_observed_signal_age_seconds == d("0.000000")
    assert summary.rows == ()
    assert summary.reason_codes == (
        "market_research_ism_prices_paid_surprise_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchIsmPricesPaidSurpriseDigestReasonCodeCount(
            reason_code="market_research_ism_prices_paid_surprise_digest_no_inputs",
            count=d("1.000000"),
            signal_ratio=d("0.000000"),
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_ism_prices_paid_surprise_payload_is_json_ready_and_six_decimal() -> None:
    summary = report((signal(),))

    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].final_confidence = d("0.500000")  # type: ignore[misc]

    payload = market_research_ism_prices_paid_surprise_digest_payload(summary)
    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["signal_count"] == "1.000000"
    assert payload["rows"][0]["actual_prices_paid_index"] == "55.400000"  # type: ignore[index]
    assert payload["reason_code_counts"][0]["count"] == "1.000000"  # type: ignore[index]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _walk_payload(payload)
    _assert_six_decimal_string(payload["signal_count"])
    _assert_six_decimal_string(payload["average_final_confidence"])
    _assert_six_decimal_string(payload["rows"][0]["surprise_index"])  # type: ignore[index]

    payload_text = repr(payload).lower()
    for forbidden in (
        "vendor-internal-prices-paid",
        "api_key",
        "private_key",
        "wallet",
        "submit_order",
        "cancel_order",
        "replace_order",
    ):
        assert forbidden not in payload_text


def test_ism_prices_paid_surprise_rejects_false_public_flags() -> None:
    summary = report((signal(),))
    row = summary.rows[0]
    reason_count = summary.reason_code_counts[0]

    false_flag_cases = (
        lambda: cfg(paper_only=False),
        lambda: cfg(report_only=False),
        lambda: cfg(readonly=False),
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

    for make_invalid in false_flag_cases:
        with pytest.raises(ValueError, match="must be True"):
            make_invalid()


def test_ism_prices_paid_surprise_rejects_bad_types_tz_and_reference_values() -> None:
    with pytest.raises(ValueError, match="actual_prices_paid_index must be a Decimal"):
        signal(actual_prices_paid_index=55.4)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="expected_prices_paid_index must be a Decimal"):
        signal(expected_prices_paid_index=_DecimalSubclass("55.000000"))

    with pytest.raises(ValueError, match="source_count must be a whole-count Decimal"):
        signal(source_count=d("1.500000"))

    with pytest.raises(ValueError, match="confirmation_ratio must be between 0 and 1"):
        signal(confirmation_ratio=d("1.000001"))

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 3, 13, 30))

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 3, 13, 30, tzinfo=_NoneOffsetTz()))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report((), generated_at=datetime(2026, 7, 3, 14, 0, tzinfo=_NoneOffsetTz()))

    with pytest.raises(ValueError, match="public_signal_reference must be public"):
        signal(public_signal_reference="https://vendor.example/ism?token=secret-123")

    with pytest.raises(ValueError, match="duplicate condition_id"):
        report(
            (
                signal(condition_id="duplicate-condition", release_id="release.one"),
                signal(condition_id="duplicate-condition", release_id="release.two"),
            ),
        )

    with pytest.raises(ValueError, match="duplicate release_id"):
        report(
            (
                signal(condition_id="condition.one", release_id="duplicate-release"),
                signal(condition_id="condition.two", release_id="duplicate-release"),
            ),
        )


def test_ism_prices_paid_surprise_public_constructors_reject_noncanonical_sequences() -> None:
    summary = report(
        (
            signal(
                "condition_ready",
                release_id="ism.prices_paid.ready",
            ),
            signal(
                "condition_watch",
                release_id="ism.prices_paid.watch",
                actual_prices_paid_index=d("58.500000"),
                base_confidence=d("0.850000"),
            ),
            signal(
                "condition_blocked",
                release_id="ism.prices_paid.blocked",
                observed_at=GENERATED_AT - timedelta(hours=3),
                actual_prices_paid_index=d("62.500000"),
                source_count=d("1.000000"),
                revision_ratio=d("0.300000"),
                confirmation_ratio=d("0.400000"),
                base_confidence=d("0.700000"),
            ),
        ),
    )

    with pytest.raises(ValueError, match="rows must use deterministic sequence"):
        replace(summary, rows=tuple(reversed(summary.rows)))

    with pytest.raises(ValueError, match="reason_codes must use deterministic sequence"):
        replace(summary, reason_codes=tuple(reversed(summary.reason_codes)))

    with pytest.raises(
        ValueError,
        match="reason_code_counts must use deterministic sequence",
    ):
        replace(summary, reason_code_counts=tuple(reversed(summary.reason_code_counts)))

    with pytest.raises(ValueError, match="reason_codes must use deterministic sequence"):
        replace(summary.rows[0], reason_codes=tuple(reversed(summary.rows[0].reason_codes)))

    with pytest.raises(ValueError, match="reason_codes must not include no_inputs"):
        replace(
            summary.rows[1],
            reason_codes=("market_research_ism_prices_paid_surprise_digest_no_inputs",),
        )

    with pytest.raises(ValueError, match="reason_code_counts must match rows"):
        replace(
            summary,
            reason_code_counts=(
                MarketResearchIsmPricesPaidSurpriseDigestReasonCodeCount(
                    reason_code="market_research_ism_prices_paid_surprise_digest_no_inputs",
                    count=d("1.000000"),
                    signal_ratio=d("0.000000"),
                ),
            ),
            reason_codes=("market_research_ism_prices_paid_surprise_digest_no_inputs",),
        )


def test_ism_prices_paid_surprise_module_has_no_io_or_live_mutation_surface() -> None:
    source_path = (
        Path(__file__).parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_ism_prices_paid_surprise_digest.py"
    )
    source = source_path.read_text(encoding="utf-8")
    lowered = source.lower()
    tree = ast.parse(source)

    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert imported_roots.isdisjoint(
        {
            "ccxt",
            "eth_account",
            "httpx",
            "psycopg",
            "requests",
            "socket",
            "sqlalchemy",
            "sqlite3",
            "urllib",
            "web3",
        },
    )

    forbidden_calls = {"open", "connect", "request", "urlopen", "Session"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_calls
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_calls

    for forbidden_fragment in (
        "api_key",
        "private_key",
        "wallet",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
        "live_trading",
        "exchange",
        "database",
        "sqlite",
        "psycopg",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "secret",
        "token",
        "fast",
    ):
        assert forbidden_fragment not in lowered

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
