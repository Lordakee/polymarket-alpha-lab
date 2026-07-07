from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from numbers import Number
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_packet_breaking_news_source_triage_v2"


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def source_input(
    source_ref: str = "source-main",
    *,
    packet_ref: str = "packet-alpha",
    question_ref: str = "question-alpha",
    source_kind: str = "official",
    source_age_seconds: str = "60.000000",
    corroboration_count: str = "2.000000",
    contradiction_risk_score: str = "0.000000",
    market_probability_move_abs: str = "0.000000",
    market_close_horizon_seconds: str = "200000.000000",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchPacketBreakingNewsSourceTriageV2Input(
        packet_ref=packet_ref,
        question_ref=question_ref,
        source_ref=source_ref,
        source_kind=source_kind,
        source_age_seconds=d(source_age_seconds),
        corroboration_count=d(corroboration_count),
        contradiction_risk_score=d(contradiction_risk_score),
        market_probability_move_abs=d(market_probability_move_abs),
        market_close_horizon_seconds=d(market_close_horizon_seconds),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*rows: object):
    module = api()
    return module.build_research_packet_breaking_news_source_triage_v2_report(rows)


def assert_no_numeric_payload_values(value: Any) -> None:
    if isinstance(value, Number) and type(value) is not bool:
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_numeric_payload_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_numeric_payload_values(item)


def test_builds_phase1_breaking_news_source_triage_report_from_decimal_inputs() -> None:
    result = report(
        source_input(
            "unofficial-breaking",
            source_kind="unofficial",
            source_age_seconds="7200.000000",
            corroboration_count="0.000000",
            contradiction_risk_score="0.800000",
            market_probability_move_abs="0.070000",
            market_close_horizon_seconds="1800.000000",
        ),
        source_input(
            "official-watch",
            source_kind="official",
            source_age_seconds="600.000000",
            corroboration_count="1.000000",
            contradiction_risk_score="0.200000",
            market_probability_move_abs="0.010000",
            market_close_horizon_seconds="72000.000000",
        ),
        source_input("official-clear", source_kind="official"),
    )

    assert result.config_version == "research-packet-breaking-news-source-triage-v2-v0"
    assert result.report_status == "blocked"
    assert result.recommended_follow_up_priority == "immediate"
    assert result.input_count == d("3.000000")
    assert result.blocked_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.pass_count == d("1.000000")
    assert result.official_source_count == d("2.000000")
    assert result.unofficial_source_count == d("1.000000")
    assert result.stale_source_count == d("1.000000")
    assert result.weak_corroboration_count == d("2.000000")
    assert result.contradiction_risk_count == d("2.000000")
    assert result.high_contradiction_risk_count == d("1.000000")
    assert result.large_market_probability_move_count == d("1.000000")
    assert result.market_close_urgent_count == d("1.000000")
    assert result.highest_priority_score == d("0.960000")
    assert result.reason_codes == (
        "breaking_news_source_triage_status_blocked",
        "breaking_news_source_unofficial",
        "breaking_news_source_stale",
        "breaking_news_corroboration_weak",
        "breaking_news_contradiction_elevated",
        "breaking_news_contradiction_high",
        "breaking_news_market_probability_move_large",
        "breaking_news_market_close_urgent",
    )

    blocked, watched, passed = result.rows
    assert blocked.source_ref == "unofficial-breaking"
    assert blocked.priority_rank == d("1.000000")
    assert blocked.priority_score == d("0.960000")
    assert blocked.unofficial_source_score == d("1.000000")
    assert blocked.source_age_score == d("1.000000")
    assert blocked.corroboration_gap_score == d("1.000000")
    assert blocked.contradiction_risk_score == d("0.800000")
    assert blocked.market_probability_move_score == d("1.000000")
    assert blocked.close_urgency_score == d("1.000000")
    assert blocked.triage_status == "blocked"
    assert blocked.recommended_follow_up_priority == "immediate"
    assert blocked.reason_codes == (
        "breaking_news_source_triage_status_blocked",
        "breaking_news_source_unofficial",
        "breaking_news_source_stale",
        "breaking_news_corroboration_weak",
        "breaking_news_contradiction_high",
        "breaking_news_market_probability_move_large",
        "breaking_news_market_close_urgent",
    )

    assert watched.source_ref == "official-watch"
    assert watched.priority_rank == d("2.000000")
    assert watched.priority_score == d("0.171087")
    assert watched.triage_status == "watch"
    assert watched.recommended_follow_up_priority == "elevated"
    assert watched.reason_codes == (
        "breaking_news_source_triage_status_watch",
        "breaking_news_corroboration_weak",
        "breaking_news_contradiction_elevated",
    )

    assert passed.source_ref == "official-clear"
    assert passed.priority_rank == d("3.000000")
    assert passed.priority_score == d("0.000000")
    assert passed.triage_status == "pass"
    assert passed.recommended_follow_up_priority == "routine"
    assert passed.reason_codes == ("breaking_news_source_triage_status_pass",)
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True


def test_payload_round_trips_decimal_strings_and_stable_digests() -> None:
    module = api()
    result = report(
        source_input(
            "unofficial-breaking",
            source_kind="unofficial",
            source_age_seconds="7200.000000",
            corroboration_count="0.000000",
            contradiction_risk_score="0.800000",
            market_probability_move_abs="0.070000",
            market_close_horizon_seconds="1800.000000",
        ),
        source_input("official-clear", source_kind="official"),
    )
    rebuilt = report(
        source_input(
            "unofficial-breaking",
            source_kind="unofficial",
            source_age_seconds="7200.000000",
            corroboration_count="0.000000",
            contradiction_risk_score="0.800000",
            market_probability_move_abs="0.070000",
            market_close_horizon_seconds="1800.000000",
        ),
        source_input("official-clear", source_kind="official"),
    )

    assert result.derived_validation_digest == rebuilt.derived_validation_digest
    assert tuple(row.derived_validation_digest for row in result.rows) == tuple(
        row.derived_validation_digest for row in rebuilt.rows
    )

    payload = module.research_packet_breaking_news_source_triage_v2_payload(result)

    assert tuple(payload) == (
        "config_version",
        "report_status",
        "recommended_follow_up_priority",
        "input_count",
        "blocked_count",
        "watch_count",
        "pass_count",
        "official_source_count",
        "unofficial_source_count",
        "stale_source_count",
        "weak_corroboration_count",
        "contradiction_risk_count",
        "high_contradiction_risk_count",
        "large_market_probability_move_count",
        "market_close_urgent_count",
        "highest_priority_score",
        "rows",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert payload["input_count"] == "2.000000"
    assert payload["highest_priority_score"] == "0.960000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert isinstance(payload["rows"], list)
    assert tuple(payload["rows"][0]) == (
        "packet_ref",
        "question_ref",
        "source_ref",
        "source_kind",
        "priority_rank",
        "priority_score",
        "unofficial_source_score",
        "source_age_score",
        "corroboration_gap_score",
        "contradiction_risk_score",
        "market_probability_move_score",
        "close_urgency_score",
        "source_age_seconds",
        "corroboration_count",
        "market_probability_move_abs",
        "market_close_horizon_seconds",
        "triage_status",
        "recommended_follow_up_priority",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert payload["rows"][0]["priority_score"] == "0.960000"
    assert payload["rows"][0]["source_age_seconds"] == "7200.000000"
    assert len(payload["derived_validation_digest"]) == 64
    assert len(payload["rows"][0]["derived_validation_digest"]) == 64
    assert_no_numeric_payload_values(payload)

    restored = module.ResearchPacketBreakingNewsSourceTriageV2Report.from_payload(payload)
    assert restored == result

    tampered = dict(payload)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        module.ResearchPacketBreakingNewsSourceTriageV2Report.from_payload(tampered)


def test_outputs_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    result = report(source_input("official-clear"))

    with pytest.raises(FrozenInstanceError):
        result.rows[0].triage_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="source_age_seconds must be a Decimal"):
        module.ResearchPacketBreakingNewsSourceTriageV2Input(
            packet_ref="packet-alpha",
            question_ref="question-alpha",
            source_ref="bad-age",
            source_kind="official",
            source_age_seconds=0.1,
            corroboration_count=d("2.000000"),
            contradiction_risk_score=d("0.000000"),
            market_probability_move_abs=d("0.000000"),
            market_close_horizon_seconds=d("200000.000000"),
        )
    with pytest.raises(ValueError, match="market_probability_move_abs must be between"):
        source_input("bad-move", market_probability_move_abs="1.100000")
    with pytest.raises(ValueError, match="readonly must be True"):
        source_input("bad-flag", readonly=False)
    with pytest.raises(ValueError, match="reason_codes must use deterministic sequence"):
        replace(
            result.rows[0],
            reason_codes=(
                "breaking_news_source_stale",
                "breaking_news_source_triage_status_pass",
            ),
        )
    with pytest.raises(ValueError, match="report must be a"):
        module.research_packet_breaking_news_source_triage_v2_payload(object())


def test_empty_report_is_blocked_without_losing_decimal_payload_contract() -> None:
    module = api()
    result = report()
    payload = module.research_packet_breaking_news_source_triage_v2_payload(result)

    assert result.report_status == "blocked"
    assert result.recommended_follow_up_priority == "immediate"
    assert result.input_count == d("0.000000")
    assert result.rows == ()
    assert result.reason_codes == ("breaking_news_source_triage_no_inputs",)
    assert payload["input_count"] == "0.000000"
    assert payload["rows"] == []
    assert_no_numeric_payload_values(payload)


def test_module_is_pure_and_has_no_io_or_action_surface() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    forbidden_import_roots = {
        "http",
        "io",
        "json",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_call_names = {
        "open",
        "print",
        "input",
        "compile",
        "eval",
        "exec",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "trade",
    }
    forbidden_attr_fragments = (
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "network",
        "persist",
        "request",
        "secret",
        "sign",
        "submit",
        "trade",
        "wallet",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots = {alias.name.split(".", 1)[0] for alias in node.names}
            assert imported_roots.isdisjoint(forbidden_import_roots)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
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
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
