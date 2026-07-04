from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.strategy_team_recommendation_digest import (
    PaperStrategyTeamRecommendationConfig,
    PaperStrategyTeamRecommendationReport,
    PaperStrategyTeamRecommendationRow,
    TeamResearchRecommendationSignal,
    build_paper_strategy_team_recommendation_report,
    strategy_team_recommendation_digest_payload,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_team_recommendation_digest.py"
)
GENERATED_AT = datetime(2026, 7, 3, 15, 30, tzinfo=timezone(timedelta(hours=2)))
OBSERVED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides) -> PaperStrategyTeamRecommendationConfig:
    values = {
        "config_version": "strategy-team-recommendation-test-v0",
        "min_net_edge": d("0.010000"),
        "min_confidence": d("0.650000"),
        "max_evidence_age_seconds": d("3600"),
        "min_liquidity": d("100.000000"),
        "max_spread": d("0.030000"),
        "max_recommendations_per_team": d("1"),
        "max_recommendations_per_category": d("1"),
    }
    values.update(overrides)
    return PaperStrategyTeamRecommendationConfig(**values)


def signal(
    market_slug: str,
    *,
    team_id: str = "crypto_btc",
    category_id: str = "finance.crypto.btc",
    side: str = "yes",
    forecast_probability: Decimal = d("0.620000"),
    implied_probability: Decimal = d("0.570000"),
    confidence: Decimal = d("0.800000"),
    liquidity: Decimal = d("500.000000"),
    spread: Decimal = d("0.010000"),
    observed_at: datetime = OBSERVED_AT,
    reason_codes: tuple[str, ...] = ("team_research_signal",),
    evidence_reference: str = "team-rollup",
) -> TeamResearchRecommendationSignal:
    return TeamResearchRecommendationSignal(
        team_id=team_id,
        category_id=category_id,
        market_slug=market_slug,
        question=f"Question for {market_slug}?",
        side=side,
        forecast_probability=forecast_probability,
        implied_probability=implied_probability,
        confidence=confidence,
        liquidity=liquidity,
        spread=spread,
        observed_at=observed_at,
        evidence_reference=evidence_reference,
        reason_codes=reason_codes,
    )


def build_report(*signals: TeamResearchRecommendationSignal):
    return build_paper_strategy_team_recommendation_report(
        signals,
        config=config(),
        generated_at=GENERATED_AT,
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


def test_builds_paper_team_recommendations_with_fee_drag_caps_and_ordering() -> None:
    report = build_report(
        signal("btc-second", forecast_probability=d("0.660000"), implied_probability=d("0.600000")),
        signal("btc-top", forecast_probability=d("0.650000"), implied_probability=d("0.570000")),
        signal(
            "eth-top",
            team_id="crypto_eth",
            category_id="finance.crypto.eth",
            forecast_probability=d("0.690000"),
            implied_probability=d("0.620000"),
        ),
    )

    assert isinstance(report, PaperStrategyTeamRecommendationReport)
    assert isinstance(report.recommendation_rows[0], PaperStrategyTeamRecommendationRow)
    assert report.generated_at == datetime(2026, 7, 3, 13, 30, tzinfo=UTC)
    assert report.config_version == "strategy-team-recommendation-test-v0"
    assert report.signal_count == d("3")
    assert report.recommend_count == d("2")
    assert report.watch_count == d("1")
    assert report.reject_count == d("0")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.market_slug for row in report.recommendation_rows) == (
        "btc-top",
        "eth-top",
        "btc-second",
    )
    assert tuple(row.paper_report_status for row in report.recommendation_rows) == (
        "recommend",
        "recommend",
        "watch",
    )

    top = report.recommendation_rows[0]
    assert top.raw_edge == d("0.080000")
    assert top.fee_drag == d("0.020000")
    assert top.net_edge == d("0.060000")
    assert top.recommendation_score == d("0.048000")
    assert top.evidence_age_seconds == d("5400")
    assert top.evidence_status == "stale"
    assert top.evidence_reference == "<redacted-evidence-reference>"
    assert top.reason_codes == (
        "team_research_signal",
        "positive_net_edge",
        "confidence_passed",
        "evidence_stale",
        "liquidity_passed",
        "spread_passed",
        "team_risk_cap_passed",
        "category_risk_cap_passed",
    )

    capped = report.recommendation_rows[2]
    assert capped.paper_report_status == "watch"
    assert capped.net_edge == d("0.040000")
    assert "team_risk_cap_reached" in capped.reason_codes


