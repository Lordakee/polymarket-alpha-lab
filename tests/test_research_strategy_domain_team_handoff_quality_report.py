from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_domain_team_handoff_quality_report import (
    DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_HANDOFF_QUALITY_REPORT_CONFIG_VERSION,
    ResearchStrategyDomainTeamHandoffQualityConfig,
    ResearchStrategyDomainTeamHandoffQualityInput,
    ResearchStrategyDomainTeamHandoffQualityReasonCodeCount,
    ResearchStrategyDomainTeamHandoffQualityReport,
    ResearchStrategyDomainTeamHandoffQualityRow,
    build_research_strategy_domain_team_handoff_quality_report,
    research_strategy_domain_team_handoff_quality_report_digest,
    research_strategy_domain_team_handoff_quality_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchStrategyDomainTeamHandoffQualityConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_HANDOFF_QUALITY_REPORT_CONFIG_VERSION
        ),
    }
    values.update(overrides)
    return ResearchStrategyDomainTeamHandoffQualityConfig(**values)


def team(
    domain_team_label: str,
    *,
    handoff_completeness: Decimal = d("0.900000"),
    unresolved_conflict_pressure: Decimal = d("0.100000"),
    evidence_maturity: Decimal = d("0.800000"),
    forecast_readiness_pressure: Decimal = d("0.200000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyDomainTeamHandoffQualityInput:
    return ResearchStrategyDomainTeamHandoffQualityInput(
        domain_team_label=domain_team_label,
        handoff_completeness=handoff_completeness,
        unresolved_conflict_pressure=unresolved_conflict_pressure,
        evidence_maturity=evidence_maturity,
        forecast_readiness_pressure=forecast_readiness_pressure,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchStrategyDomainTeamHandoffQualityInput,
    cfg: ResearchStrategyDomainTeamHandoffQualityConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyDomainTeamHandoffQualityReport:
    return build_research_strategy_domain_team_handoff_quality_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_handoff_quality_report_blocks_for_missing_team_inputs() -> None:
    quality_report = report()

    assert type(quality_report) is ResearchStrategyDomainTeamHandoffQualityReport
    assert quality_report.generated_at == GENERATED_AT
    assert quality_report.team_count == d("0")
    assert quality_report.pass_count == d("0")
    assert quality_report.watch_count == d("0")
    assert quality_report.block_count == d("0")
    assert quality_report.average_handoff_quality_score is None
    assert quality_report.min_handoff_completeness is None
    assert quality_report.min_evidence_maturity is None
    assert quality_report.max_unresolved_conflict_pressure is None
    assert quality_report.max_forecast_readiness_pressure is None
    assert quality_report.status == "block"
    assert quality_report.reason_codes == ("no_domain_team_handoff_inputs",)
    assert quality_report.reason_code_counts == (
        ResearchStrategyDomainTeamHandoffQualityReasonCodeCount(
            reason_code="no_domain_team_handoff_inputs",
            count=d("1"),
        ),
    )
    assert quality_report.rows == ()
    assert len(quality_report.derived_validation_digest) == 64
    assert quality_report.paper_only is True
    assert quality_report.report_only is True
    assert quality_report.readonly is True


def test_handoff_quality_aggregates_pass_watch_and_block_pressure() -> None:
    quality_report = report(
        team(
            "domain-team-alpha",
            reason_codes=("handoff_review_ready",),
        ),
        team(
            "domain-team-beta",
            handoff_completeness=d("0.650000"),
            unresolved_conflict_pressure=d("0.300000"),
            evidence_maturity=d("0.600000"),
            forecast_readiness_pressure=d("0.450000"),
        ),
        team(
            "domain-team-gamma",
            handoff_completeness=d("0.400000"),
            unresolved_conflict_pressure=d("0.800000"),
            evidence_maturity=d("0.300000"),
            forecast_readiness_pressure=d("0.750000"),
            reason_codes=("conflict_review_needed",),
        ),
    )

    blocked, watched, passed = quality_report.rows
    assert tuple(row.status for row in quality_report.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert quality_report.team_count == d("3")
    assert quality_report.pass_count == d("1")
    assert quality_report.watch_count == d("1")
    assert quality_report.block_count == d("1")
    assert quality_report.average_handoff_quality_score == d("0.587500")
    assert quality_report.min_handoff_completeness == d("0.400000")
    assert quality_report.min_evidence_maturity == d("0.300000")
    assert quality_report.max_unresolved_conflict_pressure == d("0.800000")
    assert quality_report.max_forecast_readiness_pressure == d("0.750000")
    assert quality_report.status == "block"
    assert quality_report.paper_only is True
    assert quality_report.report_only is True
    assert quality_report.readonly is True

    assert blocked.domain_team_label == "domain-team-gamma"
    assert blocked.handoff_quality_score == d("0.287500")
    assert blocked.conflict_resolution_score == d("0.200000")
    assert blocked.forecast_stability_score == d("0.250000")
    assert blocked.lowest_dimension_score == d("0.200000")
    assert blocked.reason_codes == (
        "domain_team_handoff_quality_block",
        "evidence_maturity_block",
        "forecast_readiness_pressure_block",
        "handoff_completeness_block",
        "input_conflict_review_needed",
        "report_only_domain_team_handoff_quality_block",
        "unresolved_conflicts_block",
    )
    assert watched.domain_team_label == "domain-team-beta"
    assert watched.handoff_quality_score == d("0.625000")
    assert watched.lowest_dimension_score == d("0.550000")
    assert "domain_team_handoff_quality_watch" in watched.reason_codes
    assert "forecast_readiness_pressure_watch" in watched.reason_codes
    assert passed.domain_team_label == "domain-team-alpha"
    assert passed.handoff_quality_score == d("0.850000")
    assert passed.reason_codes == (
        "domain_team_handoff_quality_pass",
        "evidence_maturity_pass",
        "forecast_readiness_pressure_pass",
        "handoff_completeness_pass",
        "input_handoff_review_ready",
        "report_only_domain_team_handoff_quality_pass",
        "unresolved_conflicts_pass",
    )


def test_payload_is_deterministic_decimal_only_and_digest_validated() -> None:
    first = report(
        team("z-domain-team", reason_codes=("zeta", "alpha")),
        team("a-domain-team"),
        generated_at=datetime(
            2026,
            7,
            8,
            5,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )
    second = report(
        team("a-domain-team"),
        team("z-domain-team", reason_codes=("alpha", "zeta")),
        generated_at=datetime(
            2026,
            7,
            8,
            5,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )

    first_payload = research_strategy_domain_team_handoff_quality_report_payload(first)
    second_payload = research_strategy_domain_team_handoff_quality_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["team_count"] == "2"
    assert first_payload["rows"][0]["domain_team_label"] == "a-domain-team"
    assert first_payload["rows"][0]["handoff_quality_score"] == "0.850000"
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert research_strategy_domain_team_handoff_quality_report_digest(first) == (
        first.derived_validation_digest
    )
    assert len(first.derived_validation_digest) == 64
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert not any(type(value) in (int, float) for value in _walk_payload_values(first_payload))
    assert ": 0." not in encoded
    assert not any(_has_forbidden_public_key(key) for key in _walk_payload_keys(first_payload))

    tampered = dict(first_payload)
    tampered["pass_count"] = "1"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_domain_team_handoff_quality_report_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)


def test_public_payload_rejects_raw_identifiers_unsafe_values_flags_and_numbers() -> None:
    payload = research_strategy_domain_team_handoff_quality_report_payload(
        report(team("domain-team-alpha")),
    )

    for key in (
        "candidate_id",
        "market_slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet_address",
        "order_id",
        "trade_id",
        "raw_item",
    ):
        unsafe = dict(payload)
        unsafe[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            research_strategy_domain_team_handoff_quality_report_payload(unsafe)

    for value in (
        "raw market slug",
        "https://example.test/path",
        "source text",
        "wallet signer",
        "auth token",
        "order ticket",
        "trade route",
        "buy signal",
        "sell signal",
        "position sizing",
    ):
        unsafe = dict(payload)
        unsafe["reason_codes"] = [value]
        with pytest.raises(ValueError, match="unsafe public"):
            research_strategy_domain_team_handoff_quality_report_payload(unsafe)

    numeric = dict(payload)
    numeric["team_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        research_strategy_domain_team_handoff_quality_report_payload(numeric)

    downgraded = dict(payload)
    downgraded["report_only"] = False
    with pytest.raises(ValueError, match="report_only"):
        research_strategy_domain_team_handoff_quality_report_payload(downgraded)


def test_validation_rejects_non_decimals_bad_labels_statuses_and_flags() -> None:
    with pytest.raises(ValueError, match="handoff_completeness"):
        team("domain-team-alpha", handoff_completeness=0.9)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="evidence_maturity"):
        team("domain-team-alpha", evidence_maturity=_DecimalSubclass("0.800000"))

    with pytest.raises(ValueError, match="forecast_readiness_pressure"):
        team("domain-team-alpha", forecast_readiness_pressure=d("1.1"))

    with pytest.raises(ValueError, match="domain_team_label"):
        team("raw-market-alpha")

    with pytest.raises(ValueError, match="domain_team_label"):
        team("domain-team-alpha?")

    with pytest.raises(ValueError, match="reason_codes"):
        team("domain-team-alpha", reason_codes=("NeedsReview",))

    with pytest.raises(ValueError, match="paper_only"):
        team("domain-team-alpha", paper_only=False)

    with pytest.raises(ValueError, match="generated_at"):
        report(team("domain-team-alpha"), generated_at=datetime(2026, 7, 8, 12, 0))

    with pytest.raises(ValueError, match="generated_at"):
        report(
            team("domain-team-alpha"),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )

    quality_report = report(team("domain-team-alpha"))
    with pytest.raises(ValueError, match="status"):
        replace(quality_report.rows[0], status="blocked")

    with pytest.raises(TypeError, match="subclass"):

        class BadConfig(ResearchStrategyDomainTeamHandoffQualityConfig):
            pass


def test_public_dataclasses_are_frozen_and_materialized_fields_validate() -> None:
    quality_report = report(team("domain-team-alpha"))
    row = quality_report.rows[0]

    with pytest.raises(FrozenInstanceError):
        quality_report.status = "watch"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        row.handoff_quality_score = d("0")  # type: ignore[misc]

    with pytest.raises(ValueError, match="handoff_quality_score"):
        replace(row, handoff_quality_score=d("0.100000"))

    with pytest.raises(ValueError, match="status"):
        replace(row, status="watch")

    with pytest.raises(ValueError, match="team_count"):
        replace(quality_report, team_count=d("2"))

    for value in (quality_report, row, *quality_report.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item is None:
                continue
            if field.name.endswith(("_count", "_score", "_pressure", "_maturity")):
                assert type(item) is Decimal


def test_module_exposes_no_execution_storage_or_decision_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_domain_team_handoff_quality_report.py"
    )
    text = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "wallet",
        "auth",
        "order",
        "trade",
        "live trading",
        "buy",
        "sell",
        "recommendation",
        "position sizing",
        "database",
    )
    assert all(term not in text for term in forbidden_terms)

    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    forbidden_import_roots = {
        "http",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "connect",
        "execute",
        "open",
        "request",
        "send",
        "urlopen",
        "write",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names


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


def _has_forbidden_public_key(key: str) -> bool:
    lowered = key.lower()
    return any(
        fragment in lowered
        for fragment in (
            "candidate",
            "market",
            "slug",
            "question",
            "url",
            "source",
            "dsn",
            "table",
            "token",
            "wallet",
            "order",
            "trade",
            "raw",
        )
    )
