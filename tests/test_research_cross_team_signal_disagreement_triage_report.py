from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_cross_team_signal_disagreement_triage_report"
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_cross_team_signal_disagreement_triage_report.py",
)


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
            api.DEFAULT_RESEARCH_CROSS_TEAM_SIGNAL_DISAGREEMENT_TRIAGE_CONFIG_VERSION
        ),
        "pass_triage_score": d("0.750000"),
        "watch_triage_score": d("0.500000"),
        "block_model_disagreement": d("0.700000"),
        "block_signal_spread": d("0.600000"),
        "watch_model_disagreement": d("0.350000"),
        "watch_signal_spread": d("0.300000"),
        "freshness_watch_age_hours": d("24.000000"),
        "freshness_block_age_hours": d("72.000000"),
        "min_team_count": d("2.000000"),
        "confidence_weight": d("0.300000"),
        "evidence_quality_weight": d("0.250000"),
        "freshness_weight": d("0.200000"),
        "model_agreement_weight": d("0.150000"),
        "signal_agreement_weight": d("0.100000"),
    }
    values.update(overrides)
    return api.ResearchCrossTeamSignalDisagreementTriageConfig(**values)


def _input(domain_key: str = "macro", team_key: str = "research", **overrides: object) -> object:
    api = _api()
    values = {
        "domain_key": domain_key,
        "team_key": team_key,
        "aggregate_confidence": d("0.900000"),
        "evidence_quality": d("0.850000"),
        "freshness_age_hours": d("6.000000"),
        "model_disagreement": d("0.100000"),
        "signal_value": d("0.700000"),
    }
    values.update(overrides)
    return api.ResearchCrossTeamSignalDisagreementTriageInput(**values)


