from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_energy_opec_quota_compliance_digest import (
    DEFAULT_MARKET_RESEARCH_ENERGY_OPEC_QUOTA_COMPLIANCE_DIGEST_CONFIG_VERSION,
    MarketResearchEnergyOpecQuotaComplianceDigestConfig,
    MarketResearchEnergyOpecQuotaComplianceDigestInputRow,
    MarketResearchEnergyOpecQuotaComplianceDigestReasonCodeCount,
    MarketResearchEnergyOpecQuotaComplianceDigestReport,
    build_market_research_energy_opec_quota_compliance_digest,
    market_research_energy_opec_quota_compliance_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchEnergyOpecQuotaComplianceDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_ENERGY_OPEC_QUOTA_COMPLIANCE_DIGEST_CONFIG_VERSION
        ),
        "fresh_report_max_age_seconds": d("86400.000000"),
        "min_secondary_source_count": d("2"),
        "material_overproduction_threshold_bpd": d("250000.000000"),
        "severe_overproduction_threshold_bpd": d("750000.000000"),
        "material_revision_threshold_bpd": d("300000.000000"),
        "thin_spare_capacity_threshold_bpd": d("1000000.000000"),
    }
    values.update(overrides)
    return MarketResearchEnergyOpecQuotaComplianceDigestConfig(**values)


