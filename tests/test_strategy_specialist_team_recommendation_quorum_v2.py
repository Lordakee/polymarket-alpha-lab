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


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_specialist_team_recommendation_quorum_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 15, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 14, 45, tzinfo=UTC)
CONFIG_VERSION = "strategy-specialist-team-recommendation-quorum-v2-test"
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_specialist_team_recommendation_quorum_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": CONFIG_VERSION,
        "quorum_team_count": d("2.000000"),
        "quorum_domain_count": d("2.000000"),
        "min_domain_expertise": d("0.700000"),
        "min_calibration_score": d("0.650000"),
        "min_independent_source_count": d("2.000000"),
        "min_source_independence_score": d("0.700000"),
        "max_conflict_severity": d("0.300000"),
        "max_confidence_dispersion": d("0.200000"),
        "min_liquidity_score": d("0.600000"),
        "max_fee_drag": d("0.100000"),
        "max_estimated_slippage": d("0.050000"),
        "min_quorum_score": d("0.700000"),
    }
    values.update(overrides)
    return module.StrategySpecialistTeamRecommendationQuorumV2Config(**values)


def recommendation(team_id: str = "macro_team", **overrides: object):
    module = api()
    values = {
        "candidate_id": "candidate-alpha",
        "team_id": team_id,
        "domain_id": "macro",
        "recommendation_side": "yes",
        "confidence": d("0.800000"),
        "domain_expertise": d("0.900000"),
        "calibration_score": d("0.850000"),
        "independent_source_count": d("2.000000"),
        "source_independence_score": d("0.800000"),
        "conflict_severity": d("0.100000"),
        "liquidity_score": d("0.900000"),
        "fee_drag": d("0.020000"),
        "estimated_slippage": d("0.010000"),
        "observed_at": OBSERVED_AT,
        "reason_codes": ("specialist_recommendation_available",),
    }
    values.update(overrides)
    return module.StrategySpecialistTeamRecommendationQuorumV2Input(**values)


