from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_recommendation_information_quality_gate_v2"
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "min_source_count": d("3"),
        "source_count_pass_floor": d("4"),
        "min_primary_source_count": d("1"),
        "source_recency_pass_minutes": d("60.000000"),
        "max_source_age_minutes": d("180.000000"),
        "contradiction_severity_watch_threshold": d("0.250000"),
        "contradiction_severity_block_threshold": d("0.600000"),
        "resolution_rule_specificity_block_threshold": d("0.400000"),
        "resolution_rule_specificity_pass_threshold": d("0.750000"),
        "market_close_urgency_minutes": d("45.000000"),
        "urgent_source_count_pass_floor": d("5"),
        "urgent_source_recency_pass_minutes": d("30.000000"),
    }
    values.update(overrides)
    return module.StrategyRecommendationInformationQualityGateV2Config(**values)


def recommendation(**overrides: object) -> Any:
    module = api()
    values = {
        "recommendation_id": "rec-alpha",
        "market_slug": "fed-decision-july",
        "source_count": d("5"),
        "primary_source_count": d("2"),
        "latest_source_age_minutes": d("15.000000"),
        "contradiction_severity": d("0.050000"),
        "resolution_rule_specificity": d("0.950000"),
        "minutes_until_market_close": d("240.000000"),
        "source_reference": "research-note-alpha",
    }
    values.update(overrides)
    return module.StrategyRecommendationInformationQualityGateV2Input(**values)


