from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import importlib
import inspect
import json
from typing import get_args, get_type_hints

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_event_catalyst_volatility_pressure_report"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _api():
    return importlib.import_module(MODULE_NAME)


def _input(
    domain_label: str,
    *,
    catalyst_recency_hours: Decimal = d("240.000000"),
    evidence_contradiction_score: Decimal = d("0.050000"),
    liquidity_stress_score: Decimal = d("0.100000"),
    probability_movement_score: Decimal = d("0.100000"),
    resolution_proximity_hours: Decimal = d("240.000000"),
):
    api = _api()
    return api.ResearchEventCatalystVolatilityPressureInput(
        domain_label=domain_label,
        catalyst_recency_hours=catalyst_recency_hours,
        evidence_contradiction_score=evidence_contradiction_score,
        liquidity_stress_score=liquidity_stress_score,
        probability_movement_score=probability_movement_score,
        resolution_proximity_hours=resolution_proximity_hours,
    )


def _config():
    return _api().ResearchEventCatalystVolatilityPressureConfig()


def _report(*inputs):
    return _api().build_research_event_catalyst_volatility_pressure_report(
        inputs,
        config=_config(),
        generated_at=GENERATED_AT,
    )


def test_build_report_classifies_domain_pressure_rows_and_totals_deterministically() -> None:
    api = _api()
    block = _input(
        "policy-domain",
        catalyst_recency_hours=d("2.000000"),
        evidence_contradiction_score=d("0.700000"),
        liquidity_stress_score=d("0.800000"),
        probability_movement_score=d("0.900000"),
        resolution_proximity_hours=d("4.000000"),
    )
    watch = _input(
        "sports-domain",
        catalyst_recency_hours=d("24.000000"),
        evidence_contradiction_score=d("0.300000"),
        liquidity_stress_score=d("0.200000"),
        probability_movement_score=d("0.100000"),
        resolution_proximity_hours=d("48.000000"),
    )
    passed = _input("macro-domain")

    report = _report(watch, passed, block)
    repeated = _report(block, passed, watch)

    assert report.status == "block"
    assert report.reason_codes == (
        "catalyst_recency_present",
        "evidence_contradiction_present",
        "liquidity_stress_present",
        "probability_movement_present",
        "resolution_proximity_present",
    )
    assert report.domain_count == d("3.000000")
    assert report.pass_domain_count == d("1.000000")
    assert report.watch_domain_count == d("1.000000")
    assert report.block_domain_count == d("1.000000")
    assert report.flagged_domain_count == d("2.000000")
    assert report.flagged_domain_ratio == d("0.666667")
    assert report.catalyst_recency_domain_count == d("2.000000")
    assert report.evidence_contradiction_domain_count == d("2.000000")
    assert report.liquidity_stress_domain_count == d("1.000000")
    assert report.probability_movement_domain_count == d("1.000000")
    assert report.resolution_proximity_domain_count == d("2.000000")
    assert report.min_catalyst_recency_hours == d("2.000000")
    assert report.min_resolution_proximity_hours == d("4.000000")
    assert report.max_evidence_contradiction_score == d("0.700000")
    assert report.max_liquidity_stress_score == d("0.800000")
    assert report.max_probability_movement_score == d("0.900000")
    assert report.rows == repeated.rows
    assert report.derived_validation_digest == repeated.derived_validation_digest

    assert tuple(row.domain_label for row in report.rows) == (
        "policy-domain",
        "sports-domain",
        "macro-domain",
    )
    block_row = report.rows[0]
    assert block_row.status == "block"
    assert block_row.pressure_flag_count == d("5.000000")
    assert block_row.catalyst_recency is True
    assert block_row.evidence_contradiction is True
    assert block_row.liquidity_stress is True
    assert block_row.probability_movement is True
    assert block_row.resolution_proximity is True
    assert block_row.reason_codes == (
        "catalyst_recency",
        "evidence_contradiction",
        "liquidity_stress",
        "probability_movement",
        "resolution_proximity",
    )

    watch_row = report.rows[1]
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "catalyst_recency",
        "evidence_contradiction",
        "resolution_proximity",
    )

    pass_row = report.rows[2]
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == ("volatility_pressure_pass",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = api.research_event_catalyst_volatility_pressure_report_to_payload(report)
    json.dumps(payload, sort_keys=True)
    assert _float_paths(payload) == ()
    assert payload == api.research_event_catalyst_volatility_pressure_report_to_payload(
        repeated,
    )
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["domain_count"] == "3.000000"
    assert payload["flagged_domain_ratio"] == "0.666667"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_empty_report_passes_with_decimal_zeroes_and_stable_digest() -> None:
    report = _report()
    repeated = _report()

    assert report.status == "pass"
    assert report.reason_codes == ("volatility_pressure_pass",)
    assert report.domain_count == d("0.000000")
    assert report.flagged_domain_count == d("0.000000")
    assert report.flagged_domain_ratio == d("0.000000")
    assert report.min_catalyst_recency_hours == d("0.000000")
    assert report.min_resolution_proximity_hours == d("0.000000")
    assert report.max_evidence_contradiction_score == d("0.000000")
    assert report.max_liquidity_stress_score == d("0.000000")
    assert report.max_probability_movement_score == d("0.000000")
    assert report.rows == ()
    assert report.derived_validation_digest == repeated.derived_validation_digest


def test_public_dataclasses_are_frozen_decimal_only_and_flags_are_hard_required() -> None:
    api = _api()
    contract_classes = (
        api.ResearchEventCatalystVolatilityPressureConfig,
        api.ResearchEventCatalystVolatilityPressureInput,
        api.ResearchEventCatalystVolatilityPressureDomainRow,
        api.ResearchEventCatalystVolatilityPressureReport,
    )
    for contract_class in contract_classes:
        assert is_dataclass(contract_class)
        assert contract_class.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract_class)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        for field_name, hint in get_type_hints(contract_class).items():
            if field_name in {"paper_only", "report_only", "readonly"}:
                continue
            assert not _type_uses_float(hint)

    input_row = _input("frozen-domain")
    with pytest.raises(FrozenInstanceError):
        input_row.domain_label = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="catalyst_recency_watch_hours"):
        api.ResearchEventCatalystVolatilityPressureConfig(
            catalyst_recency_watch_hours=72,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="evidence_contradiction_score"):
        _input("float-domain", evidence_contradiction_score=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="liquidity_stress_score"):
        _input("subclass-domain", liquidity_stress_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="resolution_proximity_hours"):
        _input("int-domain", resolution_proximity_hours=24)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        api.build_research_event_catalyst_volatility_pressure_report(
            (),
            config=_config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="report_only"):
        replace(input_row, report_only=False)