def test_team_recommendation_digest_blocks_weak_inputs_with_stable_reason_codes() -> None:
    report = build_paper_strategy_team_recommendation_report(
        (
            signal("negative-edge", forecast_probability=d("0.590000"), implied_probability=d("0.580000")),
            signal("low-confidence", confidence=d("0.640000")),
            signal("thin-liquidity", liquidity=d("99.999999")),
            signal("wide-spread", spread=d("0.030001")),
        ),
        config=config(max_recommendations_per_team=d("10"), max_recommendations_per_category=d("10")),
        generated_at=GENERATED_AT,
    )

    rows_by_slug = {row.market_slug: row for row in report.recommendation_rows}
    assert rows_by_slug["negative-edge"].paper_report_status == "reject"
    assert "nonpositive_net_edge_after_fee_drag" in rows_by_slug["negative-edge"].reason_codes
    assert rows_by_slug["low-confidence"].paper_report_status == "watch"
    assert "confidence_below_threshold" in rows_by_slug["low-confidence"].reason_codes
    assert rows_by_slug["thin-liquidity"].paper_report_status == "watch"
    assert "liquidity_below_threshold" in rows_by_slug["thin-liquidity"].reason_codes
    assert rows_by_slug["wide-spread"].paper_report_status == "watch"
    assert "spread_above_threshold" in rows_by_slug["wide-spread"].reason_codes


def test_team_recommendation_digest_is_report_only_decimal_and_deterministically_sorted() -> None:
    report = build_paper_strategy_team_recommendation_report(
        (
            signal(
                "same-score-z",
                team_id="team_z",
                category_id="category_z",
                forecast_probability=d("0.650000"),
                implied_probability=d("0.570000"),
            ),
            signal(
                "same-score-a",
                team_id="team_a",
                category_id="category_a",
                forecast_probability=d("0.650000"),
                implied_probability=d("0.570000"),
            ),
        ),
        config=config(max_recommendations_per_team=d("10"), max_recommendations_per_category=d("10")),
        generated_at=GENERATED_AT,
    )

    assert tuple(row.team_id for row in report.recommendation_rows) == ("team_a", "team_z")
    assert tuple(row.paper_report_status for row in report.recommendation_rows) == (
        "recommend",
        "recommend",
    )
    assert all(not hasattr(row, "action") for row in report.recommendation_rows)

    for value in (report, *report.recommendation_rows):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(
                (
                    "_count",
                    "_probability",
                    "_confidence",
                    "_liquidity",
                    "_spread",
                    "_seconds",
                    "_edge",
                    "_drag",
                    "_score",
                ),
            ):
                assert type(item_value) is Decimal


def test_team_recommendation_payload_is_json_ready_report_only_and_redacted() -> None:
    secret = "postgres://agent:super-secret-token@localhost/polymarket"
    report = build_report(
        signal(
            "secret-source",
            evidence_reference=secret,
            forecast_probability=d("0.650000"),
            implied_probability=d("0.570000"),
        ),
    )

    payload = strategy_team_recommendation_digest_payload(report)
    rendered = repr(payload).lower()
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-03T13:30:00+00:00"
    assert payload["signal_count"] == "1"
    assert payload["recommendation_rows"][0]["paper_report_status"] == "recommend"
    assert payload["recommendation_rows"][0]["evidence_reference"] == "<redacted-evidence-reference>"
    assert '"0.048000"' in encoded
    assert "action" not in rendered
    assert "order" not in rendered
    assert "trade" not in rendered
    assert "super-secret-token" not in rendered
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)


