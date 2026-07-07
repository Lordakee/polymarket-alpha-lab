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


MODULE_NAME = "polymarket_alpha_lab.strategy_recommendation_research_quality_join_v2"
GENERATED_AT = datetime(2026, 7, 7, 9, 30, tzinfo=UTC)


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
        "min_research_quality_score": d("0.650000"),
        "watch_research_quality_score": d("0.800000"),
        "min_counterevidence_quorum_ratio": d("0.500000"),
        "watch_counterevidence_quorum_ratio": d("0.750000"),
        "min_source_authority_score": d("0.500000"),
        "min_source_freshness_score": d("0.550000"),
        "watch_source_authority_score": d("0.700000"),
        "watch_source_freshness_score": d("0.750000"),
    }
    values.update(overrides)
    return module.StrategyRecommendationResearchQualityJoinV2Config(**values)


def recommendation(**overrides: object) -> Any:
    module = api()
    values = {
        "recommendation_id": "rec-alpha",
        "candidate_id": "cand-alpha",
        "market_id": "mkt-fed",
        "event_slug": "fed-decision-july",
        "category": "macro",
        "net_edge": d("0.120000"),
        "research_quality_score": d("0.900000"),
        "counterevidence_quorum_ratio": d("0.850000"),
        "source_authority_score": d("0.800000"),
        "source_freshness_score": d("0.900000"),
    }
    values.update(overrides)
    return module.StrategyRecommendationResearchQualityJoinV2Input(**values)