def report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_strategy_recommendation_information_quality_gate_v2(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def assert_numeric_fields_are_decimal(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if type(item) is bool:
            continue
        assert type(item) is not float
        assert type(item) is not int
        if isinstance(item, tuple):
            for nested in item:
                if is_dataclass(nested):
                    assert_numeric_fields_are_decimal(nested)


def assert_no_float_or_int_values(value: object) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def test_information_quality_gate_blocks_watches_and_passes_deterministically() -> None:
    result = report(
        recommendation(
            recommendation_id="rec-pass",
            market_slug="macro-fed",
            source_count=d("5"),
            primary_source_count=d("2"),
            latest_source_age_minutes=d("15.000000"),
            contradiction_severity=d("0.050000"),
            resolution_rule_specificity=d("0.950000"),
            minutes_until_market_close=d("240.000000"),
        ),
        recommendation(
            recommendation_id="rec-watch",
            market_slug="sports-final",
            source_count=d("3"),
            primary_source_count=d("1"),
            latest_source_age_minutes=d("90.000000"),
            contradiction_severity=d("0.300000"),
            resolution_rule_specificity=d("0.600000"),
            minutes_until_market_close=d("30.000000"),
        ),
        recommendation(
            recommendation_id="rec-block",
            market_slug="election-turnout",
            source_count=d("2"),
            primary_source_count=d("0"),
            latest_source_age_minutes=d("240.000000"),
            contradiction_severity=d("0.750000"),
            resolution_rule_specificity=d("0.300000"),
            minutes_until_market_close=d("20.000000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-recommendation-information-quality-gate-v2"
    assert result.recommendation_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.gate_status == "blocked"
    assert result.reason_codes == (
        "source_coverage_blocked",
        "source_coverage_weak",
        "primary_source_missing",
        "source_recency_blocked",
        "source_recency_stale",
        "contradiction_severity_blocked",
        "contradiction_severity_watch",
        "resolution_rule_specificity_blocked",
        "resolution_rule_specificity_watch",
        "market_close_urgency_blocked",
        "market_close_urgency_watch",
        "information_quality_gate_pass",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.validation_digest)
    assert_numeric_fields_are_decimal(result)

    assert tuple(row.recommendation_id for row in result.results) == (
        "rec-block",
        "rec-watch",
        "rec-pass",
    )

    blocked = result.results[0]
    assert blocked.market_slug == "election-turnout"
    assert blocked.source_coverage_ratio == d("0.500000")
    assert blocked.primary_source_ratio == d("0.000000")
    assert blocked.source_recency_score == d("0.000000")
    assert blocked.contradiction_score == d("0.250000")
    assert blocked.market_close_urgent is True
    assert blocked.gate_status == "blocked"
    assert blocked.reason_codes == (
        "source_coverage_blocked",
        "primary_source_missing",
        "source_recency_blocked",
        "contradiction_severity_blocked",
        "resolution_rule_specificity_blocked",
        "market_close_urgency_blocked",
    )
    assert_digest(blocked.validation_digest)

    watched = result.results[1]
    assert watched.source_coverage_ratio == d("0.750000")
    assert watched.primary_source_ratio == d("1.000000")
    assert watched.source_recency_score == d("0.500000")
    assert watched.contradiction_score == d("0.700000")
    assert watched.market_close_urgent is True
    assert watched.gate_status == "watch"
    assert watched.reason_codes == (
        "source_coverage_weak",
        "source_recency_stale",
        "contradiction_severity_watch",
        "resolution_rule_specificity_watch",
        "market_close_urgency_watch",
    )

    passed = result.results[2]
    assert passed.source_coverage_ratio == d("1.000000")
    assert passed.primary_source_ratio == d("1.000000")
    assert passed.source_recency_score == d("0.916667")
    assert passed.contradiction_score == d("0.950000")
    assert passed.market_close_urgent is False
    assert passed.gate_status == "pass"
    assert passed.reason_codes == ("information_quality_gate_pass",)
    assert blocked.information_quality_score < watched.information_quality_score
    assert watched.information_quality_score < passed.information_quality_score

    same_result = report(
        recommendation(
            recommendation_id="rec-pass",
            market_slug="macro-fed",
            source_count=d("5"),
            primary_source_count=d("2"),
            latest_source_age_minutes=d("15.000000"),
            contradiction_severity=d("0.050000"),
            resolution_rule_specificity=d("0.950000"),
            minutes_until_market_close=d("240.000000"),
        ),
        recommendation(
            recommendation_id="rec-watch",
            market_slug="sports-final",
            source_count=d("3"),
            primary_source_count=d("1"),
            latest_source_age_minutes=d("90.000000"),
            contradiction_severity=d("0.300000"),
            resolution_rule_specificity=d("0.600000"),
            minutes_until_market_close=d("30.000000"),
        ),
        recommendation(
            recommendation_id="rec-block",
            market_slug="election-turnout",
            source_count=d("2"),
            primary_source_count=d("0"),
            latest_source_age_minutes=d("240.000000"),
            contradiction_severity=d("0.750000"),
            resolution_rule_specificity=d("0.300000"),
            minutes_until_market_close=d("20.000000"),
        ),
    )
    assert same_result.validation_digest == result.validation_digest


def test_empty_report_is_blocked_readonly_and_decimal_zeroed() -> None:
    result = report()

    assert result.recommendation_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.blocked_count == d("0")
    assert result.gate_status == "blocked"
    assert result.reason_codes == (
        "strategy_recommendation_information_quality_gate_v2_empty",
    )
    assert result.results == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.validation_digest)


def test_payload_helper_is_json_ready_redacted_and_rejects_live_surfaces() -> None:
    module = api()
    result = report(
        recommendation(
            source_reference="https://example.test/feed?token=secret",
        ),
    )

    payload = module.strategy_recommendation_information_quality_gate_v2_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["recommendation_count"] == "1"
    assert payload["results"][0]["source_count"] == "5"
    assert payload["results"][0]["latest_source_age_minutes"] == "15.000000"
    assert payload["results"][0]["redacted_source_reference"] == "<redacted>"
    assert payload["results"][0]["validation_digest"] == result.results[0].validation_digest
    assert "token=secret" not in encoded
    assert_no_float_or_int_values(payload)
    assert (
        module.strategy_recommendation_information_quality_gate_v2_payload(payload)
        == payload
    )

    with pytest.raises(ValueError, match="readonly"):
        module.strategy_recommendation_information_quality_gate_v2_payload(
            {**payload, "readonly": False},
        )

    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_recommendation_information_quality_gate_v2_payload(
            {**payload, "wallet": {"address": "0x0"}},
        )

    with pytest.raises(ValueError, match="numeric"):
        module.strategy_recommendation_information_quality_gate_v2_payload(
            {**payload, "recommendation_count": 1},
        )

    with pytest.raises(ValueError, match="numeric"):
        module.strategy_recommendation_information_quality_gate_v2_payload(
            {**payload, "pass_count": 1.0},
        )


def test_inputs_config_and_datetimes_reject_invalid_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        recommendation(source_count=3)
    with pytest.raises(ValueError, match="source_count must be an integer"):
        recommendation(source_count=d("3.5"))
    with pytest.raises(ValueError, match="primary_source_count must not exceed source_count"):
        recommendation(source_count=d("1"), primary_source_count=d("2"))
    with pytest.raises(ValueError, match="latest_source_age_minutes must be nonnegative"):
        recommendation(latest_source_age_minutes=d("-0.000001"))
    with pytest.raises(ValueError, match="contradiction_severity must be between 0 and 1"):
        recommendation(contradiction_severity=d("1.100000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        recommendation(paper_only=False)
    with pytest.raises(ValueError, match="source_recency_pass_minutes must not exceed"):
        config(
            source_recency_pass_minutes=d("200.000000"),
            max_source_age_minutes=d("100.000000"),
        )
    with pytest.raises(ValueError, match="contradiction watch threshold must not exceed"):
        config(
            contradiction_severity_watch_threshold=d("0.700000"),
            contradiction_severity_block_threshold=d("0.600000"),
        )
    with pytest.raises(ValueError, match="resolution block threshold must not exceed"):
        config(
            resolution_rule_specificity_block_threshold=d("0.800000"),
            resolution_rule_specificity_pass_threshold=d("0.700000"),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_recommendation_information_quality_gate_v2(
            (recommendation(),),
            config=config(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_recommendation_information_quality_gate_v2(
            (recommendation(),),
            config=config(),
            generated_at=datetime(2026, 7, 6, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )

    with pytest.raises(ValueError, match="recommendation_id values must be unique"):
        report(recommendation(), recommendation())

    result = report(recommendation())
    with pytest.raises(FrozenInstanceError):
        result.results[0].gate_status = "blocked"


def test_validation_digest_and_report_validation_recompute_fields() -> None:
    result = report(recommendation())
    row = result.results[0]

    with pytest.raises(ValueError, match="information_quality_score must match"):
        replace(
            row,
            information_quality_score=row.information_quality_score + d("0.000001"),
        )

    with pytest.raises(ValueError, match="gate_status must match"):
        replace(row, gate_status="blocked")

    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(row, validation_digest="0" * 64)

    with pytest.raises(ValueError, match="pass_count must match"):
        replace(result, pass_count=result.pass_count + d("1"))

    with pytest.raises(ValueError, match="results must be sorted deterministically"):
        replace(
            result,
            results=(
                information_quality_result("rec-zeta"),
                information_quality_result("rec-alpha"),
            ),
        )

    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(result, validation_digest="0" * 64)


def information_quality_result(recommendation_id: str) -> Any:
    return report(recommendation(recommendation_id=recommendation_id)).results[0]


def test_module_is_pure_readonly_report_only_and_contains_no_io_surfaces() -> None:
    path = Path(
        "src/polymarket_alpha_lab/"
        "strategy_recommendation_information_quality_gate_v2.py",
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    source = path.read_text(encoding="utf-8").lower()

    banned_imports = {
        "asyncio",
        "http",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    banned_calls = {
        "connect",
        "delete",
        "execute",
        "insert",
        "login",
        "open",
        "post",
        "request",
        "send",
        "submit",
        "update",
        "urlopen",
        "write",
    }
    banned_attributes = banned_calls | {"commit", "replace", "rollback", "session"}
    forbidden_terms = (
        "auth",
        "broker",
        "database",
        "db write",
        "live trading",
        "network",
        "order",
        "supabase",
        "wallet",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_calls
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_attributes

    assert [term for term in forbidden_terms if term in source] == []
