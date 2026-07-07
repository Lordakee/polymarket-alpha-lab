from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_recommendation_team_conflict_resolution_gate_v2.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
CONFIG_VERSION = "team-conflict-resolution-gate-v2-test"
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_recommendation_team_conflict_resolution_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": CONFIG_VERSION,
        "max_forecast_dispersion": d("0.050000"),
        "max_evidence_quality_difference": d("0.100000"),
        "max_source_family_overlap_ratio": d("0.250000"),
        "max_recency_mismatch_seconds": d("3600.000000"),
        "max_resolution_ambiguity_score": d("0.300000"),
        "min_cost_adjusted_edge": d("0.020000"),
    }
    values.update(overrides)
    return module.StrategyRecommendationTeamConflictResolutionGateV2Config(**values)


def recommendation(recommendation_id: str, **overrides: object):
    module = api()
    values = {
        "recommendation_id": recommendation_id,
        "candidate_id": "candidate-alpha",
        "market_slug": "event-alpha",
        "team_id": "crypto_btc",
        "recommendation_side": "yes",
        "forecast_probability": d("0.620000"),
        "evidence_quality_score": d("0.850000"),
        "source_family": "prediction-model",
        "evidence_observed_at": GENERATED_AT - timedelta(minutes=20),
        "resolution_ambiguity_score": d("0.100000"),
        "cost_adjusted_edge": d("0.040000"),
    }
    values.update(overrides)
    return module.StrategyRecommendationTeamConflictResolutionGateV2Input(**values)