def report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_strategy_recommendation_research_quality_join_v2_report(
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


def test_research_quality_join_blocks_watches_and_passes_before_action() -> None:
    result = report(
        recommendation(
            recommendation_id="rec-pass",
            candidate_id="cand-pass",
            market_id="mkt-pass",
            event_slug="fed-decision-july",
            category="macro",
            net_edge=d("0.120000"),
            research_quality_score=d("0.900000"),
            counterevidence_quorum_ratio=d("0.850000"),
            source_authority_score=d("0.800000"),
            source_freshness_score=d("0.900000"),
        ),
        recommendation(
            recommendation_id="rec-watch",
            candidate_id="cand-watch",
            market_id="mkt-watch",
            event_slug="cup-final",
            category="sports",
            net_edge=d("0.090000"),
            research_quality_score=d("0.720000"),
            counterevidence_quorum_ratio=d("0.650000"),
            source_authority_score=d("0.620000"),
            source_freshness_score=d("0.650000"),
        ),
        recommendation(
            recommendation_id="rec-block",
            candidate_id="cand-block",
            market_id="mkt-block",
            event_slug="thin-rumor",
            category="politics",
            net_edge=d("0.200000"),
            research_quality_score=d("0.500000"),
            counterevidence_quorum_ratio=d("0.300000"),
            source_authority_score=d("0.400000"),
            source_freshness_score=d("0.450000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-recommendation-research-quality-join-v2"
    assert result.recommendation_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.low_quality_count == d("2")
    assert result.weak_counterevidence_count == d("2")
    assert result.stale_or_low_authority_count == d("2")
    assert result.max_quality_adjusted_edge == d("0.066096")
    assert result.report_status == "blocked"
    assert result.reason_code_counts == (
        ("research_quality_blocked", d("1")),
        ("research_quality_watch", d("1")),
        ("counterevidence_quorum_blocked", d("1")),
        ("counterevidence_quorum_watch", d("1")),
        ("source_authority_low", d("1")),
        ("source_freshness_stale", d("1")),
        ("source_authority_watch", d("1")),
        ("source_freshness_watch", d("1")),
        ("research_quality_join_pass", d("1")),
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.derived_validation_digest)
    assert_numeric_fields_are_decimal(result)

    assert tuple(row.recommendation_id for row in result.results) == (
        "rec-block",
        "rec-watch",
        "rec-pass",
    )

    blocked = result.results[0]
    assert blocked.quality_adjusted_edge == d("0.005400")
    assert blocked.status == "blocked"
    assert blocked.reason_codes == (
        "research_quality_blocked",
        "counterevidence_quorum_blocked",
        "source_authority_low",
        "source_freshness_stale",
    )
    assert_digest(blocked.derived_validation_digest)

    watched = result.results[1]
    assert watched.quality_adjusted_edge == d("0.016974")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "research_quality_watch",
        "counterevidence_quorum_watch",
        "source_authority_watch",
        "source_freshness_watch",
    )

    passed = result.results[2]
    assert passed.quality_adjusted_edge == d("0.066096")
    assert passed.status == "pass"
    assert passed.reason_codes == ("research_quality_join_pass",)

    same_result = report(
        recommendation(
            recommendation_id="rec-pass",
            candidate_id="cand-pass",
            market_id="mkt-pass",
            event_slug="fed-decision-july",
            category="macro",
            net_edge=d("0.120000"),
            research_quality_score=d("0.900000"),
            counterevidence_quorum_ratio=d("0.850000"),
            source_authority_score=d("0.800000"),
            source_freshness_score=d("0.900000"),
        ),
        recommendation(
            recommendation_id="rec-watch",
            candidate_id="cand-watch",
            market_id="mkt-watch",
            event_slug="cup-final",
            category="sports",
            net_edge=d("0.090000"),
            research_quality_score=d("0.720000"),
            counterevidence_quorum_ratio=d("0.650000"),
            source_authority_score=d("0.620000"),
            source_freshness_score=d("0.650000"),
        ),
        recommendation(
            recommendation_id="rec-block",
            candidate_id="cand-block",
            market_id="mkt-block",
            event_slug="thin-rumor",
            category="politics",
            net_edge=d("0.200000"),
            research_quality_score=d("0.500000"),
            counterevidence_quorum_ratio=d("0.300000"),
            source_authority_score=d("0.400000"),
            source_freshness_score=d("0.450000"),
        ),
    )
    assert same_result.derived_validation_digest == result.derived_validation_digest


def test_empty_report_is_empty_status_and_decimal_zeroed() -> None:
    result = report()

    assert result.recommendation_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.blocked_count == d("0")
    assert result.low_quality_count == d("0")
    assert result.weak_counterevidence_count == d("0")
    assert result.stale_or_low_authority_count == d("0")
    assert result.max_quality_adjusted_edge == d("0.000000")
    assert result.report_status == "empty"
    assert result.reason_code_counts == ()
    assert result.results == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.derived_validation_digest)
    assert_numeric_fields_are_decimal(result)


def test_payload_helper_is_json_ready_and_rejects_live_surfaces() -> None:
    module = api()
    result = report(recommendation())

    payload = module.strategy_recommendation_research_quality_join_v2_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["generated_at"] == "2026-07-07T09:30:00+00:00"
    assert payload["recommendation_count"] == "1"
    assert payload["pass_count"] == "1"
    assert payload["max_quality_adjusted_edge"] == "0.066096"
    assert payload["reason_code_counts"] == [["research_quality_join_pass", "1"]]
    assert payload["results"][0]["net_edge"] == "0.120000"
    assert payload["results"][0]["quality_adjusted_edge"] == "0.066096"
    assert payload["results"][0]["derived_validation_digest"] == (
        result.results[0].derived_validation_digest
    )
    assert "wallet" not in encoded.lower()
    assert_no_float_or_int_values(payload)
    assert module.strategy_recommendation_research_quality_join_v2_payload(payload) == payload

    with pytest.raises(ValueError, match="readonly"):
        module.strategy_recommendation_research_quality_join_v2_payload(
            {**payload, "readonly": False},
        )

    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_recommendation_research_quality_join_v2_payload(
            {**payload, "wallet": {"address": "0x0"}},
        )

    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_recommendation_research_quality_join_v2_payload(
            {**payload, "public_note": "contains wallet reference"},
        )

    with pytest.raises(ValueError, match="numeric"):
        module.strategy_recommendation_research_quality_join_v2_payload(
            {**payload, "recommendation_count": 1},
        )

    with pytest.raises(ValueError, match="numeric"):
        module.strategy_recommendation_research_quality_join_v2_payload(
            {**payload, "max_quality_adjusted_edge": 1.0},
        )


def test_inputs_config_and_datetimes_reject_invalid_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="net_edge must be a Decimal"):
        recommendation(net_edge=0.12)
    with pytest.raises(ValueError, match="net_edge must be nonnegative"):
        recommendation(net_edge=d("-0.000001"))
    with pytest.raises(ValueError, match="research_quality_score must be between 0 and 1"):
        recommendation(research_quality_score=d("1.100000"))
    with pytest.raises(ValueError, match="counterevidence_quorum_ratio must be between 0 and 1"):
        recommendation(counterevidence_quorum_ratio=d("-0.000001"))
    with pytest.raises(ValueError, match="candidate_id must be a non-empty canonical string"):
        recommendation(candidate_id=" cand-alpha")
    with pytest.raises(ValueError, match="paper_only must be True"):
        recommendation(paper_only=False)
    with pytest.raises(ValueError, match="minimum quality threshold must not exceed watch"):
        config(
            min_research_quality_score=d("0.900000"),
            watch_research_quality_score=d("0.800000"),
        )
    with pytest.raises(
        ValueError,
        match="minimum counterevidence threshold must not exceed watch",
    ):
        config(
            min_counterevidence_quorum_ratio=d("0.900000"),
            watch_counterevidence_quorum_ratio=d("0.800000"),
        )
    with pytest.raises(ValueError, match="minimum authority threshold must not exceed watch"):
        config(
            min_source_authority_score=d("0.900000"),
            watch_source_authority_score=d("0.800000"),
        )
    with pytest.raises(ValueError, match="minimum freshness threshold must not exceed watch"):
        config(
            min_source_freshness_score=d("0.900000"),
            watch_source_freshness_score=d("0.800000"),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_recommendation_research_quality_join_v2_report(
            (recommendation(),),
            config=config(),
            generated_at=datetime(2026, 7, 7, 9, 30),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_recommendation_research_quality_join_v2_report(
            (recommendation(),),
            config=config(),
            generated_at=datetime(2026, 7, 7, 9, 30, tzinfo=_NoneOffsetTimezone()),
        )

    with pytest.raises(ValueError, match="recommendation_id values must be unique"):
        report(recommendation(), recommendation(candidate_id="cand-beta"))

    result = report(recommendation())
    with pytest.raises(FrozenInstanceError):
        result.results[0].status = "blocked"


def test_derived_validation_digest_and_report_validation_recompute_fields() -> None:
    result = report(recommendation())
    row = result.results[0]

    with pytest.raises(ValueError, match="quality_adjusted_edge must match"):
        replace(
            row,
            quality_adjusted_edge=row.quality_adjusted_edge + d("0.000001"),
        )

    with pytest.raises(ValueError, match="status must match"):
        replace(row, status="blocked")

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(row, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="pass_count must match"):
        replace(result, pass_count=result.pass_count + d("1"))

    with pytest.raises(ValueError, match="results must be sorted deterministically"):
        replace(
            result,
            results=(
                quality_join_result("rec-zeta", "cand-zeta"),
                quality_join_result("rec-alpha", "cand-alpha"),
            ),
        )

    with pytest.raises(ValueError, match="reason_code_counts must match"):
        replace(result, reason_code_counts=(("research_quality_join_pass", d("2")),))

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(result, derived_validation_digest="0" * 64)


def quality_join_result(recommendation_id: str, candidate_id: str) -> Any:
    return report(
        recommendation(
            recommendation_id=recommendation_id,
            candidate_id=candidate_id,
        ),
    ).results[0]


def test_module_is_pure_readonly_report_only_and_contains_no_io_surfaces() -> None:
    path = Path(
        "src/polymarket_alpha_lab/"
        "strategy_recommendation_research_quality_join_v2.py",
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
        "authorization",
        "private_key",
        "credential",
        "api_key",
        "bearer",
        "signing",
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