def input_row(
    research_key: str = "research.opec.iraq",
    *,
    condition_id: str = "condition_opec_iraq",
    market_slug: str = "opec-iraq-production-quota",
    producer_group: str = "opec-plus",
    member_country: str = "iraq",
    quota_period: str = "2026-07",
    quota_source_reference: str = "opec-monthly-oil-market-report",
    report_timestamp: datetime | None = None,
    acknowledged_at: object = _UNSET,
    secondary_source_count: Decimal = d("2"),
    quota_bpd: Decimal = d("4000000.000000"),
    estimated_production_bpd: Decimal = d("4300000.000000"),
    prior_estimated_production_bpd: Decimal = d("4100000.000000"),
    spare_capacity_bpd: Decimal = d("1500000.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchEnergyOpecQuotaComplianceDigestInputRow:
    return MarketResearchEnergyOpecQuotaComplianceDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        market_slug=market_slug,
        producer_group=producer_group,
        member_country=member_country,
        quota_period=quota_period,
        quota_source_reference=quota_source_reference,
        report_timestamp=report_timestamp or GENERATED_AT - timedelta(hours=4),
        acknowledged_at=(
            GENERATED_AT - timedelta(hours=1)
            if acknowledged_at is _UNSET
            else acknowledged_at
        ),
        secondary_source_count=secondary_source_count,
        quota_bpd=quota_bpd,
        estimated_production_bpd=estimated_production_bpd,
        prior_estimated_production_bpd=prior_estimated_production_bpd,
        spare_capacity_bpd=spare_capacity_bpd,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchEnergyOpecQuotaComplianceDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchEnergyOpecQuotaComplianceDigestReport:
    return build_market_research_energy_opec_quota_compliance_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"float leaked into public report: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_floats(item)
    elif isinstance(value, (tuple, list)):
        for item in value:
            assert_no_floats(item)


def test_empty_input_returns_report_only_no_input_digest() -> None:
    summary = report((), generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))))

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_ENERGY_OPEC_QUOTA_COMPLIANCE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "ready"
    assert summary.recommended_next_step == (
        "hold_report_only_market_research_energy_opec_quota_compliance_digest"
    )
    assert summary.source_row_count == ZERO
    assert summary.screened_market_count == ZERO
    assert summary.low_risk_count == ZERO
    assert summary.watch_risk_count == ZERO
    assert summary.high_risk_count == ZERO
    assert summary.overproduction_count == ZERO
    assert summary.production_revision_count == ZERO
    assert summary.thin_secondary_source_count == ZERO
    assert summary.stale_report_count == ZERO
    assert summary.thin_spare_capacity_count == ZERO
    assert summary.max_overproduction_bpd == ZERO
    assert summary.average_compliance_ratio == ZERO
    assert summary.reason_code_counts == ()
    assert summary.rows == ()
    assert summary.reason_codes == (
        "market_research_energy_opec_quota_compliance_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert_no_floats(asdict(summary))


def test_high_risk_classification_sorts_and_counts_reason_codes() -> None:
    summary = report(
        (
            input_row(
                "research.opec.uae",
                condition_id="condition_opec_uae",
                market_slug="opec-uae-production-quota",
                member_country="uae",
                quota_source_reference="https://vendor.example/opec?token=secret-123",
                report_timestamp=GENERATED_AT - timedelta(days=2),
                acknowledged_at=None,
                secondary_source_count=d("1"),
                quota_bpd=d("3200000.000000"),
                estimated_production_bpd=d("4050000.000000"),
                prior_estimated_production_bpd=d("3500000.000000"),
                spare_capacity_bpd=d("500000.000000"),
            ),
            input_row(
                "research.opec.saudi",
                condition_id="condition_opec_saudi",
                market_slug="opec-saudi-production-quota",
                member_country="saudi-arabia",
                quota_source_reference="opec-official-release",
                report_timestamp=GENERATED_AT - timedelta(hours=1),
                secondary_source_count=d("4"),
                quota_bpd=d("9000000.000000"),
                estimated_production_bpd=d("8900000.000000"),
                prior_estimated_production_bpd=d("8880000.000000"),
                spare_capacity_bpd=d("2500000.000000"),
            ),
            input_row(
                "research.opec.iraq",
                condition_id="condition_opec_iraq",
                market_slug="opec-iraq-production-quota",
                member_country="iraq",
                quota_source_reference="iraq-ministry-oil",
                report_timestamp=GENERATED_AT - timedelta(hours=6),
                secondary_source_count=d("2"),
                quota_bpd=d("4000000.000000"),
                estimated_production_bpd=d("4325000.000000"),
                prior_estimated_production_bpd=d("4300000.000000"),
                spare_capacity_bpd=d("1200000.000000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=2))),
    )

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "escalate_report_only_market_research_energy_opec_quota_compliance_digest"
    )
    assert summary.source_row_count == d("3")
    assert summary.screened_market_count == d("3")
    assert summary.low_risk_count == d("1")
    assert summary.watch_risk_count == d("1")
    assert summary.high_risk_count == d("1")
    assert summary.overproduction_count == d("2")
    assert summary.severe_overproduction_count == d("1")
    assert summary.production_revision_count == d("1")
    assert summary.thin_secondary_source_count == d("1")
    assert summary.stale_report_count == d("1")
    assert summary.thin_spare_capacity_count == d("1")
    assert summary.max_overproduction_bpd == d("850000.000000")
    assert summary.average_compliance_ratio == d("1.111921")

    assert tuple((row.market_slug, row.member_country) for row in summary.rows) == (
        ("opec-uae-production-quota", "uae"),
        ("opec-iraq-production-quota", "iraq"),
        ("opec-saudi-production-quota", "saudi-arabia"),
    )

    uae = summary.rows[0]
    assert uae.risk_status == "high"
    assert uae.report_age_seconds == d("172800.000000")
    assert uae.production_surprise_bpd == d("850000.000000")
    assert uae.production_revision_bpd == d("550000.000000")
    assert uae.compliance_ratio == d("1.265625")
    assert uae.redacted_quota_source_reference == "sha256:7c604c112b0c"
    assert uae.reason_codes == (
        "market_research_energy_opec_quota_compliance_digest_severe_overproduction",
        "market_research_energy_opec_quota_compliance_digest_production_revision",
        "market_research_energy_opec_quota_compliance_digest_stale_report",
        "market_research_energy_opec_quota_compliance_digest_thin_secondary_sources",
        "market_research_energy_opec_quota_compliance_digest_thin_spare_capacity",
    )

    iraq = summary.rows[1]
    assert iraq.risk_status == "watch"
    assert iraq.production_surprise_bpd == d("325000.000000")
    assert iraq.reason_codes == (
        "market_research_energy_opec_quota_compliance_digest_overproduction",
    )

    saudi = summary.rows[2]
    assert saudi.risk_status == "low"
    assert saudi.production_surprise_bpd == d("-100000.000000")
    assert saudi.redacted_quota_source_reference == "opec-official-release"
    assert saudi.reason_codes == (
        "market_research_energy_opec_quota_compliance_digest_low_risk",
    )

    assert summary.reason_code_counts == (
        MarketResearchEnergyOpecQuotaComplianceDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_opec_quota_compliance_digest_"
                "overproduction"
            ),
            count=d("1"),
            report_ratio=d("0.333333"),
        ),
        MarketResearchEnergyOpecQuotaComplianceDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_opec_quota_compliance_digest_"
                "production_revision"
            ),
            count=d("1"),
            report_ratio=d("0.333333"),
        ),
        MarketResearchEnergyOpecQuotaComplianceDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_opec_quota_compliance_digest_"
                "severe_overproduction"
            ),
            count=d("1"),
            report_ratio=d("0.333333"),
        ),
        MarketResearchEnergyOpecQuotaComplianceDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_opec_quota_compliance_digest_"
                "stale_report"
            ),
            count=d("1"),
            report_ratio=d("0.333333"),
        ),
        MarketResearchEnergyOpecQuotaComplianceDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_opec_quota_compliance_digest_"
                "thin_secondary_sources"
            ),
            count=d("1"),
            report_ratio=d("0.333333"),
        ),
        MarketResearchEnergyOpecQuotaComplianceDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_opec_quota_compliance_digest_"
                "thin_spare_capacity"
            ),
            count=d("1"),
            report_ratio=d("0.333333"),
        ),
        MarketResearchEnergyOpecQuotaComplianceDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_opec_quota_compliance_digest_"
                "low_risk"
            ),
            count=d("1"),
            report_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == (
        "market_research_energy_opec_quota_compliance_digest_high_risk_present",
        "market_research_energy_opec_quota_compliance_digest_watch_risk_present",
        "market_research_energy_opec_quota_compliance_digest_stale_report_present",
        "market_research_energy_opec_quota_compliance_digest_thin_secondary_sources_present",
    )
    assert_no_floats(asdict(summary))