def build_report(*items: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_recommendation_team_conflict_resolution_gate_v2_report(
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


def test_empty_input_returns_watch_paper_report() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.input_count == ZERO
    assert report.candidate_count == ZERO
    assert report.qualified_count == ZERO
    assert report.watch_count == ZERO
    assert report.blocked_count == ZERO
    assert report.status == "watch"
    assert report.reason_codes == ("empty_team_conflict_resolution_gate_v2",)
    assert report.rows == ()
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_blocks_candidate_when_conflict_resolution_metrics_exceed_gate_thresholds() -> None:
    report = build_report(
        recommendation(
            "rec-best-thin-edge",
            team_id="crypto_btc",
            recommendation_side="yes",
            forecast_probability=d("0.610000"),
            evidence_quality_score=d("0.900000"),
            source_family="market-model",
            evidence_observed_at=GENERATED_AT - timedelta(minutes=30),
            resolution_ambiguity_score=d("0.250000"),
            cost_adjusted_edge=d("0.015000"),
        ),
        recommendation(
            "rec-opposing-stale",
            team_id="macro_policy",
            recommendation_side="no",
            forecast_probability=d("0.720000"),
            evidence_quality_score=d("0.720000"),
            source_family="market-model",
            evidence_observed_at=GENERATED_AT - timedelta(hours=2, minutes=30),
            resolution_ambiguity_score=d("0.450000"),
            cost_adjusted_edge=d("0.010000"),
        ),
        recommendation(
            "rec-confirming",
            team_id="elections_us",
            recommendation_side="yes",
            forecast_probability=d("0.650000"),
            evidence_quality_score=d("0.800000"),
            source_family="news-model",
            evidence_observed_at=GENERATED_AT - timedelta(minutes=15),
            resolution_ambiguity_score=d("0.200000"),
            cost_adjusted_edge=d("0.012000"),
        ),
    )

    assert report.status == "blocked"
    assert report.input_count == d("3.000000")
    assert report.candidate_count == d("1.000000")
    assert report.qualified_count == ZERO
    assert report.watch_count == ZERO
    assert report.blocked_count == d("1.000000")
    assert report.reason_codes == (
        "side_disagreement",
        "forecast_dispersion_high",
        "evidence_quality_difference_high",
        "source_family_overlap_high",
        "recency_mismatch_high",
        "resolution_ambiguity_high",
        "cost_adjusted_edge_margin_low",
        "team_conflict_resolution_gate_v2_blocked",
    )

    row = report.rows[0]
    assert row.candidate_id == "candidate-alpha"
    assert row.market_slug == "event-alpha"
    assert row.chosen_recommendation_id == "rec-best-thin-edge"
    assert row.chosen_team_id == "crypto_btc"
    assert row.chosen_side == "yes"
    assert row.team_count == d("3.000000")
    assert row.side_count == d("2.000000")
    assert row.source_family_count == d("2.000000")
    assert row.forecast_dispersion == d("0.110000")
    assert row.evidence_quality_difference == d("0.180000")
    assert row.source_family_overlap_ratio == d("0.333333")
    assert row.recency_mismatch_seconds == d("8100.000000")
    assert row.max_resolution_ambiguity_score == d("0.450000")
    assert row.best_cost_adjusted_edge == d("0.015000")
    assert row.cost_adjusted_edge_margin == d("-0.005000")
    assert row.gate_status == "blocked"
    assert row.reason_codes == report.reason_codes
    assert len(row.derived_validation_digest) == 64
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_qualified_and_watch_rows_are_sorted_and_reported_deterministically() -> None:
    report = build_report(
        recommendation(
            "rec-clear-a",
            candidate_id="candidate-clear",
            team_id="crypto_btc",
            forecast_probability=d("0.610000"),
            evidence_quality_score=d("0.880000"),
            source_family="market-model",
            evidence_observed_at=GENERATED_AT - timedelta(minutes=20),
            resolution_ambiguity_score=d("0.100000"),
            cost_adjusted_edge=d("0.050000"),
        ),
        recommendation(
            "rec-clear-b",
            candidate_id="candidate-clear",
            team_id="macro_policy",
            forecast_probability=d("0.630000"),
            evidence_quality_score=d("0.840000"),
            source_family="news-model",
            evidence_observed_at=GENERATED_AT - timedelta(minutes=30),
            resolution_ambiguity_score=d("0.120000"),
            cost_adjusted_edge=d("0.030000"),
        ),
        recommendation(
            "rec-watch-a",
            candidate_id="candidate-watch",
            team_id="crypto_btc",
            recommendation_side="yes",
            forecast_probability=d("0.590000"),
            evidence_quality_score=d("0.860000"),
            source_family="market-model",
            evidence_observed_at=GENERATED_AT - timedelta(minutes=25),
            resolution_ambiguity_score=d("0.100000"),
            cost_adjusted_edge=d("0.040000"),
        ),
        recommendation(
            "rec-watch-b",
            candidate_id="candidate-watch",
            team_id="macro_policy",
            recommendation_side="no",
            forecast_probability=d("0.680000"),
            evidence_quality_score=d("0.820000"),
            source_family="news-model",
            evidence_observed_at=GENERATED_AT - timedelta(minutes=35),
            resolution_ambiguity_score=d("0.100000"),
            cost_adjusted_edge=d("0.035000"),
        ),
    )

    assert report.status == "watch"
    assert report.input_count == d("4.000000")
    assert report.candidate_count == d("2.000000")
    assert report.qualified_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.blocked_count == ZERO
    assert tuple(row.candidate_id for row in report.rows) == (
        "candidate-watch",
        "candidate-clear",
    )
    assert tuple(row.gate_status for row in report.rows) == ("watch", "qualified")
    assert report.reason_codes == (
        "side_disagreement",
        "forecast_dispersion_high",
        "team_conflict_resolution_gate_v2_watch",
        "team_conflict_resolution_gate_v2_qualified",
    )
    assert report.rows[0].reason_codes == (
        "side_disagreement",
        "forecast_dispersion_high",
        "team_conflict_resolution_gate_v2_watch",
    )
    assert report.rows[1].reason_codes == ("team_conflict_resolution_gate_v2_qualified",)


def test_payload_serializes_decimals_as_strings_and_rejects_tampering() -> None:
    module = api()
    report = build_report(
        recommendation("rec-alpha"),
        recommendation(
            "rec-beta",
            team_id="macro_policy",
            source_family="news-model",
            cost_adjusted_edge=d("0.030000"),
        ),
    )

    payload = module.strategy_recommendation_team_conflict_resolution_gate_v2_payload(report)

    assert payload["input_count"] == "2.000000"
    assert payload["candidate_count"] == "1.000000"
    assert payload["rows"][0]["forecast_dispersion"] == "0.000000"
    assert payload["rows"][0]["cost_adjusted_edge_margin"] == "0.020000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["derived_validation_digest"] == report.rows[0].derived_validation_digest
    assert module.strategy_recommendation_team_conflict_resolution_gate_v2_payload(payload) == payload
    json.dumps(payload, sort_keys=True)
    assert_no_float_values(payload)

    tampered_count = {**payload, "candidate_count": "9.000000"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_recommendation_team_conflict_resolution_gate_v2_payload(tampered_count)

    tampered_row = dict(payload)
    tampered_row["rows"] = [dict(payload["rows"][0])]
    tampered_row["rows"][0]["gate_status"] = "blocked"
    with pytest.raises(ValueError, match="reason_codes|derived_validation_digest"):
        module.strategy_recommendation_team_conflict_resolution_gate_v2_payload(tampered_row)

    with pytest.raises(ValueError, match="paper_only"):
        module.strategy_recommendation_team_conflict_resolution_gate_v2_payload(
            {**payload, "paper_only": False},
        )
    with pytest.raises(ValueError, match="Decimal|string|JSON"):
        module.strategy_recommendation_team_conflict_resolution_gate_v2_payload(
            {**payload, "candidate_count": d("1.000000")},
        )
    with pytest.raises(ValueError, match="float"):
        module.strategy_recommendation_team_conflict_resolution_gate_v2_payload(
            {**payload, "candidate_count": 1.0},
        )


def test_frozen_dataclasses_decimal_only_flags_and_type_validation() -> None:
    module = api()
    report = build_report(recommendation("rec-alpha"))

    assert is_dataclass(module.StrategyRecommendationTeamConflictResolutionGateV2Config)
    assert is_dataclass(module.StrategyRecommendationTeamConflictResolutionGateV2Input)
    assert is_dataclass(module.StrategyRecommendationTeamConflictResolutionGateV2Row)
    assert is_dataclass(module.StrategyRecommendationTeamConflictResolutionGateV2Report)

    with pytest.raises(FrozenInstanceError):
        report.status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].forecast_dispersion = d("0.100000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        recommendation("rec-readonly", readonly=False)
    with pytest.raises(ValueError, match="forecast_probability"):
        recommendation("rec-float", forecast_probability=0.62)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_quality_score"):
        recommendation("rec-decimal-subclass", evidence_quality_score=_DecimalSubclass("0.850000"))
    with pytest.raises(ValueError, match="evidence_observed_at"):
        recommendation(
            "rec-datetime-subclass",
            evidence_observed_at=_DatetimeSubclass(2026, 7, 7, 11, 40, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        recommendation("rec-naive-time", evidence_observed_at=datetime(2026, 7, 7, 11, 40))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(recommendation("rec-good"), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="future"):
        build_report(
            recommendation(
                "rec-future",
                evidence_observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="duplicate recommendation_id"):
        build_report(recommendation("rec-dup"), recommendation("rec-dup"))
    with pytest.raises(ValueError, match="config"):
        module.build_strategy_recommendation_team_conflict_resolution_gate_v2_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="unsafe"):
        recommendation("rec-unsafe", team_id="wallet_team")

    for value in (report, *report.rows):
        for field in fields(value):
            if field.name in {
                "derived_validation_digest",
                "paper_only",
                "report_only",
                "readonly",
            }:
                continue
            item_value = getattr(value, field.name)
            if field.name.endswith(
                (
                    "_count",
                    "_dispersion",
                    "_difference",
                    "_ratio",
                    "_seconds",
                    "_score",
                    "_edge",
                    "_margin",
                ),
            ):
                assert type(item_value) is Decimal


def test_module_has_no_io_network_or_stateful_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_modules: list[str] = []
    forbidden_import_fragments = (
        "asyncpg",
        "broker",
        "client",
        "db",
        "http",
        "network",
        "psycopg",
        "request",
        "socket",
        "sql",
        "sqlite",
        "subprocess",
        "supabase",
        "urllib",
    )
    forbidden_call_names = {
        "open",
        "connect",
        "execute",
        "fetch",
        "request",
        "get",
        "post",
        "put",
        "delete",
        "submit",
        "cancel",
        "sign",
        "write",
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

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported_modules.append(node.module or "")
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)

    assert imported_modules
    for module_name in imported_modules:
        lowered = module_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_import_fragments)
