from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, get_type_hints

import pytest

import polymarket_alpha_lab.source_official_vs_market_signal_divergence_report as api
from polymarket_alpha_lab.source_official_vs_market_signal_divergence_report import (
    DIVERGENCE_STATUSES,
    SourceOfficialVsMarketSignalDivergenceInput,
    SourceOfficialVsMarketSignalDivergenceReport,
    build_source_official_vs_market_signal_divergence_report,
    source_official_vs_market_signal_divergence_report_digest,
    source_official_vs_market_signal_divergence_report_to_payload,
    validate_source_official_vs_market_signal_divergence_public_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "source_official_vs_market_signal_divergence_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def signal_input(
    **overrides: object,
) -> SourceOfficialVsMarketSignalDivergenceInput:
    values = {
        "official_signal_probability": d("0.820000"),
        "market_implied_probability": d("0.560000"),
        "independent_source_probability": d("0.780000"),
        "divergence_threshold_probability": d("0.100000"),
        "source_freshness_age_hours": d("3.000000"),
    }
    values.update(overrides)
    return SourceOfficialVsMarketSignalDivergenceInput(**values)


def report(**overrides: object) -> SourceOfficialVsMarketSignalDivergenceReport:
    return build_source_official_vs_market_signal_divergence_report(
        signal_input(**overrides),
    )


def assert_no_runtime_numbers(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_runtime_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)


def test_divergence_status_vocabulary_is_exact() -> None:
    assert DIVERGENCE_STATUSES == (
        "official_market_divergence",
        "aligned",
        "stale_source_watch",
    )