def build_report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_specialist_team_recommendation_quorum_v2_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_quorum_met_uses_domain_calibration_source_conflict_dispersion_and_costs() -> None:
    report = build_report(
        recommendation(
            "macro_team",
            domain_id="macro",
            confidence=d("0.800000"),
            domain_expertise=d("0.900000"),
            calibration_score=d("0.850000"),
            independent_source_count=d("2.000000"),
            source_independence_score=d("0.800000"),
            conflict_severity=d("0.100000"),
            liquidity_score=d("0.900000"),
            fee_drag=d("0.020000"),
            estimated_slippage=d("0.010000"),
        ),
        recommendation(
            "policy_team",
            domain_id="policy",
            confidence=d("0.700000"),
            domain_expertise=d("0.800000"),
            calibration_score=d("0.750000"),
            independent_source_count=d("3.000000"),
            source_independence_score=d("0.900000"),
            conflict_severity=d("0.200000"),
            liquidity_score=d("0.800000"),
            fee_drag=d("0.030000"),
            estimated_slippage=d("0.020000"),
        ),
        generated_at=datetime(2026, 7, 6, 10, 0, tzinfo=timezone(timedelta(hours=-5))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.candidate_count == d("1.000000")
    assert report.recommendation_count == d("2.000000")
    assert report.quorum_met_count == d("1.000000")
    assert report.watch_count == ZERO
    assert report.blocked_count == ZERO
    assert report.status == "quorum_met"
    assert report.reason_codes == ("quorum_met",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    row = report.rows[0]
    assert row.candidate_id == "candidate-alpha"
    assert row.recommendation_side == "yes"
    assert row.team_count == d("2.000000")
    assert row.qualified_team_count == d("2.000000")
    assert row.domain_count == d("2.000000")
    assert row.qualified_domain_count == d("2.000000")
    assert row.independent_source_count == d("5.000000")
    assert row.domain_expertise_score == d("0.850000")
    assert row.calibration_score == d("0.800000")
    assert row.source_coverage_score == d("0.850000")
    assert row.conflict_severity == d("0.200000")
    assert row.confidence_dispersion == d("0.100000")
    assert row.liquidity_fee_awareness_score == d("0.936667")
    assert row.quorum_score == d("0.892083")
    assert row.quorum_status == "quorum_met"
    assert row.latest_observed_at == OBSERVED_AT
    assert row.reason_codes == ("quorum_met",)

    payload = api().strategy_specialist_team_recommendation_quorum_v2_payload(report)
    assert payload["candidate_count"] == "1.000000"
    assert payload["recommendation_count"] == "2.000000"
    assert payload["rows"][0]["quorum_score"] == "0.892083"
    assert payload["rows"][0]["independent_source_count"] == "5.000000"
    assert payload["rows"][0]["derived_validation_digest"] == row.derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    json.dumps(payload, sort_keys=True)
    assert_no_float_values(payload)


def test_gaps_conflicts_dispersion_and_liquidity_costs_drive_watch_and_blocked() -> None:
    report = build_report(
        recommendation(
            "solo_team",
            candidate_id="candidate-watch",
            domain_id="macro",
            confidence=d("0.720000"),
            independent_source_count=d("1.000000"),
            source_independence_score=d("0.600000"),
        ),
        recommendation(
            "conflict_team_a",
            candidate_id="candidate-blocked",
            domain_id="crypto",
            confidence=d("0.950000"),
            conflict_severity=d("0.450000"),
            liquidity_score=d("0.550000"),
            fee_drag=d("0.120000"),
            estimated_slippage=d("0.080000"),
        ),
        recommendation(
            "conflict_team_b",
            candidate_id="candidate-blocked",
            domain_id="policy",
            confidence=d("0.500000"),
            conflict_severity=d("0.350000"),
        ),
    )

    assert report.status == "blocked"
    assert report.quorum_met_count == ZERO
    assert report.watch_count == d("1.000000")
    assert report.blocked_count == d("1.000000")
    assert report.reason_codes == (
        "quorum_blocked",
        "quorum_watch",
        "conflict_severity_blocked",
        "confidence_dispersion_watch",
        "liquidity_fee_awareness_watch",
        "domain_quorum_gap",
        "source_coverage_gap",
        "team_quorum_gap",
    )
    assert tuple(row.candidate_id for row in report.rows) == (
        "candidate-blocked",
        "candidate-watch",
    )
    blocked, watched = report.rows
    assert blocked.quorum_status == "blocked"
    assert blocked.conflict_severity == d("0.450000")
    assert blocked.confidence_dispersion == d("0.450000")
    assert "conflict_severity_blocked" in blocked.reason_codes
    assert "confidence_dispersion_watch" in blocked.reason_codes
    assert "liquidity_fee_awareness_watch" in blocked.reason_codes
    assert watched.quorum_status == "watch"
    assert watched.qualified_team_count == ZERO
    assert watched.qualified_domain_count == ZERO
    assert watched.reason_codes == (
        "quorum_watch",
        "domain_quorum_gap",
        "source_coverage_gap",
        "team_quorum_gap",
    )


def test_empty_report_is_readonly_report_only_and_decimal_zeroed() -> None:
    report = build_report()

    assert report.candidate_count == ZERO
    assert report.recommendation_count == ZERO
    assert report.quorum_met_count == ZERO
    assert report.watch_count == ZERO
    assert report.blocked_count == ZERO
    assert report.status == "watch"
    assert report.reason_codes == ("empty_recommendation_quorum",)
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    populated = build_report(recommendation(), recommendation("policy_team", domain_id="policy"))
    for value in (report, populated, *populated.rows):
        for item in fields(value):
            if item.name in {
                "paper_only",
                "report_only",
                "readonly",
                "derived_validation_digest",
            }:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(
                (
                    "_count",
                    "_score",
                    "_severity",
                    "_dispersion",
                    "_drag",
                    "_slippage",
                ),
            ):
                assert type(item_value) is Decimal


def test_payload_revalidates_digest_flags_and_rejects_unsafe_public_content() -> None:
    module = api()
    report = build_report(recommendation(), recommendation("policy_team", domain_id="policy"))
    payload = module.strategy_specialist_team_recommendation_quorum_v2_payload(report)

    assert module.strategy_specialist_team_recommendation_quorum_v2_payload(payload) == payload

    tampered_count = {**payload, "candidate_count": "9.000000"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_specialist_team_recommendation_quorum_v2_payload(tampered_count)

    tampered_row = dict(payload)
    tampered_row["rows"] = [dict(payload["rows"][0])]
    tampered_row["rows"][0]["quorum_score"] = "0.111111"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_specialist_team_recommendation_quorum_v2_payload(tampered_row)

    downgraded = {**payload, "paper_only": False}
    with pytest.raises(ValueError, match="paper_only"):
        module.strategy_specialist_team_recommendation_quorum_v2_payload(downgraded)

    unsafe_key = {**payload, "wallet_reference": "paper"}
    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_specialist_team_recommendation_quorum_v2_payload(unsafe_key)

    unsafe_value = {**payload, "status": "live_mode"}
    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_specialist_team_recommendation_quorum_v2_payload(unsafe_value)

    decimal_drift = {**payload, "candidate_count": d("1.000000")}
    with pytest.raises(ValueError, match="Decimal|string|JSON"):
        module.strategy_specialist_team_recommendation_quorum_v2_payload(decimal_drift)


def test_frozen_dataclasses_decimal_only_canonical_inputs_and_public_safety() -> None:
    module = api()
    report = build_report(recommendation(), recommendation("policy_team", domain_id="policy"))

    assert is_dataclass(module.StrategySpecialistTeamRecommendationQuorumV2Config)
    assert is_dataclass(module.StrategySpecialistTeamRecommendationQuorumV2Input)
    assert is_dataclass(module.StrategySpecialistTeamRecommendationQuorumV2Row)
    assert is_dataclass(module.StrategySpecialistTeamRecommendationQuorumV2Report)
    with pytest.raises(FrozenInstanceError):
        report.status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].quorum_score = d("0.100000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        recommendation(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="confidence"):
        recommendation(confidence=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="domain_expertise"):
        recommendation(domain_expertise=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="observed_at"):
        recommendation(observed_at=_DatetimeSubclass(2026, 7, 6, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(recommendation(), generated_at=datetime(2026, 7, 6, 15, 0))
    with pytest.raises(ValueError, match="unsafe"):
        recommendation(team_id="wallet_team")
    with pytest.raises(ValueError, match="duplicate"):
        build_report(recommendation(), recommendation())
    with pytest.raises(ValueError, match="ordered"):
        recommendation(reason_codes={"alpha_reason", "beta_reason"})


def test_module_scope_has_no_live_state_io_auth_order_or_persistence_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "db",
        "http",
        "network",
        "order",
        "psycopg",
        "request",
        "socket",
        "sql",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_names = {
        "open",
        "read",
        "write",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "sign",
    }
    forbidden_attr_fragments = (
        "account",
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "file",
        "network",
        "order",
        "persist",
        "request",
        "sign",
        "submit",
        "trade",
        "wallet",
        "write",
    )
    forbidden_attr_names = {
        "open",
        "read",
        "read_text",
        "read_bytes",
        "write",
        "write_text",
        "write_bytes",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert lowered not in forbidden_attr_names
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)

    assert imports
    for module_name in imports:
        assert not module_name.startswith("polymarket_alpha_lab.")
        lowered = module_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_import_fragments)
