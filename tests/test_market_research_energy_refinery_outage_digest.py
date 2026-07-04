from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_energy_refinery_outage_digest import (
    DEFAULT_MARKET_RESEARCH_ENERGY_REFINERY_OUTAGE_DIGEST_CONFIG_VERSION,
    MarketResearchEnergyRefineryOutageDigestConfig,
    MarketResearchEnergyRefineryOutageDigestInput,
    MarketResearchEnergyRefineryOutageDigestReasonCodeCount,
    MarketResearchEnergyRefineryOutageDigestRegionSummary,
    MarketResearchEnergyRefineryOutageDigestReport,
    build_market_research_energy_refinery_outage_digest,
    market_research_energy_refinery_outage_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 14, 0, tzinfo=UTC)
SOURCE_TZ = timezone(timedelta(hours=-5))
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_energy_refinery_outage_digest.py",
)


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
) -> MarketResearchEnergyRefineryOutageDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_ENERGY_REFINERY_OUTAGE_DIGEST_CONFIG_VERSION
        ),
        "material_capacity_bpd": d("150000.000000"),
        "critical_capacity_bpd": d("400000.000000"),
        "max_signal_age_seconds": d("21600.000000"),
        "min_source_count": d("2.000000"),
        "min_confidence_ratio": d("0.600000"),
    }
    values.update(overrides)
    return MarketResearchEnergyRefineryOutageDigestConfig(**values)