def test_sorting_is_deterministic_for_tied_risk_rows() -> None:
    first = input_row(
        "research.opec.b",
        condition_id="condition_b",
        market_slug="b-market",
        member_country="b-country",
        quota_bpd=d("1000000.000000"),
        estimated_production_bpd=d("1800000.000000"),
        prior_estimated_production_bpd=d("1000000.000000"),
        spare_capacity_bpd=d("100000.000000"),
    )
    second = input_row(
        "research.opec.a",
        condition_id="condition_a",
        market_slug="a-market",
        member_country="a-country",
        quota_bpd=d("1000000.000000"),
        estimated_production_bpd=d("1800000.000000"),
        prior_estimated_production_bpd=d("1000000.000000"),
        spare_capacity_bpd=d("100000.000000"),
    )

    forward = report((first, second))
    reversed_summary = report((second, first))

    expected_order = ("a-market", "b-market")
    assert tuple(row.market_slug for row in forward.rows) == expected_order
    assert tuple(row.market_slug for row in reversed_summary.rows) == expected_order
    assert forward.reason_code_counts == reversed_summary.reason_code_counts
    assert forward.reason_codes == reversed_summary.reason_codes


def test_non_default_thresholds_change_risk_classification() -> None:
    loose_config = config(
        material_overproduction_threshold_bpd=d("500000.000000"),
        severe_overproduction_threshold_bpd=d("1000000.000000"),
        material_revision_threshold_bpd=d("900000.000000"),
        thin_spare_capacity_threshold_bpd=d("200000.000000"),
    )

    summary = report(
        (
            input_row(
                quota_bpd=d("4000000.000000"),
                estimated_production_bpd=d("4325000.000000"),
                prior_estimated_production_bpd=d("4300000.000000"),
                spare_capacity_bpd=d("1200000.000000"),
            ),
        ),
        cfg=loose_config,
    )

    assert summary.digest_status == "ready"
    assert summary.low_risk_count == d("1")
    assert summary.watch_risk_count == ZERO
    assert summary.high_risk_count == ZERO
    assert summary.overproduction_count == ZERO
    assert summary.production_revision_count == ZERO
    assert summary.thin_spare_capacity_count == ZERO
    assert summary.rows[0].risk_status == "low"
    assert summary.rows[0].reason_codes == (
        "market_research_energy_opec_quota_compliance_digest_low_risk",
    )


def test_rejects_invalid_inputs_and_preserves_hard_flags() -> None:
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report((), generated_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="quota_bpd must be positive"):
        input_row(quota_bpd=ZERO)

    with pytest.raises(ValueError, match="report_timestamp cannot be after generated_at"):
        report((input_row(report_timestamp=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="config must be exactly"):
        build_market_research_energy_opec_quota_compliance_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="config hard flags must be true"):
        replace(config(), paper_only=False)

    with pytest.raises(ValueError, match="input row hard flags must be true"):
        input_row(readonly=False)

    with pytest.raises(TypeError):
        input_row(secondary_source_count=1)  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        input_row(estimated_production_bpd=_DecimalSubclass("1.000000"))

    with pytest.raises(TypeError):
        input_row(member_country=_StringSubclass("iraq"))

    with pytest.raises(TypeError):
        input_row(report_timestamp=_DatetimeSubclass(2026, 7, 4, tzinfo=UTC))

    summary = report((input_row(),))
    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="report hard flags must be true"):
        replace(summary, report_only=False)


def test_payload_serializes_public_numerics_as_strings() -> None:
    summary = report((input_row(),))
    payload = market_research_energy_opec_quota_compliance_digest_payload(summary)

    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["source_row_count"] == "1.000000"
    assert payload["rows"][0]["quota_bpd"] == "4000000.000000"
    assert payload["rows"][0]["report_timestamp"] == "2026-07-04T08:00:00+00:00"

    def walk(value: object) -> tuple[object, ...]:
        if isinstance(value, dict):
            return tuple(item for sub in value.values() for item in walk(sub))
        if isinstance(value, list):
            return tuple(item for sub in value for item in walk(sub))
        return (value,)

    assert not any(isinstance(item, Decimal) for item in walk(payload))
    assert not any(isinstance(item, float) for item in walk(payload))


def test_module_is_pure_report_only_and_has_no_banned_io_or_secret_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_energy_opec_quota_compliance_digest.py"
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    banned_import_roots = {
        "httpx",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "psycopg",
        "supabase",
    }
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    assert imports.isdisjoint(banned_import_roots)

    banned_calls = {
        "connect",
        "execute",
        "urlopen",
        "request",
        "post",
        "put",
        "patch",
        "delete",
        "order",
        "cancel",
        "replace",
    }
    calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    calls.update(
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    )
    assert calls.isdisjoint(banned_calls)

    lowered = source.lower()
    assert "private_key" not in lowered
    assert "wallet" not in lowered
    assert "live trading" not in lowered
    assert "auth" not in lowered