def test_public_surface_rejects_identifier_like_labels_sensitive_terms_and_bad_digest() -> None:
    api = _api()

    with pytest.raises(ValueError, match="domain_label"):
        _input("0x" + "a" * 64)
    with pytest.raises(ValueError, match="domain_label"):
        _input(_join_parts("eve", "nt_id") + ":abc")
    with pytest.raises(ValueError, match="domain_label"):
        _input(_join_parts("mar", "ket_id") + ":123")
    with pytest.raises(ValueError, match="domain_label"):
        _input(_join_parts("sou", "rce_id") + ":abc")
    with pytest.raises(ValueError, match="domain_label"):
        _input(_join_parts("wal", "let") + "-review")

    report = _report(_input("digest-domain"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.ResearchEventCatalystVolatilityPressureReport(
            generated_at=report.generated_at,
            config_version=report.config_version,
            status=report.status,
            reason_codes=report.reason_codes,
            domain_count=report.domain_count,
            pass_domain_count=report.pass_domain_count,
            watch_domain_count=report.watch_domain_count,
            block_domain_count=report.block_domain_count,
            flagged_domain_count=report.flagged_domain_count,
            catalyst_recency_domain_count=report.catalyst_recency_domain_count,
            evidence_contradiction_domain_count=(
                report.evidence_contradiction_domain_count
            ),
            liquidity_stress_domain_count=report.liquidity_stress_domain_count,
            probability_movement_domain_count=(
                report.probability_movement_domain_count
            ),
            resolution_proximity_domain_count=(
                report.resolution_proximity_domain_count
            ),
            flagged_domain_ratio=report.flagged_domain_ratio,
            min_catalyst_recency_hours=report.min_catalyst_recency_hours,
            min_resolution_proximity_hours=report.min_resolution_proximity_hours,
            max_evidence_contradiction_score=(
                report.max_evidence_contradiction_score
            ),
            max_liquidity_stress_score=report.max_liquidity_stress_score,
            max_probability_movement_score=report.max_probability_movement_score,
            rows=report.rows,
            derived_validation_digest="not-the-digest",
        )


def test_module_is_pure_report_only_without_io_or_action_surface() -> None:
    api = _api()
    public_names = tuple(api.__all__)
    source = inspect.getsource(api).lower()
    tree = ast.parse(source)

    assert api.__all__ == (
        "DEFAULT_RESEARCH_EVENT_CATALYST_VOLATILITY_PRESSURE_REPORT_CONFIG_VERSION",
        "ResearchEventCatalystVolatilityPressureConfig",
        "ResearchEventCatalystVolatilityPressureDomainRow",
        "ResearchEventCatalystVolatilityPressureInput",
        "ResearchEventCatalystVolatilityPressureReport",
        "build_research_event_catalyst_volatility_pressure_report",
        "research_event_catalyst_volatility_pressure_report_to_payload",
    )
    assert api.VOLATILITY_PRESSURE_STATUSES == ("pass", "watch", "block")
    assert "float(" not in source
    for restricted in (
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
        _join_parts("rec", "ommend"),
        _join_parts("pos", "ition"),
        _join_parts("pos", "ition sizing"),
        _join_parts("wal", "let"),
        _join_parts("au", "th"),
        _join_parts("ord", "er"),
        _join_parts("tr", "ade"),
        _join_parts("li", "ve"),
        _join_parts("eve", "nt_id"),
        _join_parts("mar", "ket_id"),
        _join_parts("sou", "rce_id"),
        "condition_id",
    ):
        assert restricted not in source
        assert all(restricted not in name.lower() for name in public_names)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "patch",
                "place",
                "post",
                "put",
                "request",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _float_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if isinstance(value, float):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()


def _type_uses_float(value: object) -> bool:
    if value is float:
        return True
    return any(_type_uses_float(item) for item in get_args(value))


def _join_parts(*parts: str) -> str:
    return "".join(parts)