def signal(
    refinery_key: str = "gulf_coast_refinery",
    *,
    region: str = "us_gulf",
    signal_status: str = "pass",
    observed_at: datetime = GENERATED_AT - timedelta(hours=2),
    offline_capacity_bpd: Decimal = d("0.000000"),
    total_capacity_bpd: Decimal = d("500000.000000"),
    expected_restart_delay_days: Decimal = d("0.000000"),
    source_count: Decimal = d("2.000000"),
    confidence_ratio: Decimal = d("0.850000"),
    source_ref: str = "public_refinery_outage_notice",
    source_config_version: str = "energy-refinery-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchEnergyRefineryOutageDigestInput:
    return MarketResearchEnergyRefineryOutageDigestInput(
        refinery_key=refinery_key,
        region=region,
        signal_status=signal_status,
        observed_at=observed_at,
        offline_capacity_bpd=offline_capacity_bpd,
        total_capacity_bpd=total_capacity_bpd,
        expected_restart_delay_days=expected_restart_delay_days,
        source_count=source_count,
        confidence_ratio=confidence_ratio,
        source_ref=source_ref,
        source_config_version=source_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchEnergyRefineryOutageDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchEnergyRefineryOutageDigestReport:
    return build_market_research_energy_refinery_outage_digest(
        rows,
        generated_at=generated_at,
        config=cfg or config(),
    )


def test_refinery_outage_digest_reduces_inputs_deterministically() -> None:
    summary = report(
        (
            signal(
                "baytown",
                region="us_gulf",
                signal_status="watch",
                observed_at=GENERATED_AT - timedelta(hours=8),
                offline_capacity_bpd=d("175000.000000"),
                expected_restart_delay_days=d("2.500000"),
                source_ref="private-refinery-feed",
            ),
            signal(
                "rotterdam",
                region="emea",
                signal_status="blocked",
                observed_at=(GENERATED_AT - timedelta(hours=7)).astimezone(SOURCE_TZ),
                offline_capacity_bpd=d("425000.000000"),
                total_capacity_bpd=d("500000.000000"),
                expected_restart_delay_days=d("8.000000"),
                source_count=d("1.000000"),
                confidence_ratio=d("0.500000"),
                source_ref="https://vendor.example/feed?token=secret-123",
            ),
            signal(
                "midwest",
                region="us_midwest",
                observed_at=GENERATED_AT,
                source_config_version="energy-refinery-clean-source-v0",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(SOURCE_TZ),
    )

    assert isinstance(summary, MarketResearchEnergyRefineryOutageDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_ENERGY_REFINERY_OUTAGE_DIGEST_CONFIG_VERSION
    )
    assert tuple(row.refinery_key for row in summary.signals) == (
        "baytown",
        "midwest",
        "rotterdam",
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_energy_refinery_outage_digest"
    )
    assert summary.refinery_count == d("3.000000")
    assert summary.signal_count == d("3.000000")
    assert summary.pass_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("1.000000")
    assert summary.blocked_signal_count == d("1.000000")
    assert summary.material_outage_count == d("1.000000")
    assert summary.critical_outage_count == d("1.000000")
    assert summary.stale_signal_count == d("2.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.low_confidence_count == d("1.000000")
    assert summary.total_offline_capacity_bpd == d("600000.000000")
    assert summary.max_offline_capacity_bpd == d("425000.000000")
    assert summary.max_outage_capacity_ratio == d("0.850000")
    assert summary.max_expected_restart_delay_days == d("8.000000")
    assert summary.average_confidence_ratio == d("0.733333")
    assert summary.reason_codes == (
        "market_research_energy_refinery_outage_digest_critical_capacity_offline",
        "market_research_energy_refinery_outage_digest_material_capacity_offline",
        "market_research_energy_refinery_outage_digest_stale_signal",
        "market_research_energy_refinery_outage_digest_thin_sources",
        "market_research_energy_refinery_outage_digest_low_confidence",
        "market_research_energy_refinery_outage_digest_watch",
    )
    assert summary.reason_code_counts == (
        MarketResearchEnergyRefineryOutageDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_refinery_outage_digest_"
                "critical_capacity_offline"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchEnergyRefineryOutageDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_refinery_outage_digest_"
                "material_capacity_offline"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchEnergyRefineryOutageDigestReasonCodeCount(
            reason_code="market_research_energy_refinery_outage_digest_stale_signal",
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchEnergyRefineryOutageDigestReasonCodeCount(
            reason_code="market_research_energy_refinery_outage_digest_thin_sources",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchEnergyRefineryOutageDigestReasonCodeCount(
            reason_code="market_research_energy_refinery_outage_digest_low_confidence",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchEnergyRefineryOutageDigestReasonCodeCount(
            reason_code="market_research_energy_refinery_outage_digest_watch",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert summary.region_summaries == (
        MarketResearchEnergyRefineryOutageDigestRegionSummary(
            region="emea",
            signal_count=d("1.000000"),
            watch_signal_count=ZERO,
            blocked_signal_count=d("1.000000"),
            stale_signal_count=d("1.000000"),
            offline_capacity_bpd=d("425000.000000"),
            max_outage_capacity_ratio=d("0.850000"),
            max_expected_restart_delay_days=d("8.000000"),
            reason_codes=(
                "market_research_energy_refinery_outage_digest_"
                "critical_capacity_offline",
                "market_research_energy_refinery_outage_digest_stale_signal",
                "market_research_energy_refinery_outage_digest_thin_sources",
                "market_research_energy_refinery_outage_digest_low_confidence",
            ),
        ),
        MarketResearchEnergyRefineryOutageDigestRegionSummary(
            region="us_gulf",
            signal_count=d("1.000000"),
            watch_signal_count=d("1.000000"),
            blocked_signal_count=ZERO,
            stale_signal_count=d("1.000000"),
            offline_capacity_bpd=d("175000.000000"),
            max_outage_capacity_ratio=d("0.350000"),
            max_expected_restart_delay_days=d("2.500000"),
            reason_codes=(
                "market_research_energy_refinery_outage_digest_"
                "material_capacity_offline",
                "market_research_energy_refinery_outage_digest_stale_signal",
                "market_research_energy_refinery_outage_digest_watch",
            ),
        ),
    )

    watch_signal, pass_signal, blocked_signal = summary.signals
    assert watch_signal.signal_status == "watch"
    assert watch_signal.signal_age_seconds == d("28800.000000")
    assert watch_signal.outage_capacity_ratio == d("0.350000")
    assert watch_signal.redacted_source_ref == "sha256:5ca565716859"
    assert pass_signal.signal_status == "pass"
    assert pass_signal.signal_age_seconds == ZERO
    assert pass_signal.redacted_source_ref == "public_refinery_outage_notice"
    assert blocked_signal.signal_status == "blocked"
    assert blocked_signal.observed_at == GENERATED_AT - timedelta(hours=7)
    assert blocked_signal.redacted_source_ref == "sha256:f1b9cf4094c0"
    assert summary.source_config_versions == (
        ("baytown", "us_gulf", "energy-refinery-source-v0"),
        ("midwest", "us_midwest", "energy-refinery-clean-source-v0"),
        ("rotterdam", "emea", "energy-refinery-source-v0"),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    serialized = repr(asdict(summary)).lower()
    for token in (
        "secret-123",
        "vendor.example",
        "https://",
        "private-refinery-feed",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "token",
    ):
        assert token not in serialized
    _assert_decimal_only_public_numeric_fields(summary)


def test_refinery_outage_digest_passes_with_clean_fresh_signals() -> None:
    summary = report(
        (
            signal("alpha", region="us_gulf"),
            signal("beta", region="us_gulf", offline_capacity_bpd=d("50000.000000")),
        ),
    )

    assert summary.digest_status == "pass"
    assert summary.recommended_next_step == (
        "allow_report_only_energy_refinery_outage_digest"
    )
    assert summary.reason_codes == (
        "market_research_energy_refinery_outage_digest_passed",
    )
    assert summary.region_summaries == ()
    assert summary.reason_code_counts == (
        MarketResearchEnergyRefineryOutageDigestReasonCodeCount(
            reason_code="market_research_energy_refinery_outage_digest_passed",
            count=d("2.000000"),
            signal_ratio=d("1.000000"),
        ),
    )


def test_empty_refinery_outage_digest_is_blocked_and_decimal_only() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_energy_refinery_outage_digest"
    )
    assert summary.refinery_count == ZERO
    assert summary.signal_count == ZERO
    assert summary.pass_signal_count == ZERO
    assert summary.watch_signal_count == ZERO
    assert summary.blocked_signal_count == ZERO
    assert summary.total_offline_capacity_bpd == ZERO
    assert summary.max_outage_capacity_ratio == ZERO
    assert summary.average_confidence_ratio == ZERO
    assert summary.signals == ()
    assert summary.reason_codes == (
        "market_research_energy_refinery_outage_digest_empty",
    )
    assert summary.reason_code_counts == (
        MarketResearchEnergyRefineryOutageDigestReasonCodeCount(
            reason_code="market_research_energy_refinery_outage_digest_empty",
            count=ZERO,
            signal_ratio=ZERO,
        ),
    )
    _assert_decimal_only_public_numeric_fields(summary)


def test_refinery_outage_dataclasses_are_frozen_and_validate_surface() -> None:
    row = signal("alpha")
    summary = report((row,))

    assert row.observed_at == datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
    with pytest.raises(FrozenInstanceError):
        row.refinery_key = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("2.000000")  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):
        type("BadInput", (MarketResearchEnergyRefineryOutageDigestInput,), {})
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal("bad-time", observed_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(TypeError, match="offline_capacity_bpd must be a Decimal"):
        MarketResearchEnergyRefineryOutageDigestInput(
            refinery_key="bad-float",
            region="us_gulf",
            signal_status="pass",
            observed_at=GENERATED_AT,
            offline_capacity_bpd=1.0,  # type: ignore[arg-type]
            total_capacity_bpd=d("500000.000000"),
            expected_restart_delay_days=ZERO,
            source_count=d("2.000000"),
            confidence_ratio=d("0.850000"),
            source_ref="public_refinery_outage_notice",
        )
    with pytest.raises(ValueError, match="refinery_key must be a plain str"):
        signal(_StringSubclass("bad-string"))
    with pytest.raises(TypeError, match="source_count must be a Decimal"):
        signal("bad-decimal-subclass", source_count=_DecimalSubclass("2.000000"))
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report((row,), generated_at=_DateTimeSubclass(2026, 7, 4, 14, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="paper_only"):
        signal("bad-flags", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(config(), readonly=False)
    with pytest.raises(ValueError, match="offline_capacity_bpd must not exceed"):
        signal(
            "bad-capacity",
            offline_capacity_bpd=d("600000.000000"),
            total_capacity_bpd=d("500000.000000"),
        )
    with pytest.raises(ValueError, match="material_capacity_bpd must be below"):
        config(
            material_capacity_bpd=d("400000.000000"),
            critical_capacity_bpd=d("400000.000000"),
        )


def test_refinery_outage_payload_decimal_strings_and_safe_contract() -> None:
    summary = report((signal("alpha", offline_capacity_bpd=d("200000.000000")),))
    payload = market_research_energy_refinery_outage_digest_payload(summary)

    assert payload["signal_count"] == "1.000000"
    assert payload["total_offline_capacity_bpd"] == "200000.000000"
    assert payload["signals"][0]["source_count"] == "2.000000"
    assert payload["signals"][0]["outage_capacity_ratio"] == "0.400000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "'source_ref':" not in repr(payload)

    for value in (config(), signal("surface"), summary.signals[0], summary, payload):
        _assert_decimal_only_public_numeric_fields(value)


def test_refinery_outage_module_has_no_forbidden_side_effect_imports() -> None:
    module_path = Path(__file__).resolve().parents[1] / MODULE_PATH
    source = module_path.read_text()
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "balance",
        "order",
        "cancel",
        "replace",
        "secret",
        "network",
        "database",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_roots = {
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "supabase",
        "web3",
    }
    forbidden_calls = {
        "open",
        "connect",
        "request",
        "urlopen",
        "post",
        "put",
        "patch",
        "delete",
        "send",
        "trade",
        "place_order",
        "cancel_order",
        "replace_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name for alias in getattr(node, "names", ())]
            if isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
            assert not any(name.split(".")[0] in forbidden_roots for name in names)
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            if isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls


def _assert_decimal_only_public_numeric_fields(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            field_value = getattr(value, field.name)
            if isinstance(field_value, bool):
                continue
            if field.name.endswith(
                ("count", "ratio", "seconds", "days", "bpd"),
            ):
                assert isinstance(field_value, Decimal), field.name
            _assert_decimal_only_public_numeric_fields(field_value)
    elif isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str) and key.endswith(
                ("count", "ratio", "seconds", "days", "bpd"),
            ):
                assert isinstance(item, str), key
            _assert_decimal_only_public_numeric_fields(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_decimal_only_public_numeric_fields(item)
    elif isinstance(value, (float, int)) and not isinstance(value, bool):
        pytest.fail(f"digest output must not contain public numeric scalar: {value!r}")


def walk_values(value: object):
    if isinstance(value, dict):
        for item in value.values():
            yield from walk_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from walk_values(item)
    else:
        yield value
