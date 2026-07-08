from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_cross_domain_catalyst_correlation_report"
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_cross_domain_catalyst_correlation_report.py",
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _api() -> Any:
    return importlib.import_module(MODULE_NAME)


def _config(**overrides: object) -> object:
    api = _api()
    values = {
        "config_version": (
            api.DEFAULT_RESEARCH_CROSS_DOMAIN_CATALYST_CORRELATION_CONFIG_VERSION
        ),
        "watch_correlation_pressure": d("0.450000"),
        "block_correlation_pressure": d("0.760000"),
        "shared_intensity_watch": d("0.500000"),
        "shared_intensity_high": d("0.750000"),
        "shared_conflict_watch": d("0.350000"),
        "shared_conflict_high": d("0.600000"),
        "intensity_weight": d("0.500000"),
        "freshness_weight": d("0.250000"),
        "conflict_weight": d("0.250000"),
    }
    values.update(overrides)
    return api.ResearchCrossDomainCatalystCorrelationConfig(**values)


def _input(domain: str, **overrides: object) -> object:
    api = _api()
    defaults = {
        "politics": {
            "aggregate_intensity": d("0.900000"),
            "aggregate_freshness": d("0.850000"),
            "aggregate_conflict": d("0.700000"),
        },
        "crypto": {
            "aggregate_intensity": d("0.880000"),
            "aggregate_freshness": d("0.800000"),
            "aggregate_conflict": d("0.680000"),
        },
        "equities": {
            "aggregate_intensity": d("0.600000"),
            "aggregate_freshness": d("0.700000"),
            "aggregate_conflict": d("0.300000"),
        },
        "gold": {
            "aggregate_intensity": d("0.580000"),
            "aggregate_freshness": d("0.680000"),
            "aggregate_conflict": d("0.250000"),
        },
        "soccer": {
            "aggregate_intensity": d("0.250000"),
            "aggregate_freshness": d("0.900000"),
            "aggregate_conflict": d("0.150000"),
        },
        "basketball": {
            "aggregate_intensity": d("0.220000"),
            "aggregate_freshness": d("0.880000"),
            "aggregate_conflict": d("0.180000"),
        },
    }
    values = dict(defaults[domain])
    values.update(overrides)
    return api.ResearchCrossDomainCatalystCorrelationInput(domain=domain, **values)


