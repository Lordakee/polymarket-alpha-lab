from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.strategy_recommendation_concentration_throttle_v2 import (
    StrategyRecommendationConcentrationThrottleV2Candidate,
    StrategyRecommendationConcentrationThrottleV2Config,
    StrategyRecommendationConcentrationThrottleV2Report,
    StrategyRecommendationConcentrationThrottleV2Row,
    build_strategy_recommendation_concentration_throttle_v2_report,
    strategy_recommendation_concentration_throttle_v2_payload,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_recommendation_concentration_throttle_v2.py"
)
GENERATED_AT = datetime(2026, 7, 4, 16, 30, tzinfo=timezone(timedelta(hours=-4)))


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyRecommendationConcentrationThrottleV2Config:
    values: dict[str, object] = {
        "config_version": "strategy-recommendation-concentration-throttle-v2-test",
        "max_recommendations_per_category": d("1.000000"),
        "max_recommendations_per_event": d("1.000000"),
        "max_recommendations_per_team": d("1.000000"),
    }
    values.update(overrides)
    return StrategyRecommendationConcentrationThrottleV2Config(**values)


def candidate(
    recommendation_id: str,
    *,
    category_id: str = "category_alpha",
    event_id: str = "event_alpha",
    team_id: str = "team_alpha",
    market_slug: str | None = None,
    recommendation_score: Decimal = d("0.900000"),
    reason_codes: tuple[str, ...] = ("upstream_recommendation",),
) -> StrategyRecommendationConcentrationThrottleV2Candidate:
    return StrategyRecommendationConcentrationThrottleV2Candidate(
        recommendation_id=recommendation_id,
        category_id=category_id,
        event_id=event_id,
        team_id=team_id,
        market_slug=market_slug or f"{recommendation_id}-market",
        recommendation_score=recommendation_score,
        reason_codes=reason_codes,
    )


