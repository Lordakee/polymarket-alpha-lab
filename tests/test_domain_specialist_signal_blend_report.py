from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.domain_specialist_signal_blend_report import (
    DEFAULT_DOMAIN_SPECIALIST_SIGNAL_BLEND_REPORT_CONFIG_VERSION,
    DomainSpecialistSignalBlendConfig,
    DomainSpecialistSignalBlendInput,
    DomainSpecialistSignalBlendReasonCodeCount,
    DomainSpecialistSignalBlendReport,
    DomainSpecialistSignalBlendRow,
    build_domain_specialist_signal_blend_report,
    domain_specialist_signal_blend_report_digest,
    domain_specialist_signal_blend_report_payload,
)


GENERATED_AT = datetime(2026, 7, 12, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> DomainSpecialistSignalBlendConfig:
    values = {
        "config_version": DEFAULT_DOMAIN_SPECIALIST_SIGNAL_BLEND_REPORT_CONFIG_VERSION,
        "min_pass_team_calibration_confidence": d("0.750000"),
        "min_watch_team_calibration_confidence": d("0.500000"),
        "min_pass_source_reliability_score": d("0.700000"),
        "min_watch_source_reliability_score": d("0.450000"),
        "max_pass_cost_burden_ratio": d("0.080000"),
        "max_watch_cost_burden_ratio": d("0.200000"),
        "team_signal_weight": d("0.500000"),
        "baseline_signal_weight": d("0.300000"),
        "market_signal_weight": d("0.200000"),
    }
    values.update(overrides)
    return DomainSpecialistSignalBlendConfig(**values)


def signal_input(
    signal_ref: str = "macro-team-inflation-path",
    *,
    specialist_team: str = "macro-team",
    domain: str = "inflation-policy",
    team_forecast_probability: Decimal = d("0.720000"),
    baseline_probability: Decimal = d("0.600000"),
    market_probability: Decimal = d("0.550000"),
    team_calibration_confidence: Decimal = d("0.850000"),
    source_reliability_score: Decimal = d("0.800000"),
    cost_burden_ratio: Decimal = d("0.040000"),
    observed_at: datetime = GENERATED_AT,
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> DomainSpecialistSignalBlendInput:
    return DomainSpecialistSignalBlendInput(
        signal_ref=signal_ref,
        specialist_team=specialist_team,
        domain=domain,
        team_forecast_probability=team_forecast_probability,
        baseline_probability=baseline_probability,
        market_probability=market_probability,
        team_calibration_confidence=team_calibration_confidence,
        source_reliability_score=source_reliability_score,
        cost_burden_ratio=cost_burden_ratio,
        observed_at=observed_at,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: DomainSpecialistSignalBlendInput,
    cfg: DomainSpecialistSignalBlendConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> DomainSpecialistSignalBlendReport:
    return build_domain_specialist_signal_blend_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_report_is_readonly_block_with_decimal_zeroes() -> None:
    blend_report = report()

    assert type(blend_report) is DomainSpecialistSignalBlendReport
    assert is_dataclass(blend_report)
    assert blend_report.generated_at == GENERATED_AT
    assert (
        blend_report.config_version
        == "domain-specialist-signal-blend-report-v0"
    )
    assert blend_report.input_count == ZERO
    assert blend_report.pass_count == ZERO
    assert blend_report.watch_count == ZERO
    assert blend_report.block_count == ZERO
    assert blend_report.average_blended_probability is None
    assert blend_report.average_blend_weight is None
    assert blend_report.max_confidence_band == ZERO
    assert blend_report.status == "block"
    assert blend_report.reason_codes == ("no_domain_specialist_probability_signals",)
    assert blend_report.reason_code_counts == (
        DomainSpecialistSignalBlendReasonCodeCount(
            reason_code="no_domain_specialist_probability_signals",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert blend_report.rows == ()
    assert blend_report.paper_only is True
    assert blend_report.report_only is True
    assert blend_report.readonly is True


def test_blends_specialist_baseline_and_market_probabilities_with_attention_reasons() -> None:
    blend_report = report(
        signal_input(
            "macro-team-pass",
            team_forecast_probability=d("0.720000"),
            baseline_probability=d("0.600000"),
            market_probability=d("0.550000"),
            team_calibration_confidence=d("0.850000"),
            source_reliability_score=d("0.800000"),
            cost_burden_ratio=d("0.040000"),
            reason_codes=("domain_review_complete",),
        ),
        signal_input(
            "policy-team-watch",
            specialist_team="policy-team",
            domain="fiscal-policy",
            team_forecast_probability=d("0.400000"),
            baseline_probability=d("0.500000"),
            market_probability=d("0.650000"),
            team_calibration_confidence=d("0.620000"),
            source_reliability_score=d("0.600000"),
            cost_burden_ratio=d("0.120000"),
        ),
        signal_input(
            "energy-team-block",
            specialist_team="energy-team",
            domain="oil-supply",
            team_forecast_probability=d("0.820000"),
            baseline_probability=d("0.450000"),
            market_probability=d("0.400000"),
            team_calibration_confidence=d("0.420000"),
            source_reliability_score=d("0.300000"),
            cost_burden_ratio=d("0.260000"),
            reason_codes=("manual_review_requested",),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert blend_report.generated_at == GENERATED_AT
    assert blend_report.input_count == d("3.000000")
    assert blend_report.pass_count == d("1.000000")
    assert blend_report.watch_count == d("1.000000")
    assert blend_report.block_count == d("1.000000")
    assert blend_report.average_blended_probability == d("0.585000")
    assert blend_report.average_blend_weight == d("0.357800")
    assert blend_report.max_confidence_band == d("0.420000")
    assert blend_report.status == "block"
    assert blend_report.reason_codes == (
        "domain_specialist_signal_blend_block",
        "team_calibration_confidence_block",
        "source_reliability_score_block",
        "cost_burden_ratio_block",
        "team_calibration_confidence_watch",
        "source_reliability_score_watch",
        "cost_burden_ratio_watch",
        "team_market_divergence_attention",
    )

    block_row, pass_row, watch_row = blend_report.rows
    assert tuple(row.signal_ref for row in blend_report.rows) == (
        "energy-team-block",
        "macro-team-pass",
        "policy-team-watch",
    )
    assert type(block_row) is DomainSpecialistSignalBlendRow
    assert block_row.blended_probability == d("0.625000")
    assert block_row.blend_weight == d("0.093240")
    assert block_row.confidence_band == d("0.420000")
    assert block_row.status == "block"
    assert block_row.reason_codes == (
        "domain_specialist_signal_blend_block",
        "team_calibration_confidence_block",
        "source_reliability_score_block",
        "cost_burden_ratio_block",
        "team_market_divergence_attention",
        "manual_review_domain_specialist_signal_blend_block",
        "input_manual_review_requested",
    )

    assert pass_row.blended_probability == d("0.650000")
    assert pass_row.blend_weight == d("0.652800")
    assert pass_row.confidence_band == d("0.170000")
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == (
        "domain_specialist_signal_blend_pass",
        "input_domain_review_complete",
    )

    assert watch_row.blended_probability == d("0.480000")
    assert watch_row.blend_weight == d("0.327360")
    assert watch_row.confidence_band == d("0.250000")
    assert watch_row.status == "watch"
    assert "team_calibration_confidence_watch" in watch_row.reason_codes
    assert "source_reliability_score_watch" in watch_row.reason_codes
    assert "cost_burden_ratio_watch" in watch_row.reason_codes
    assert "team_market_divergence_attention" in watch_row.reason_codes


def test_payload_and_digest_are_deterministic_decimal_strings_and_safe() -> None:
    first = report(
        signal_input("domain-blend-z", reason_codes=("zeta", "alpha")),
        signal_input("domain-blend-a", domain="rates-policy"),
    )
    second = report(
        signal_input("domain-blend-a", domain="rates-policy"),
        signal_input("domain-blend-z", reason_codes=("alpha", "zeta")),
    )

    first_payload = domain_specialist_signal_blend_report_payload(first)
    second_payload = domain_specialist_signal_blend_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert domain_specialist_signal_blend_report_digest(first) == (
        domain_specialist_signal_blend_report_digest(second)
    )
    assert len(domain_specialist_signal_blend_report_digest(first)) == 64
    assert first_payload["rows"][0]["blended_probability"] == "0.650000"
    assert first_payload["rows"][0]["blend_weight"] == "0.652800"
    assert first_payload["rows"][0]["confidence_band"] == "0.170000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert ": 0." not in encoded
    assert not any(
        _has_forbidden_public_surface_key(key)
        for key in _walk_payload_keys(first_payload)
    )


def test_validation_rejects_non_decimal_values_bad_flags_and_inconsistent_rows() -> None:
    populated = report(signal_input())

    for value in (
        config(),
        signal_input(),
        populated,
        *populated.rows,
        *populated.reason_code_counts,
    ):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item_value is None:
                continue
            if item.name.endswith(
                (
                    "_count",
                    "_score",
                    "_confidence",
                    "_probability",
                    "_ratio",
                    "_weight",
                    "_band",
                ),
            ):
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].blended_probability = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="team_signal_weight"):
        config(team_signal_weight=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="baseline_signal_weight"):
        config(baseline_signal_weight=_DecimalSubclass("0.300000"))
    with pytest.raises(ValueError, match="weights"):
        config(market_signal_weight=d("0.300000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(signal_input(), generated_at=datetime(2026, 7, 12, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            signal_input(),
            generated_at=_DatetimeSubclass(2026, 7, 12, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        report(
            signal_input(observed_at=datetime(2026, 7, 12, 12, 1, tzinfo=UTC)),
        )
    with pytest.raises(ValueError, match="signal_ref"):
        signal_input(" raw-signal-ref")
    with pytest.raises(ValueError, match="signal_ref"):
        signal_input("market-slug-ref")
    with pytest.raises(ValueError, match="team_forecast_probability"):
        signal_input(team_forecast_probability=0.72)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="baseline_probability"):
        signal_input(baseline_probability=d("1.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        signal_input(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(signal_input(), paper_only=False)
    with pytest.raises(ValueError, match="blended_probability"):
        replace(populated.rows[0], blended_probability=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(populated, status="watch")


def test_owned_module_has_no_execution_trading_database_network_or_raw_public_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "domain_specialist_signal_blend_report.py"
    )
    source = module_path.read_text(encoding="utf-8")
    text = source.lower()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    call_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_roots = {
        "aiohttp",
        "httpx",
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
        "connect",
        "execute",
        "float",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    forbidden_terms = (
        "database",
        "wallet",
        "auth",
        "private-key",
        "private_key",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recommend",
        "sizing",
        "market_id",
        "market_slug",
        "condition_id",
        "token_id",
        "question",
        "source_text",
    )

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
    assert all(term not in text for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)


def _walk_payload_keys(value: object) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(key)
            keys.extend(_walk_payload_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_payload_keys(item))
    return tuple(keys)


def _has_forbidden_public_surface_key(key: str) -> bool:
    return key in {
        "market_id",
        "market_slug",
        "condition_id",
        "token_id",
        "question",
        "source_text",
        "source_url",
        "source_reference",
        "raw_text",
    }