def _report(
    *inputs: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> object:
    return _api().build_research_cross_team_signal_disagreement_triage_report(
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


def test_builds_public_triage_report_across_team_disagreements() -> None:
    api = _api()
    report = _report(
        _input(
            "raw-event-alpha?market=hidden&source=private",
            "fundamental",
            aggregate_confidence=d("0.920000"),
            evidence_quality=d("0.880000"),
            freshness_age_hours=d("6.000000"),
            model_disagreement=d("0.100000"),
            signal_value=d("0.720000"),
        ),
        _input(
            "raw-event-alpha?market=hidden&source=private",
            "technical",
            aggregate_confidence=d("0.860000"),
            evidence_quality=d("0.820000"),
            freshness_age_hours=d("12.000000"),
            model_disagreement=d("0.150000"),
            signal_value=d("0.680000"),
        ),
        _input(
            "policy-domain",
            "fresh-watch",
            aggregate_confidence=d("0.650000"),
            evidence_quality=d("0.700000"),
            freshness_age_hours=d("30.000000"),
            model_disagreement=d("0.300000"),
            signal_value=d("0.550000"),
        ),
        _input(
            "policy-domain",
            "stale-watch",
            aggregate_confidence=d("0.620000"),
            evidence_quality=d("0.680000"),
            freshness_age_hours=d("48.000000"),
            model_disagreement=d("0.320000"),
            signal_value=d("0.300000"),
        ),
        _input(
            "geopolitical-domain",
            "high-team",
            aggregate_confidence=d("0.900000"),
            evidence_quality=d("0.850000"),
            freshness_age_hours=d("8.000000"),
            model_disagreement=d("0.820000"),
            signal_value=d("0.950000"),
        ),
        _input(
            "geopolitical-domain",
            "low-team",
            aggregate_confidence=d("0.880000"),
            evidence_quality=d("0.800000"),
            freshness_age_hours=d("10.000000"),
            model_disagreement=d("0.780000"),
            signal_value=d("0.120000"),
        ),
    )

    assert type(report) is api.ResearchCrossTeamSignalDisagreementTriageReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        api.DEFAULT_RESEARCH_CROSS_TEAM_SIGNAL_DISAGREEMENT_TRIAGE_CONFIG_VERSION
    )
    assert report.status == "block"
    assert report.domain_count == d("3.000000")
    assert report.signal_count == d("6.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_triage_score == d("0.736722")
    assert report.max_model_disagreement == d("0.800000")
    assert report.max_signal_spread == d("0.830000")
    assert report.max_freshness_age_hours == d("39.000000")
    assert report.min_team_count == d("2.000000")
    assert report.reason_codes == (
        "model_disagreement_block",
        "signal_spread_block",
        "freshness_watch",
        "triage_score_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    blocked, watched, passed = report.rows
    assert blocked.domain_digest.startswith("sha256:")
    assert "geopolitical-domain" not in blocked.domain_digest
    assert blocked.team_count == d("2.000000")
    assert blocked.average_aggregate_confidence == d("0.890000")
    assert blocked.average_evidence_quality == d("0.825000")
    assert blocked.average_freshness_age_hours == d("9.000000")
    assert blocked.freshness_score == d("0.875000")
    assert blocked.average_model_disagreement == d("0.800000")
    assert blocked.model_agreement_score == d("0.200000")
    assert blocked.signal_spread == d("0.830000")
    assert blocked.signal_agreement_score == d("0.170000")
    assert blocked.triage_score == d("0.695250")
    assert blocked.reason_codes == (
        "model_disagreement_block",
        "signal_spread_block",
        "triage_score_watch",
    )

    assert watched.status == "watch"
    assert watched.triage_score == d("0.633167")
    assert watched.reason_codes == (
        "freshness_watch",
        "triage_score_watch",
    )

    assert passed.status == "pass"
    assert passed.triage_score == d("0.881750")
    assert passed.reason_codes == ("cross_team_disagreement_triage_pass",)


def test_payload_is_deterministic_redacted_digest_checked_and_decimal_strings() -> None:
    api = _api()
    report = _report(
        _input("domain-a", "team-a", signal_value=d("0.700000")),
        _input("domain-a", "team-b", signal_value=d("0.680000")),
    )

    payload = api.research_cross_team_signal_disagreement_triage_report_payload(report)
    payload_again = api.research_cross_team_signal_disagreement_triage_report_payload(report)

    assert payload == payload_again
    assert payload == report.payload
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["domain_count"] == "1.000000"
    assert payload["rows"][0]["triage_score"] == "0.898833"
    assert payload["rows"][0]["domain_digest"].startswith("sha256:")
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64

    encoded = json.dumps(payload, sort_keys=True)
    rendered = repr(payload).casefold()
    assert "domain-a" not in encoded
    assert "team-a" not in encoded
    assert "market" not in rendered
    assert "source" not in rendered
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert not any(type(value) is int for value in _walk_values(payload))

    tampered = dict(payload)
    tampered["status"] = "block"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.research_cross_team_signal_disagreement_triage_report_payload(tampered)

    downgraded = dict(payload)
    downgraded["report_only"] = False
    with pytest.raises(ValueError, match="report_only"):
        api.research_cross_team_signal_disagreement_triage_report_payload(downgraded)


def test_empty_input_is_report_only_block_without_recommendation_or_sizing() -> None:
    report = _report()
    payload = _api().research_cross_team_signal_disagreement_triage_report_payload(report)

    assert report.status == "block"
    assert report.domain_count == ZERO
    assert report.signal_count == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("empty_input",)
    assert payload["reason_code_counts"] == [
        {
            "reason_code": "empty_input",
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
    report = _report(
        _input("domain-a", "team-a"),
        _input("domain-a", "team-b", signal_value=d("0.680000")),
    )

    for cls_name in (
        "ResearchCrossTeamSignalDisagreementTriageConfig",
        "ResearchCrossTeamSignalDisagreementTriageInput",
        "ResearchCrossTeamSignalDisagreementTriageRow",
        "ResearchCrossTeamSignalDisagreementTriageReasonCodeCount",
        "ResearchCrossTeamSignalDisagreementTriageReport",
    ):
        assert is_dataclass(getattr(api, cls_name))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].triage_score = d("0.100000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="aggregate_confidence"):
        _input("domain-a", "team-a", aggregate_confidence=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_quality"):
        _input("domain-a", "team-a", evidence_quality=d("1.000001"))
    with pytest.raises(ValueError, match="freshness_age_hours"):
        _input("domain-a", "team-a", freshness_age_hours=d("-0.000001"))
    with pytest.raises(ValueError, match="generated_at"):
        _report(generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="signal_value"):
        _input("domain-a", "team-a", signal_value=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="paper_only"):
        _input("domain-a", "team-a", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    for value in (report, *report.rows, *report.reason_code_counts):
        for field in fields(value):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            item = getattr(value, field.name)
            if isinstance(item, Decimal):
                assert type(item) is Decimal
            if field.name.endswith(("_count", "_score", "_hours", "_ratio", "_spread")):
                assert type(item) is Decimal


def test_rejects_wallet_auth_order_trade_private_key_and_db_network_surfaces() -> None:
    api = _api()
    unsafe_terms = (
        "wallet",
        "auth",
        "order",
        "trade",
        "private_key",
        "database",
        "network",
        "mutation",
    )

    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe"):
            _input("domain-a", f"team-{term}")
        with pytest.raises(ValueError, match="unsafe"):
            api.research_cross_team_signal_disagreement_triage_report_payload(
                {
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                    term: "blocked",
                    "derived_validation_digest": "0" * 64,
                },
            )


def test_source_has_no_network_db_or_execution_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
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
    assert not any("recommendation" in value for value in string_values)
    assert not any("sizing" in value for value in string_values)
