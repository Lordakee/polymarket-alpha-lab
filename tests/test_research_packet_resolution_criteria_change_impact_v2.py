from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_packet_resolution_criteria_change_impact_v2"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": "phase1_resolution_criteria_change_impact_v2",
        "max_fresh_criteria_age_seconds": d("3600"),
        "near_settlement_seconds": d("86400"),
        "watch_impact_bps": d("300.000000"),
        "high_impact_bps": d("700.000000"),
        "stale_criteria_penalty_bps": d("160.000000"),
        "change_severity_weight_bps": d("500.000000"),
        "primary_source_penalty_bps": d("90.000000"),
        "proxy_source_penalty_bps": d("180.000000"),
        "unmapped_source_penalty_bps": d("300.000000"),
        "market_exposure_weight_bps": d("250.000000"),
        "contradiction_penalty_bps": d("85.000000"),
        "settlement_proximity_penalty_bps": d("140.000000"),
    }
    values.update(overrides)
    return module.ResearchPacketResolutionCriteriaChangeImpactV2Config(**values)


def candidate(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "candidate_id": "candidate-alpha",
        "market_slug": "market-alpha",
        "criteria_id": "criteria-alpha",
        "criteria_last_verified_at": GENERATED_AT - timedelta(seconds=7200),
        "change_severity": d("0.800000"),
        "official_source_tier": "proxy",
        "market_exposure": d("0.400000"),
        "contradiction_count": d("3"),
        "settlement_at": GENERATED_AT + timedelta(hours=12),
        "reason_codes": ("research_packet_present",),
    }
    values.update(overrides)
    return module.ResearchPacketResolutionCriteriaChangeImpactV2Input(**values)