def test_detects_official_market_divergence_with_readonly_payload_and_digest() -> None:
    first = report()
    second = report()

    assert type(first) is SourceOfficialVsMarketSignalDivergenceReport
    assert is_dataclass(first)
    assert first.divergence_status == "official_market_divergence"
    assert first.official_market_probability_gap == d("0.260000")
    assert first.independent_official_probability_gap == d("0.040000")
    assert first.independent_market_probability_gap == d("0.220000")
    assert first.reason_codes == (
        "official_market_gap_meets_threshold",
        "independent_source_supports_official_signal",
        "source_freshness_within_phase1_window",
    )
    assert first.manual_next_step == "manual_review_official_market_gap"
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second

    payload = source_official_vs_market_signal_divergence_report_to_payload(first)
    assert first.public_payload == payload
    assert payload == {
        "official_signal_probability": "0.820000",
        "market_implied_probability": "0.560000",
        "independent_source_probability": "0.780000",
        "divergence_threshold_probability": "0.100000",
        "source_freshness_age_hours": "3.000000",
        "official_market_probability_gap": "0.260000",
        "independent_official_probability_gap": "0.040000",
        "independent_market_probability_gap": "0.220000",
        "divergence_status": "official_market_divergence",
        "reason_codes": [
            "official_market_gap_meets_threshold",
            "independent_source_supports_official_signal",
            "source_freshness_within_phase1_window",
        ],
        "manual_next_step": "manual_review_official_market_gap",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    expected_digest = sha256(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"),
    ).hexdigest()
    assert first.payload_digest == expected_digest
    assert first.payload_digest == second.payload_digest
    assert (
        source_official_vs_market_signal_divergence_report_digest(first)
        == expected_digest
    )
    assert (
        validate_source_official_vs_market_signal_divergence_public_payload(payload)
        == payload
    )
    assert_no_runtime_numbers(payload)


def test_aligned_signal_reports_no_divergence_without_triggering_next_step() -> None:
    result = report(
        official_signal_probability=d("0.610000"),
        market_implied_probability=d("0.560000"),
        independent_source_probability=d("0.600000"),
        divergence_threshold_probability=d("0.100000"),
    )

    assert result.divergence_status == "aligned"
    assert result.reason_codes == ("official_market_gap_below_threshold",)
    assert result.manual_next_step == "no_manual_action_required"
    assert result.official_market_probability_gap == d("0.050000")
    assert result.public_payload["divergence_status"] == "aligned"


def test_stale_independent_source_prevents_divergence_callout() -> None:
    result = report(source_freshness_age_hours=d("73.000000"))

    assert result.divergence_status == "stale_source_watch"
    assert result.reason_codes == (
        "official_market_gap_meets_threshold",
        "independent_source_supports_official_signal",
        "source_freshness_outside_phase1_window",
    )
    assert result.manual_next_step == "refresh_independent_source_before_manual_review"
    assert result.public_payload["source_freshness_age_hours"] == "73.000000"


def test_independent_source_must_support_official_side_for_divergence_callout() -> None:
    result = report(independent_source_probability=d("0.580000"))

    assert result.divergence_status == "aligned"
    assert result.reason_codes == (
        "official_market_gap_meets_threshold",
        "independent_source_does_not_support_official_signal",
        "source_freshness_within_phase1_window",
    )
    assert result.manual_next_step == "no_manual_action_required"


def test_dataclasses_are_frozen_and_decimal_only() -> None:
    source = signal_input()
    result = report()

    assert is_dataclass(SourceOfficialVsMarketSignalDivergenceInput)
    assert is_dataclass(SourceOfficialVsMarketSignalDivergenceReport)
    assert source.__dataclass_params__.frozen
    assert result.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        result.divergence_status = "aligned"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(SourceOfficialVsMarketSignalDivergenceInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(SourceOfficialVsMarketSignalDivergenceReport):
            pass

    with pytest.raises(ValueError, match="official_signal_probability"):
        signal_input(official_signal_probability=1)
    with pytest.raises(ValueError, match="market_implied_probability"):
        signal_input(market_implied_probability=0.5)
    with pytest.raises(ValueError, match="independent_source_probability"):
        signal_input(independent_source_probability=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="source_freshness_age_hours"):
        signal_input(source_freshness_age_hours=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        signal_input(paper_only=False)
    with pytest.raises(ValueError, match="official_market_probability_gap"):
        replace(result, official_market_probability_gap=1)  # type: ignore[arg-type]

    hints = get_type_hints(SourceOfficialVsMarketSignalDivergenceReport)
    for field_name in (
        "official_signal_probability",
        "market_implied_probability",
        "independent_source_probability",
        "divergence_threshold_probability",
        "source_freshness_age_hours",
        "official_market_probability_gap",
        "independent_official_probability_gap",
        "independent_market_probability_gap",
    ):
        assert hints[field_name] is Decimal
    for field in fields(result):
        value = getattr(result, field.name)
        if field.name.endswith("_probability") or field.name.endswith("_gap"):
            assert type(value) is Decimal
        if field.name == "source_freshness_age_hours":
            assert type(value) is Decimal


def test_manual_report_construction_must_match_derived_findings() -> None:
    with pytest.raises(ValueError, match="reason_codes"):
        SourceOfficialVsMarketSignalDivergenceReport(
            official_signal_probability=d("0.820000"),
            market_implied_probability=d("0.560000"),
            independent_source_probability=d("0.780000"),
            divergence_threshold_probability=d("0.100000"),
            source_freshness_age_hours=d("3.000000"),
            official_market_probability_gap=d("0.260000"),
            independent_official_probability_gap=d("0.040000"),
            independent_market_probability_gap=d("0.220000"),
            divergence_status="official_market_divergence",
            reason_codes=(),
            manual_next_step="manual_review_official_market_gap",
        )


def test_public_payload_tamper_checks_and_no_live_io_or_persistence_surface() -> None:
    payload = dict(report().public_payload)

    with pytest.raises(ValueError, match="official_market_probability_gap"):
        validate_source_official_vs_market_signal_divergence_public_payload(
            {**payload, "official_market_probability_gap": "0.010000"},
        )
    with pytest.raises(ValueError, match="divergence_status"):
        validate_source_official_vs_market_signal_divergence_public_payload(
            {**payload, "divergence_status": "aligned"},
        )
    with pytest.raises(ValueError, match="paper_only"):
        validate_source_official_vs_market_signal_divergence_public_payload(
            {**payload, "paper_only": False},
        )

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "web3",
        "private_key",
        "live",
        "auth",
        "wallet",
        "order",
        "private_key",
        "api_key",
        "secret_key",
        "submit",
        "execute",
        "jsonl",
        "write_text",
        "write_bytes",
    ):
        assert forbidden not in lowered_source

    tree = ast.parse(source)
    imported_roots: set[str] = set()
    call_names: set[str] = set()
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)
        elif isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id.lower())
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr.lower())

    assert not float_constants
    assert imported_roots.isdisjoint(
        {
            "requests",
            "httpx",
            "urllib",
            "socket",
            "sqlite3",
            "psycopg",
            "supabase",
            "web3",
        },
    )
    assert call_names.isdisjoint(
        {
            "connect",
            "cursor",
            "delete",
            "execute",
            "executemany",
            "fetch",
            "insert",
            "open",
            "post",
            "put",
            "rollback",
            "send",
            "sign",
            "submit",
            "upsert",
            "write",
            "write_text",
            "write_bytes",
        },
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert "wallet" not in lowered
        assert "auth" not in lowered
        assert "order" not in lowered
        assert "trade" not in lowered


def test_payload_digest_changes_when_signal_inputs_change() -> None:
    base = report()
    aligned = report(market_implied_probability=d("0.760000"))
    stale = report(source_freshness_age_hours=d("73.000000"))

    assert base.payload_digest != aligned.payload_digest
    assert base.payload_digest != stale.payload_digest
    assert base.public_payload != aligned.public_payload