def report(
    *candidates: StrategyRecommendationConcentrationThrottleV2Candidate,
    cfg: StrategyRecommendationConcentrationThrottleV2Config | None = None,
) -> StrategyRecommendationConcentrationThrottleV2Report:
    return build_strategy_recommendation_concentration_throttle_v2_report(
        candidates,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def walk_json_ready(value: Any) -> None:
    if isinstance(value, dict):
        for child in value.values():
            walk_json_ready(child)
        return
    if isinstance(value, list):
        for child in value:
            walk_json_ready(child)
        return
    assert not isinstance(value, (Decimal, datetime, float))


def test_applies_category_event_and_team_concentration_throttles() -> None:
    throttle_report = report(
        candidate("alpha-top", recommendation_score=d("0.990000")),
        candidate(
            "category-capped",
            event_id="event_beta",
            team_id="team_beta",
            recommendation_score=d("0.980000"),
        ),
        candidate(
            "event-capped",
            category_id="category_beta",
            team_id="team_gamma",
            recommendation_score=d("0.970000"),
        ),
        candidate(
            "team-capped",
            category_id="category_gamma",
            event_id="event_gamma",
            recommendation_score=d("0.960000"),
        ),
        candidate(
            "clear-second",
            category_id="category_delta",
            event_id="event_delta",
            team_id="team_delta",
            recommendation_score=d("0.950000"),
        ),
    )

    assert isinstance(throttle_report, StrategyRecommendationConcentrationThrottleV2Report)
    assert throttle_report.generated_at == datetime(2026, 7, 4, 20, 30, tzinfo=UTC)
    assert throttle_report.candidate_count == d("5.000000")
    assert throttle_report.pass_count == d("2.000000")
    assert throttle_report.throttled_count == d("3.000000")
    assert throttle_report.paper_only is True
    assert throttle_report.report_only is True
    assert throttle_report.readonly is True

    rows_by_id = {row.recommendation_id: row for row in throttle_report.rows}
    assert rows_by_id["alpha-top"].throttle_status == "pass"
    assert rows_by_id["clear-second"].throttle_status == "pass"
    assert rows_by_id["category-capped"].throttle_status == "throttled"
    assert rows_by_id["event-capped"].throttle_status == "throttled"
    assert rows_by_id["team-capped"].throttle_status == "throttled"
    assert "category_concentration_throttle" in rows_by_id["category-capped"].reason_codes
    assert "event_concentration_throttle" in rows_by_id["event-capped"].reason_codes
    assert "team_concentration_throttle" in rows_by_id["team-capped"].reason_codes
    assert throttle_report.reason_codes == (
        "category_concentration_throttle_present",
        "event_concentration_throttle_present",
        "team_concentration_throttle_present",
    )


def test_payload_serializes_decimals_as_strings_and_preserves_digest() -> None:
    throttle_report = report(candidate("payload-alpha"))

    payload = strategy_recommendation_concentration_throttle_v2_payload(throttle_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["candidate_count"] == "1.000000"
    assert payload["pass_count"] == "1.000000"
    assert payload["throttled_count"] == "0.000000"
    assert payload["rows"][0]["recommendation_score"] == "0.900000"
    assert payload["rows"][0]["throttle_rank"] == "1.000000"
    assert payload["generated_at"] == "2026-07-04T20:30:00+00:00"
    assert payload["derived_validation_digest"] == throttle_report.derived_validation_digest
    assert len(throttle_report.derived_validation_digest) == 64
    assert '"0.900000"' in encoded
    walk_json_ready(payload)


def test_public_records_are_frozen_and_decimal_only_for_numeric_values() -> None:
    throttle_report = report(candidate("frozen-alpha"))
    row = throttle_report.rows[0]

    assert isinstance(row, StrategyRecommendationConcentrationThrottleV2Row)
    with pytest.raises(FrozenInstanceError):
        row.throttle_status = "throttled"  # type: ignore[misc]

    for public_record in (
        config(),
        candidate("decimal-alpha"),
        row,
        throttle_report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            value = getattr(public_record, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert not isinstance(value, float)


def test_hard_paper_report_readonly_flags_are_enforced() -> None:
    throttle_report = report(candidate("flags-alpha"))

    assert throttle_report.paper_only is True
    assert throttle_report.report_only is True
    assert throttle_report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in throttle_report.rows)

    with pytest.raises(ValueError, match="config paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="candidate report_only must be True"):
        replace(candidate("bad-candidate-flag"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(throttle_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(throttle_report, paper_only=False)
    with pytest.raises(ValueError, match="payload readonly must be True"):
        strategy_recommendation_concentration_throttle_v2_payload(
            {**strategy_recommendation_concentration_throttle_v2_payload(throttle_report), "readonly": False},
        )


def test_derived_validation_digest_rejects_tampering() -> None:
    throttle_report = report(candidate("digest-alpha"))
    payload = strategy_recommendation_concentration_throttle_v2_payload(throttle_report)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(throttle_report, derived_validation_digest="0" * 64)

    tampered_payload = dict(payload)
    tampered_payload["pass_count"] = "999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_recommendation_concentration_throttle_v2_payload(tampered_payload)


@pytest.mark.parametrize(
    ("unsafe_key", "unsafe_value"),
    (
        ("wallet_reference", "redacted"),
        ("risk_context", "live route"),
        ("review_note", "requires signing"),
        ("category_context", "database path"),
        ("team_context", "persist result"),
        ("market_context", "buy intent"),
        ("event_context", "sell intent"),
        ("candidate_context", "trade flow"),
        ("network_context", "redacted"),
        ("mutation_context", "redacted"),
    ),
)
def test_rejects_unsafe_public_payload_keys_and_values(
    unsafe_key: str,
    unsafe_value: str,
) -> None:
    throttle_report = report(candidate("unsafe-alpha"))
    payload = strategy_recommendation_concentration_throttle_v2_payload(throttle_report)
    unsafe_payload = dict(payload)
    unsafe_payload[unsafe_key] = unsafe_value

    with pytest.raises(ValueError, match="unsafe public payload"):
        strategy_recommendation_concentration_throttle_v2_payload(unsafe_payload)


def test_module_has_no_network_auth_wallet_order_db_persistence_or_live_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    forbidden_import_fragments = (
        "aiohttp",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite",
        "subprocess",
        "supabase",
        "urllib",
        "websocket",
    )
    forbidden_call_names = {
        "buy",
        "cancel",
        "connect",
        "execute",
        "fetch",
        "open",
        "request",
        "sell",
        "sign",
        "submit",
        "trade",
        "write",
    }
    forbidden_public_name_fragments = (
        "auth",
        "database",
        "live",
        "mutation",
        "network",
        "order",
        "persist",
        "signing",
        "trade",
        "wallet",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.add(node.module or "")
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert not any(fragment in lowered for fragment in forbidden_public_name_fragments)

    assert imported_modules
    for module_name in imported_modules:
        lowered = module_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_import_fragments)

    module_globals: dict[str, Any] = {}
    exec(compile(tree, str(MODULE_PATH), "exec"), module_globals)
    for public_name in module_globals["__all__"]:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_public_name_fragments)