def estimate(subject: object | None = None, **config_overrides: object):
    module = api()
    return module.estimate_research_packet_resolution_criteria_change_impact_v2(
        candidate() if subject is None else subject,
        config=config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_no_float_or_int_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_estimates_high_impact_from_stale_changed_proxy_sourced_criteria() -> None:
    report = estimate()

    assert report.generated_at == GENERATED_AT
    assert report.criteria_age_seconds == d("7200.000000")
    assert report.settlement_proximity_seconds == d("43200.000000")
    assert report.stale_criteria_penalty_bps == d("160.000000")
    assert report.change_severity_impact_bps == d("400.000000")
    assert report.source_hierarchy_penalty_bps == d("180.000000")
    assert report.market_exposure_impact_bps == d("100.000000")
    assert report.contradiction_impact_bps == d("255.000000")
    assert report.settlement_proximity_impact_bps == d("140.000000")
    assert report.raw_impact_bps == d("1235.000000")
    assert report.impact_band == "high"
    assert report.report_status == "paper_blocked"
    assert report.reason_codes == (
        "research_packet_present",
        "research_packet_resolution_criteria_change_impact_v2",
        "impact_band_high",
        "criteria_age_stale",
        "change_severity_high",
        "source_hierarchy_proxy",
        "market_exposure_elevated",
        "contradictions_present",
        "settlement_proximity_near",
        "impact_score_high",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64


def test_low_and_watch_bands_are_deterministic() -> None:
    low_report = estimate(
        candidate(
            criteria_last_verified_at=GENERATED_AT - timedelta(seconds=600),
            change_severity=d("0.000000"),
            official_source_tier="official",
            market_exposure=d("0.050000"),
            contradiction_count=d("0"),
            settlement_at=GENERATED_AT + timedelta(days=90),
            reason_codes=(),
        ),
    )
    watch_report = estimate(
        candidate(
            criteria_last_verified_at=GENERATED_AT - timedelta(seconds=7200),
            change_severity=d("0.000000"),
            official_source_tier="primary",
            market_exposure=d("0.400000"),
            contradiction_count=d("0"),
            settlement_at=GENERATED_AT + timedelta(days=90),
            reason_codes=(),
        ),
    )

    assert low_report.raw_impact_bps == d("12.500000")
    assert low_report.impact_band == "low"
    assert low_report.report_status == "paper_clear"
    assert low_report.reason_codes == (
        "research_packet_resolution_criteria_change_impact_v2",
        "impact_band_low",
        "criteria_age_fresh",
        "change_severity_none",
        "source_hierarchy_official",
        "market_exposure_limited",
        "no_contradictions",
        "settlement_proximity_not_near",
        "impact_score_below_watch",
    )

    assert watch_report.raw_impact_bps == d("350.000000")
    assert watch_report.impact_band == "watch"
    assert watch_report.report_status == "paper_watch"
    assert watch_report.reason_codes == (
        "research_packet_resolution_criteria_change_impact_v2",
        "impact_band_watch",
        "criteria_age_stale",
        "change_severity_none",
        "source_hierarchy_primary",
        "market_exposure_elevated",
        "no_contradictions",
        "settlement_proximity_not_near",
        "impact_score_watch",
    )


def test_payload_serializes_decimal_strings_and_revalidates_digest() -> None:
    module = api()
    report = estimate()
    payload = module.research_packet_resolution_criteria_change_impact_v2_payload(
        report,
    )

    assert payload["generated_at"] == "2026-07-06T12:00:00Z"
    assert payload["criteria_last_verified_at"] == "2026-07-06T10:00:00Z"
    assert payload["settlement_at"] == "2026-07-07T00:00:00Z"
    assert payload["raw_impact_bps"] == "1235.000000"
    assert payload["contradiction_count"] == "3"
    assert payload["reason_codes"] == list(report.reason_codes)
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    ready = module.validate_research_packet_resolution_criteria_change_impact_v2_public_payload(
        payload,
    )
    assert ready == payload

    object.__setattr__(report, "raw_impact_bps", d("0.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        module.research_packet_resolution_criteria_change_impact_v2_payload(report)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    subject = candidate()
    cfg = config()
    report = estimate(subject)

    assert is_dataclass(subject)
    assert is_dataclass(cfg)
    assert is_dataclass(report)
    assert module.ResearchPacketResolutionCriteriaChangeImpactV2Input.__dataclass_params__.frozen
    assert module.ResearchPacketResolutionCriteriaChangeImpactV2Config.__dataclass_params__.frozen
    assert module.ResearchPacketResolutionCriteriaChangeImpactV2Report.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.candidate_id = "candidate-beta"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.impact_band = "low"  # type: ignore[misc]

    for instance in (subject, cfg, report):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="change_severity must be a Decimal"):
        candidate(change_severity=0.8)
    with pytest.raises(ValueError, match="contradiction_count must be integral"):
        candidate(contradiction_count=d("1.250000"))
    with pytest.raises(ValueError, match="market_exposure must be between 0 and 1"):
        candidate(market_exposure=d("1.000001"))
    with pytest.raises(ValueError, match="official_source_tier must be one of"):
        candidate(official_source_tier="secondary")
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        candidate(reason_codes=["research_packet_present"])
    with pytest.raises(ValueError, match="paper_only must be True"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="high_impact_bps must be at least watch threshold"):
        config(high_impact_bps=d("299.000000"))
    with pytest.raises(ValueError, match="score_input"):
        estimate(object())

    rebuilt = module.ResearchPacketResolutionCriteriaChangeImpactV2Report(
        **public_field_values(report),
    )
    assert rebuilt == report


def test_rejects_future_criteria_past_settlement_and_digest_tampering() -> None:
    module = api()
    report = estimate()

    with pytest.raises(ValueError, match="criteria_last_verified_at must not be after generated_at"):
        estimate(
            candidate(
                criteria_last_verified_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="settlement_at must not be before generated_at"):
        estimate(candidate(settlement_at=GENERATED_AT - timedelta(seconds=1)))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.estimate_research_packet_resolution_criteria_change_impact_v2(
            candidate(),
            config=config(),
            generated_at="2026-07-06T12:00:00Z",
        )
    with pytest.raises(ValueError, match="config"):
        module.estimate_research_packet_resolution_criteria_change_impact_v2(
            candidate(),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        module.ResearchPacketResolutionCriteriaChangeImpactV2Report(
            **{
                **public_field_values(report),
                "derived_validation_digest": "0" * 64,
            },
        )


def test_module_has_no_runtime_surface_or_float_literals() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/"
        "research_packet_resolution_criteria_change_impact_v2.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "private_key",
        "submit_",
        "cancel_",
        "place_",
        "create_",
        "open(",
        "Path(",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

    unsafe_surface_terms = (
        "live",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "wallet",
        " auth",
        "order",
        "buy",
        "sell",
        "trade",
    )
    for term in unsafe_surface_terms:
        assert term not in lowered

    tree = ast.parse(source)
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}

    assert set(imported_modules) <= {
        "__future__",
        "collections.abc",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
    assert module.__all__ == (
        "IMPACT_BANDS",
        "REPORT_STATUSES",
        "OFFICIAL_SOURCE_TIERS",
        "ResearchPacketResolutionCriteriaChangeImpactV2Config",
        "ResearchPacketResolutionCriteriaChangeImpactV2Input",
        "ResearchPacketResolutionCriteriaChangeImpactV2Report",
        "estimate_research_packet_resolution_criteria_change_impact_v2",
        "research_packet_resolution_criteria_change_impact_v2_payload",
        "validate_research_packet_resolution_criteria_change_impact_v2_public_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "research_packet_resolution_criteria_change_impact_v2" not in getattr(
        root,
        "__all__",
        (),
    )