def test_team_recommendation_digest_validates_decimal_public_api_and_flags() -> None:
    report = build_report(
        signal(
            "btc-top",
            team_id="team_a",
            category_id="category_a",
            forecast_probability=d("0.650000"),
            implied_probability=d("0.570000"),
        ),
        signal(
            "eth-top",
            team_id="team_b",
            category_id="category_b",
            forecast_probability=d("0.640000"),
            implied_probability=d("0.570000"),
        ),
    )
    row = report.recommendation_rows[0]

    with pytest.raises(FrozenInstanceError):
        row.paper_report_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="signal_count"):
        replace(report, signal_count=d("1"))
    with pytest.raises(ValueError, match="deterministically sorted"):
        replace(report, recommendation_rows=tuple(reversed(report.recommendation_rows)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="forecast_probability"):
        signal("float-probability", forecast_probability=0.62)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="max_recommendations_per_team"):
        config(max_recommendations_per_team=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="max_evidence_age_seconds"):
        config(max_evidence_age_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="timezone-aware"):
        build_paper_strategy_team_recommendation_report(
            (signal("naive-generated-at"),),
            config=config(),
            generated_at=datetime(2026, 7, 3, 13, 30),
        )


def test_team_recommendation_digest_redacts_sensitive_strings_from_repr_and_errors() -> None:
    secret = "postgres://agent:super-secret-token@localhost/polymarket"
    source = signal("secret-source", evidence_reference=secret)

    report = build_report(source)

    assert source.evidence_reference == "<redacted-evidence-reference>"
    assert report.recommendation_rows[0].evidence_reference == "<redacted-evidence-reference>"
    assert secret not in repr(source)
    assert secret not in repr(report)

    with pytest.raises(ValueError) as exc_info:
        TeamResearchRecommendationSignal(
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            market_slug="bad-probability",
            question="Bad probability?",
            side="yes",
            forecast_probability=d("1.100000"),
            implied_probability=d("0.570000"),
            confidence=d("0.800000"),
            liquidity=d("500.000000"),
            spread=d("0.010000"),
            observed_at=OBSERVED_AT,
            evidence_reference=secret,
            reason_codes=("team_research_signal",),
        )

    assert "forecast_probability" in str(exc_info.value)
    assert secret not in str(exc_info.value)


@pytest.mark.parametrize(
    "reason_code",
    (
        "order_submission",
        "auth_required",
        "replace_order",
        "live_trading_enabled",
        "bearer_token",
    ),
)
def test_team_recommendation_digest_rejects_execution_or_secret_reason_codes(
    reason_code: str,
) -> None:
    with pytest.raises(ValueError, match="reason_codes") as exc_info:
        signal("unsafe-reason", reason_codes=(reason_code,))

    assert reason_code not in str(exc_info.value)


def test_team_recommendation_digest_rejects_secret_like_public_text_without_leaking() -> None:
    secret = "postgres://agent:super-secret-token@localhost/polymarket"

    with pytest.raises(ValueError, match="question") as exc_info:
        TeamResearchRecommendationSignal(
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            market_slug="secret-question",
            question=secret,
            side="yes",
            forecast_probability=d("0.620000"),
            implied_probability=d("0.570000"),
            confidence=d("0.800000"),
            liquidity=d("500.000000"),
            spread=d("0.010000"),
            observed_at=OBSERVED_AT,
            evidence_reference="team-rollup",
            reason_codes=("team_research_signal",),
        )

    assert "super-secret-token" not in str(exc_info.value)


def test_module_scope_has_no_live_trading_or_execution_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    source = MODULE_PATH.read_text(encoding="utf-8").lower()
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
        "trade",
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
        "submit",
        "trade",
        "wallet",
        "write",
    )

    assert ".action" not in source
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
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)

    assert imports
    for module_name in imports:
        assert not module_name.startswith("polymarket_alpha_lab.")
        lowered = module_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_import_fragments)
