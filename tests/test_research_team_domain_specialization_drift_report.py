from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_domain_specialization_drift_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_domain_specialization_drift_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def generated_at():
    from datetime import UTC, datetime

    return datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def signal(**overrides: object):
    module = api()
    values = {
        "team_code": "team_macro",
        "domain": "politics",
        "aggregate_expertise_fit": d("0.900000"),
        "calibration_score": d("0.900000"),
        "memory_freshness": d("0.900000"),
        "source_coverage": d("0.900000"),
        "capacity_pressure": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainSpecializationSignal(**values)


def report(*signals: object):
    module = api()
    return module.build_research_team_domain_specialization_drift_report(
        signals,
        config=module.ResearchTeamDomainSpecializationDriftConfig(),
        generated_at=generated_at(),
    )


def assert_no_float_or_int_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_float_or_int_values(child)
    if isinstance(value, list):
        for child in value:
            assert_no_float_or_int_values(child)


def test_build_report_detects_domain_specialization_drift_with_exact_statuses() -> None:
    module = api()
    rows = (
        signal(domain="politics", team_code="team_politics"),
        signal(
            domain="crypto",
            team_code="team_crypto",
            aggregate_expertise_fit=d("0.720000"),
            calibration_score=d("0.700000"),
            memory_freshness=d("0.650000"),
            source_coverage=d("0.680000"),
            capacity_pressure=d("0.620000"),
        ),
        signal(
            domain="equities",
            team_code="team_equities",
            aggregate_expertise_fit=d("0.400000"),
            calibration_score=d("0.420000"),
            memory_freshness=d("0.450000"),
            source_coverage=d("0.480000"),
            capacity_pressure=d("0.900000"),
        ),
        signal(domain="gold", team_code="team_gold"),
        signal(domain="soccer", team_code="team_soccer"),
        signal(domain="basketball", team_code="team_basketball"),
    )

    result = report(*reversed(rows))

    assert is_dataclass(result)
    assert module.DOMAIN_SPECIALIZATION_DRIFT_STATUSES == ("pass", "watch", "block")
    assert module.RESEARCH_TEAM_DOMAIN_SPECIALIZATION_DOMAINS == (
        "politics",
        "crypto",
        "equities",
        "gold",
        "soccer",
        "basketball",
    )
    assert result.report_status == "block"
    assert result.row_count == d("6.000000")
    assert result.domain_count == d("6.000000")
    assert result.team_count == d("6.000000")
    assert result.pass_count == d("4.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.average_specialization_fit == d("0.786667")
    assert result.average_calibration_score == d("0.786667")
    assert result.average_memory_freshness == d("0.783333")
    assert result.average_source_coverage == d("0.793333")
    assert result.average_capacity_pressure == d("0.320000")
    assert result.max_drift_score == d("0.680625")
    assert [row.domain for row in result.rows] == [
        "politics",
        "crypto",
        "equities",
        "gold",
        "soccer",
        "basketball",
    ]
    assert [row.drift_status for row in result.rows] == [
        "pass",
        "watch",
        "block",
        "pass",
        "pass",
        "pass",
    ]
    assert result.rows[0].aggregate_readiness_score == d("0.900000")
    assert result.rows[0].drift_score == d("0.100000")
    assert result.rows[1].aggregate_readiness_score == d("0.687500")
    assert result.rows[1].drift_score == d("0.420125")
    assert result.rows[2].aggregate_readiness_score == d("0.437500")
    assert result.rows[2].drift_score == d("0.680625")
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = module.research_team_domain_specialization_drift_report_payload(result)
    assert payload == result.payload
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)
    assert module.validate_research_team_domain_specialization_drift_report_payload(payload)


def test_payload_and_digest_are_deterministic_for_same_public_inputs() -> None:
    left = report(
        signal(team_code="team_basketball", domain="basketball"),
        signal(team_code="team_politics", domain="politics"),
    )
    right = report(
        signal(team_code="team_politics", domain="politics"),
        signal(team_code="team_basketball", domain="basketball"),
    )

    assert left.derived_validation_digest == right.derived_validation_digest
    assert left.payload == right.payload
    encoded = json.dumps(left.payload, sort_keys=True)
    assert left.derived_validation_digest in encoded


def test_validation_requires_decimal_inputs_public_domains_flags_and_frozen_outputs() -> None:
    module = api()
    result = report(signal())

    with pytest.raises(FrozenInstanceError):
        result.report_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="aggregate_expertise_fit must be a Decimal"):
        signal(aggregate_expertise_fit=1)

    with pytest.raises(ValueError, match="calibration_score must be a Decimal"):
        signal(calibration_score=_DecimalSubclass("0.900000"))

    with pytest.raises(ValueError, match="capacity_pressure must be between 0 and 1"):
        signal(capacity_pressure=d("1.000001"))

    with pytest.raises(ValueError, match="domain must be supported"):
        signal(domain="tennis")

    with pytest.raises(ValueError, match="team_code must be a public code"):
        signal(team_code="Team Politics")

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(signal(), paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="drift_status must be supported"):
        module.ResearchTeamDomainSpecializationDriftRow(
            team_code="team_macro",
            domain="politics",
            aggregate_expertise_fit=d("0.900000"),
            calibration_score=d("0.900000"),
            memory_freshness=d("0.900000"),
            source_coverage=d("0.900000"),
            capacity_pressure=d("0.100000"),
            aggregate_readiness_score=d("0.900000"),
            drift_score=d("0.090000"),
            drift_status="clear",
            reason_codes=("domain_specialization_pass",),
        )


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    module = api()
    decimal_fields = {
        "aggregate_expertise_fit",
        "calibration_score",
        "memory_freshness",
        "source_coverage",
        "capacity_pressure",
        "watch_drift_score",
        "block_drift_score",
        "watch_readiness_floor",
        "block_readiness_floor",
        "watch_capacity_pressure",
        "block_capacity_pressure",
        "aggregate_readiness_score",
        "drift_score",
        "row_count",
        "domain_count",
        "team_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_specialization_fit",
        "average_calibration_score",
        "average_memory_freshness",
        "average_source_coverage",
        "average_capacity_pressure",
        "max_drift_score",
        "count",
    }

    for cls in (
        module.ResearchTeamDomainSpecializationDriftConfig,
        module.ResearchTeamDomainSpecializationSignal,
        module.ResearchTeamDomainSpecializationDriftRow,
        module.ResearchTeamDomainSpecializationDriftReasonCodeCount,
        module.ResearchTeamDomainSpecializationDriftReport,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in decimal_fields:
                assert hints[item.name] is Decimal


def test_payload_validation_rejects_tampering_and_unsafe_numeric_values() -> None:
    module = api()
    payload = report(signal()).payload

    tampered = dict(payload)
    tampered["report_status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.validate_research_team_domain_specialization_drift_report_payload(tampered)

    with pytest.raises(ValueError, match="payload must be readonly"):
        module.validate_research_team_domain_specialization_drift_report_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.validate_research_team_domain_specialization_drift_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "row_count": 1.0,
            },
        )

    with pytest.raises(ValueError, match="JSON numeric value must use Decimal strings"):
        module.validate_research_team_domain_specialization_drift_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "row_count": 1,
            },
        )


def test_module_scope_is_report_only_without_raw_identifiers_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "event_id",
        "market_id",
        "market_slug",
        "source_id",
        "source_url",
        "source_name",
        "source_text",
        "raw_source",
        "auth",
        "wallet",
        "order",
        "trade",
        "database",
        "network",
        "requests",
        "urllib",
        "socket",
        "sqlite",
        "open(",
        "recommend",
        "sizing",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}
