from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import ast
import numbers
import typing

import pytest

from polymarket_alpha_lab.market_research_oil_event_memory_digest import (
    MarketResearchOilEventMemoryDigestConfig,
    MarketResearchOilEventMemoryDigestEvidence,
    MarketResearchOilEventMemoryDigestEvidenceRow,
    MarketResearchOilEventMemoryDigestReport,
    build_market_research_oil_event_memory_digest,
    market_research_oil_event_memory_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketResearchOilEventMemoryDigestConfig:
    values = {
        "config_version": "market-research-oil-event-memory-digest-v1",
        "max_inventory_age_hours": d("36.000000"),
        "min_catalyst_quality_score": d("0.700000"),
        "min_curve_signal_score": d("0.600000"),
        "min_demand_confirmation_score": d("0.550000"),
        "min_source_family_count": d("3.000000"),
        "max_stale_evidence_share": d("0.250000"),
        "max_volatility_liquidity_gap": d("0.300000"),
        "confidence_decay_per_stale_share": d("0.400000"),
        "confidence_decay_per_gap": d("0.250000"),
        "min_final_confidence": d("0.650000"),
    }
    values.update(overrides)
    return MarketResearchOilEventMemoryDigestConfig(**values)


def evidence(**overrides: object) -> MarketResearchOilEventMemoryDigestEvidence:
    values = {
        "market_slug": "brent-opec-q3",
        "evidence_id": "oil-memory-001",
        "source_family": "inventory",
        "observed_at": GENERATED_AT - timedelta(hours=6),
        "inventory_data_published_at": GENERATED_AT - timedelta(hours=12),
        "opec_geopolitical_catalyst_quality": d("0.820000"),
        "futures_curve_signal": d("0.720000"),
        "demand_macro_confirmation": d("0.680000"),
        "volatility_liquidity_gap": d("0.110000"),
        "base_confidence": d("0.840000"),
        "summary": "EIA draw supports Brent setup without analyst@example.com",
        "reference": "https://example.test/report?token=secret",
        "reason_codes": (),
    }
    values.update(overrides)
    return MarketResearchOilEventMemoryDigestEvidence(**values)


def digest(
    rows: tuple[MarketResearchOilEventMemoryDigestEvidence, ...],
    *,
    cfg: MarketResearchOilEventMemoryDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchOilEventMemoryDigestReport:
    return build_market_research_oil_event_memory_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_floats(item)


def assert_no_secret_markers(value: object) -> None:
    public = repr(value).lower()
    for marker in (
        "password=",
        "api_key=",
        "private_key=",
        "signature=",
        "token=",
        "secret-value",
        "query-secret",
        "pre-query-secret",
    ):
        assert marker not in public


def test_digest_passes_with_fresh_diverse_oil_research_and_redacts_sensitive_strings() -> None:
    result = digest(
        (
            evidence(source_family="inventory", evidence_id="oil-b"),
            evidence(
                evidence_id="oil-a",
                source_family="opec",
                summary="OPEC headline confirms discipline near https://private.test/oil",
                reference="public/opec-note",
            ),
            evidence(evidence_id="oil-c", source_family="macro"),
        ),
        generated_at=datetime(2026, 7, 2, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert result.generated_at == GENERATED_AT
    assert result.generated_at.tzinfo is UTC
    assert result.config_version == "market-research-oil-event-memory-digest-v1"
    assert result.evidence_count == d("3.000000")
    assert result.source_family_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("0.000000")
    assert result.blocked_count == d("0.000000")
    assert result.digest_status == "pass"
    assert result.final_confidence == d("0.812500")
    assert result.reason_codes == (
        "demand_macro_confirmed",
        "fresh_inventory_data",
        "futures_curve_signal_confirmed",
        "oil_event_memory_digest_passed",
        "opec_geopolitical_catalyst_quality_confirmed",
        "source_family_diversity_passed",
        "volatility_liquidity_gap_acceptable",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.evidence_id for row in result.evidence_rows) == (
        "oil-a",
        "oil-b",
        "oil-c",
    )
    first = result.evidence_rows[0]
    assert first.redacted_summary == "OPEC headline confirms discipline near [REDACTED_URL]"
    assert first.redacted_reference == "public/opec-note"
    second = result.evidence_rows[1]
    assert "analyst@example.com" not in second.redacted_summary
    assert second.redacted_reference == "https://example.test/report?<redacted>"


def test_digest_blocks_stale_inventory_weak_catalysts_thin_diversity_gap_and_confidence_decay() -> None:
    result = digest(
        (
            evidence(
                source_family="inventory",
                observed_at=GENERATED_AT - timedelta(hours=80),
                inventory_data_published_at=GENERATED_AT - timedelta(hours=72),
                opec_geopolitical_catalyst_quality=d("0.500000"),
                futures_curve_signal=d("0.420000"),
                demand_macro_confirmation=d("0.300000"),
                volatility_liquidity_gap=d("0.600000"),
                base_confidence=d("0.700000"),
                reason_codes=("needs_eia_refresh",),
            ),
            evidence(
                evidence_id="oil-memory-002",
                source_family="inventory",
                observed_at=GENERATED_AT - timedelta(hours=10),
                inventory_data_published_at=GENERATED_AT - timedelta(hours=70),
                opec_geopolitical_catalyst_quality=d("0.680000"),
                futures_curve_signal=d("0.550000"),
                demand_macro_confirmation=d("0.510000"),
                volatility_liquidity_gap=d("0.450000"),
                base_confidence=d("0.720000"),
                reason_codes=(),
            ),
        ),
    )

    assert result.digest_status == "blocked"
    assert result.pass_count == d("0.000000")
    assert result.watch_count == d("0.000000")
    assert result.blocked_count == d("1.000000")
    assert result.evidence_count == d("2.000000")
    assert result.source_family_count == d("1.000000")
    assert result.stale_evidence_count == d("2.000000")
    assert result.stale_evidence_share == d("1.000000")
    assert result.max_inventory_data_age_hours == d("72.000000")
    assert result.max_volatility_liquidity_gap == d("0.600000")
    assert result.average_base_confidence == d("0.710000")
    assert result.final_confidence == d("0.160000")
    assert result.reason_codes == (
        "demand_macro_confirmation_weak",
        "final_confidence_below_threshold",
        "futures_curve_signal_weak",
        "inventory_data_stale",
        "needs_eia_refresh",
        "opec_geopolitical_catalyst_quality_weak",
        "source_family_diversity_gap",
        "stale_evidence_share_exceeds_threshold",
        "volatility_liquidity_gap_exceeds_threshold",
    )


def test_empty_digest_is_report_only_and_deterministic() -> None:
    result = digest(())

    assert result.evidence_count == d("0.000000")
    assert result.source_family_count == d("0.000000")
    assert result.digest_status == "blocked"
    assert result.final_confidence == d("0.000000")
    assert result.reason_codes == ("oil_event_memory_digest_empty",)
    assert result.evidence_rows == ()


def test_validation_enforces_decimal_utc_frozen_flags_and_public_numeric_types() -> None:
    result = digest(
        (
            evidence(source_family="inventory"),
            evidence(evidence_id="oil-memory-002", source_family="opec"),
            evidence(evidence_id="oil-memory-003", source_family="macro"),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        result.final_confidence = d("0.1")  # type: ignore[misc]

    with pytest.raises(ValueError, match="base_confidence"):
        evidence(base_confidence=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_final_confidence"):
        config(min_final_confidence=_DecimalSubclass("0.650000"))
    with pytest.raises(ValueError, match="observed_at"):
        evidence(observed_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        MarketResearchOilEventMemoryDigestReport(
            generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
            config_version="market-research-oil-event-memory-digest-v1",
            digest_status="blocked",
            evidence_count=d("0.000000"),
            source_family_count=d("0.000000"),
            pass_count=d("0.000000"),
            watch_count=d("0.000000"),
            blocked_count=d("0.000000"),
            stale_evidence_count=d("0.000000"),
            stale_evidence_share=d("0.000000"),
            max_inventory_data_age_hours=d("0.000000"),
            min_catalyst_quality_score=d("0.000000"),
            min_futures_curve_signal=d("0.000000"),
            min_demand_macro_confirmation=d("0.000000"),
            max_volatility_liquidity_gap=d("0.000000"),
            average_base_confidence=d("0.000000"),
            final_confidence=d("0.000000"),
            reason_codes=("oil_event_memory_digest_empty",),
            evidence_rows=(),
        )
    with pytest.raises(ValueError, match="paper_only"):
        evidence(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)

    public_classes = (
        MarketResearchOilEventMemoryDigestConfig,
        MarketResearchOilEventMemoryDigestEvidence,
        MarketResearchOilEventMemoryDigestEvidenceRow,
        MarketResearchOilEventMemoryDigestReport,
    )
    type_hints = {
        type_: typing.get_type_hints(type_)
        for type_ in public_classes
    }
    assert all(
        "float" not in str(type_hints[type_][field.name])
        and type_hints[type_][field.name] is not float
        for type_ in public_classes
        for field in fields(type_)
    )
    numeric_field_names = {
        "average_base_confidence",
        "base_confidence",
        "blocked_count",
        "confidence_decay_per_gap",
        "confidence_decay_per_stale_share",
        "demand_macro_confirmation",
        "evidence_count",
        "final_confidence",
        "futures_curve_signal",
        "inventory_data_age_hours",
        "max_inventory_age_hours",
        "max_inventory_data_age_hours",
        "max_stale_evidence_share",
        "max_volatility_liquidity_gap",
        "min_catalyst_quality_score",
        "min_curve_signal_score",
        "min_demand_confirmation_score",
        "min_demand_macro_confirmation",
        "min_final_confidence",
        "min_futures_curve_signal",
        "min_source_family_count",
        "opec_geopolitical_catalyst_quality",
        "pass_count",
        "source_family_count",
        "stale_evidence_count",
        "stale_evidence_share",
        "volatility_liquidity_gap",
        "watch_count",
    }
    assert all(
        type_hints[type_][field.name] is Decimal
        for type_ in public_classes
        for field in fields(type_)
        if field.name in numeric_field_names
    )
    assert all(
        not issubclass(type_hints[type_][field.name], numbers.Integral)
        for type_ in public_classes
        for field in fields(type_)
        if isinstance(type_hints[type_][field.name], type)
        and type_hints[type_][field.name] is not bool
    )


def test_payload_serializes_decimals_as_strings_and_rejects_inconsistent_reports() -> None:
    result = digest(
        (
            evidence(source_family="inventory"),
            evidence(evidence_id="oil-memory-002", source_family="opec"),
            evidence(evidence_id="oil-memory-003", source_family="macro"),
        ),
    )
    payload = market_research_oil_event_memory_digest_payload(result)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["evidence_count"] == "3.000000"
    assert payload["final_confidence"] == "0.812500"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_floats(payload)

    with pytest.raises(ValueError, match="evidence_count"):
        replace(result, evidence_count=d("2.000000"))
    with pytest.raises(ValueError, match="pass_count"):
        replace(result, pass_count=d("0.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(result, reason_codes=("inventory_data_stale",))


def test_payload_export_rechecks_hard_flags_and_rejects_runtime_public_surface() -> None:
    result = digest(
        (
            evidence(source_family="inventory"),
            evidence(evidence_id="oil-memory-002", source_family="opec"),
            evidence(evidence_id="oil-memory-003", source_family="macro"),
        ),
    )
    unsafe_row = object.__new__(MarketResearchOilEventMemoryDigestEvidenceRow)
    unsafe_row.__dict__.update(result.evidence_rows[0].__dict__)
    unsafe_row.__dict__["paper_only"] = False
    unsafe_report = object.__new__(MarketResearchOilEventMemoryDigestReport)
    unsafe_report.__dict__.update(result.__dict__)
    unsafe_report.__dict__["evidence_rows"] = (unsafe_row,) + result.evidence_rows[1:]

    with pytest.raises(ValueError, match="paper_only"):
        market_research_oil_event_memory_digest_payload(unsafe_report)

    unsafe_row = object.__new__(MarketResearchOilEventMemoryDigestEvidenceRow)
    unsafe_row.__dict__.update(result.evidence_rows[0].__dict__)
    unsafe_row.__dict__["redacted_summary"] = "runtime order submission surface"
    unsafe_report = object.__new__(MarketResearchOilEventMemoryDigestReport)
    unsafe_report.__dict__.update(result.__dict__)
    unsafe_report.__dict__["evidence_rows"] = (unsafe_row,) + result.evidence_rows[1:]

    with pytest.raises(ValueError, match="unsafe public surface"):
        market_research_oil_event_memory_digest_payload(unsafe_report)


def test_reason_and_reference_redaction_removes_execution_and_secret_surface() -> None:
    result = digest(
        (
            evidence(
                reason_codes=(
                    "wallet auth token order database live trading signal",
                    "broker-submit-cancel-private-key",
                ),
                summary=(
                    "Desk note includes wallet 0x1234567890abcdef1234567890abcdef12345678 "
                    "and bearer secret near https://private.test/oil?token=secret"
                ),
                reference="wallet://private/source?token=secret&authorization=bearer",
            ),
            evidence(evidence_id="oil-memory-002", source_family="opec"),
            evidence(evidence_id="oil-memory-003", source_family="macro"),
        ),
    )
    payload = market_research_oil_event_memory_digest_payload(result)
    public = repr(payload).lower()

    assert result.evidence_rows[0].redacted_reference.startswith("sha256:")
    assert all(reason.startswith("sha256:") for reason in result.evidence_rows[0].reason_codes)
    for token in (
        "wallet",
        "auth",
        "token",
        "order",
        "database",
        "live trading",
        "broker",
        "submit",
        "cancel",
        "private",
        "secret",
        "bearer",
        "0x1234567890abcdef1234567890abcdef12345678",
        "https://",
        ):
        assert token not in public


def test_secret_like_markers_are_redacted_from_all_public_strings() -> None:
    result = digest(
        (
            evidence(
                reason_codes=(
                    "password=secret-value",
                    "api_key=secret-value",
                    "private_key=secret-value",
                    "signature=secret-value",
                    "token=secret-value",
                ),
                summary=(
                    "Desk note password=secret-value api_key=secret-value "
                    "private_key=secret-value signature=secret-value token=secret-value"
                ),
                reference="https://example.test/password=pre-query-secret/report?x=query-secret",
            ),
            evidence(evidence_id="oil-memory-002", source_family="opec"),
            evidence(evidence_id="oil-memory-003", source_family="macro"),
        ),
    )
    payload = market_research_oil_event_memory_digest_payload(result)

    assert result.evidence_rows[0].redacted_summary.startswith("sha256:")
    assert result.evidence_rows[0].redacted_reference.startswith("sha256:")
    assert all(reason.startswith("sha256:") for reason in result.evidence_rows[0].reason_codes)
    assert_no_secret_markers(result)
    assert_no_secret_markers(payload)


def test_duplicate_evidence_sort_identity_is_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate evidence row identity"):
        digest(
            (
                evidence(
                    market_slug="brent-opec-q3",
                    evidence_id="duplicate-id",
                    source_family="inventory",
                ),
                evidence(
                    market_slug="brent-opec-q3",
                    evidence_id="duplicate-id",
                    source_family="inventory",
                    summary="Different row with same identity",
                ),
                evidence(
                    market_slug="brent-opec-q3",
                    evidence_id="oil-memory-003",
                    source_family="macro",
                ),
            ),
        )


def test_config_version_and_module_surface_are_hard_locked() -> None:
    with pytest.raises(ValueError, match="config_version"):
        config(config_version="market-research-oil-event-memory-digest-v2")

    module_path = Path(
        "src/polymarket_alpha_lab/market_research_oil_event_memory_digest.py",
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    constants: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            constants.append(node.value.lower())

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "websocket",
        "aiohttp",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "pathlib",
        "openai",
        "boto",
        "ccxt",
    )
    forbidden_call_or_attribute_names = (
        "connect",
        "execute",
        "fetch",
        "get",
        "post",
        "put",
        "delete",
        "open",
        "read",
        "write",
        "send",
        "submit",
        "cancel",
        "trade",
        "order",
        "wallet",
        "auth",
        "sign",
        "session",
        "commit",
    )
    forbidden_constant_fragments = (
        "auth",
        "broker",
        "signing",
        "submit",
        "cancel",
        "wallet",
        "account",
        "order",
        "live trading",
        "network",
        "database",
        "persist",
        "secret",
        "token",
        "private",
    )

    assert not any(
        fragment in module_name
        for module_name in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert not any(
        fragment in constant
        for constant in constants
        for fragment in forbidden_constant_fragments
    )