def _report(
    *inputs: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> object:
    return _api().build_research_cross_domain_catalyst_correlation_report(
        inputs,
        config=cfg or _config(),
        generated_at=generated_at,
    )


def _walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(_walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(_walk_values(item))
        return tuple(nested)
    return (value,)


def test_builds_public_safe_cross_domain_correlation_report() -> None:
    api = _api()
    report = _report(
        _input("politics"),
        _input("crypto"),
        _input("equities"),
        _input("gold"),
        _input("soccer"),
        _input("basketball"),
    )

    assert type(report) is api.ResearchCrossDomainCatalystCorrelationReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        api.DEFAULT_RESEARCH_CROSS_DOMAIN_CATALYST_CORRELATION_CONFIG_VERSION
    )
    assert report.status == "block"
    assert report.domain_count == d("6.000000")
    assert report.pair_count == d("15.000000")
    assert report.pass_count == d("9.000000")
    assert report.watch_count == d("5.000000")
    assert report.block_count == d("1.000000")
    assert report.average_correlation_pressure == d("0.435376")
    assert report.max_correlation_pressure == d("0.801097")
    assert report.max_aggregate_intensity == d("0.900000")
    assert report.max_aggregate_conflict == d("0.700000")
    assert report.min_aggregate_freshness == d("0.680000")
    assert report.covered_domains == (
        "basketball",
        "crypto",
        "equities",
        "gold",
        "politics",
        "soccer",
    )
    assert report.reason_codes == (
        "correlation_pressure_block",
        "correlation_pressure_watch",
        "shared_conflict_high",
        "shared_conflict_watch",
        "shared_intensity_high",
        "shared_intensity_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert len(report.rows) == 15
    assert tuple(row.status for row in report.rows).count("block") == 1
    blocked = next(row for row in report.rows if row.status == "block")
    assert (blocked.domain_a, blocked.domain_b) == ("crypto", "politics")
    assert blocked.domain_a_pressure == d("0.810000")
    assert blocked.domain_b_pressure == d("0.837500")
    assert blocked.average_intensity == d("0.890000")
    assert blocked.average_freshness == d("0.825000")
    assert blocked.average_conflict == d("0.690000")
    assert blocked.pressure_alignment == d("0.972500")
    assert blocked.correlation_pressure == d("0.801097")
    assert blocked.reason_codes == (
        "correlation_pressure_block",
        "shared_conflict_high",
        "shared_intensity_high",
    )

    watched = next(
        row
        for row in report.rows
        if (row.domain_a, row.domain_b) == ("equities", "gold")
    )
    assert watched.status == "watch"
    assert watched.correlation_pressure == d("0.521503")
    assert watched.reason_codes == (
        "correlation_pressure_watch",
        "shared_intensity_watch",
    )

    passed = next(
        row
        for row in report.rows
        if (row.domain_a, row.domain_b) == ("basketball", "soccer")
    )
    assert passed.status == "pass"
    assert passed.correlation_pressure == d("0.376484")
    assert passed.reason_codes == ("correlation_pressure_pass",)


def test_payload_is_deterministic_digest_checked_and_decimal_strings() -> None:
    api = _api()
    inputs = (
        _input("soccer"),
        _input("crypto"),
        _input("politics"),
        _input("basketball"),
    )
    report = _report(*inputs)
    shuffled_report = _report(*reversed(inputs))

    payload = api.research_cross_domain_catalyst_correlation_report_payload(report)
    payload_again = api.research_cross_domain_catalyst_correlation_report_payload(report)
    shuffled_payload = api.research_cross_domain_catalyst_correlation_report_payload(
        shuffled_report,
    )

    assert payload == payload_again
    assert payload == shuffled_payload
    assert payload == report.payload
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["domain_count"] == "4.000000"
    assert payload["pair_count"] == "6.000000"
    assert payload["rows"][0]["correlation_pressure"] == "0.801097"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64

    encoded = json.dumps(payload, sort_keys=True)
    rendered = repr(payload).casefold()
    assert "raw-event" not in encoded
    assert "market_id" not in rendered
    assert "market_slug" not in rendered
    assert "source_id" not in rendered
    assert "source_text" not in rendered
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert not any(type(value) is int for value in _walk_values(payload))

    tampered = dict(payload)
    tampered["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.research_cross_domain_catalyst_correlation_report_payload(tampered)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        api.research_cross_domain_catalyst_correlation_report_payload(downgraded)


def test_empty_and_single_domain_inputs_are_report_only_blocks() -> None:
    api = _api()
    empty_report = _report()
    single_report = _report(_input("gold"))

    assert empty_report.status == "block"
    assert empty_report.domain_count == ZERO
    assert empty_report.pair_count == ZERO
    assert empty_report.rows == ()
    assert empty_report.reason_codes == ("insufficient_domain_coverage",)

    assert single_report.status == "block"
    assert single_report.domain_count == d("1.000000")
    assert single_report.pair_count == ZERO
    assert single_report.covered_domains == ("gold",)
    assert single_report.reason_codes == ("insufficient_domain_coverage",)

    payload = api.research_cross_domain_catalyst_correlation_report_payload(empty_report)
    assert payload["reason_code_counts"] == [
        {
            "reason_code": "insufficient_domain_coverage",
            "count": "1.000000",
            "row_ratio": "1.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]

    rendered = repr(payload).casefold()
    forbidden_terms = (
        "recommendation",
        "recommended",
        "sizing",
        "size",
        "stake",
        "position",
        "allocation",
        "buy",
        "sell",
    )
    assert not any(term in rendered for term in forbidden_terms)


def test_frozen_dataclasses_decimal_only_and_validation_guards() -> None:
    api = _api()
    report = _report(_input("politics"), _input("crypto"))

    for cls_name in (
        "ResearchCrossDomainCatalystCorrelationConfig",
        "ResearchCrossDomainCatalystCorrelationInput",
        "ResearchCrossDomainCatalystCorrelationPairRow",
        "ResearchCrossDomainCatalystCorrelationReasonCodeCount",
        "ResearchCrossDomainCatalystCorrelationReport",
    ):
        assert is_dataclass(getattr(api, cls_name))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].correlation_pressure = d("0.100000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="domain"):
        api.ResearchCrossDomainCatalystCorrelationInput(
            domain="weather",
            aggregate_intensity=d("0.500000"),
            aggregate_freshness=d("0.500000"),
            aggregate_conflict=d("0.500000"),
        )
    with pytest.raises(ValueError, match="aggregate_intensity"):
        _input("politics", aggregate_intensity=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="aggregate_freshness"):
        _input("politics", aggregate_freshness=d("1.000001"))
    with pytest.raises(ValueError, match="aggregate_conflict"):
        _input("politics", aggregate_conflict=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        _report(_input("gold"), _input("soccer"), generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="paper_only"):
        _input("politics", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="unique domain"):
        _report(_input("gold"), _input("gold"))
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="hold")

    for value in (report, *report.rows, *report.reason_code_counts):
        for field in fields(value):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            item = getattr(value, field.name)
            if isinstance(item, Decimal):
                assert type(item) is Decimal
            if field.name.endswith(("_count", "_pressure", "_intensity", "_freshness", "_conflict", "_alignment", "_ratio")):
                assert type(item) is Decimal


def test_rejects_unsafe_public_surfaces() -> None:
    api = _api()
    unsafe_terms = (
        "event_id",
        "event_text",
        "market_id",
        "market_slug",
        "source_id",
        "source_text",
        "wallet",
        "auth",
        "order",
        "trade",
        "private_key",
        "database",
        "network",
        "live_execution",
    )

    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe"):
            api.research_cross_domain_catalyst_correlation_report_payload(
                {
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                    term: "blocked",
                    "derived_validation_digest": "0" * 64,
                },
            )


def test_source_has_no_io_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
    imports: list[str] = []
    calls: list[str] = []
    string_values: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            string_values.append(node.value.casefold())

    forbidden_imports = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "supabase",
    }
    forbidden_calls = {"open", "connect", "execute", "post", "put", "patch", "delete"}
    assert forbidden_imports.isdisjoint(imports)
    assert forbidden_calls.isdisjoint(calls)
    assert "event_id" not in source
    assert "event_text" not in source
    assert "market_id" not in source
    assert "market_slug" not in source
    assert "source_id" not in source
    assert "source_text" not in source
    assert not any("recommendation" in value for value in string_values)
    assert not any("sizing" in value for value in string_values)
