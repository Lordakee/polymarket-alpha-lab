from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_team_domain_feedback_loop_latency_report.py",
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(hours=2)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_domain_feedback_loop_latency_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-team-domain-feedback-loop-latency-report-v0",
        "watch_feedback_age_hours": d("24.000000"),
        "block_feedback_age_hours": d("72.000000"),
        "watch_calibration_uptake_delay_hours": d("48.000000"),
        "block_calibration_uptake_delay_hours": d("168.000000"),
        "watch_conflict_carry_forward_ratio": d("0.250000"),
        "block_conflict_carry_forward_ratio": d("0.600000"),
        "watch_review_backlog_pressure": d("0.600000"),
        "block_review_backlog_pressure": d("0.900000"),
        "watch_latency_pressure": d("0.500000"),
        "block_latency_pressure": d("0.850000"),
        "feedback_age_weight": d("0.250000"),
        "calibration_delay_weight": d("0.250000"),
        "conflict_carry_forward_weight": d("0.250000"),
        "review_backlog_weight": d("0.250000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainFeedbackLoopLatencyConfig(**values)


def feedback_signal(**overrides: object):
    module = api()
    values = {
        "domain_key": "macro_rates",
        "feedback_signal_count": d("10.000000"),
        "total_feedback_age_hours": d("120.000000"),
        "calibration_update_count": d("5.000000"),
        "total_calibration_uptake_delay_hours": d("40.000000"),
        "unresolved_conflict_count": d("4.000000"),
        "carried_forward_conflict_count": d("0.000000"),
        "review_backlog_count": d("2.000000"),
        "review_capacity_count": d("10.000000"),
        "observed_at": OBSERVED_AT,
    }
    values.update(overrides)
    return module.ResearchTeamDomainFeedbackLoopLatencyInput(**values)


def build_report(*signals: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_domain_feedback_loop_latency_report(
        signals,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_float_or_int_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_float_or_int_values(child)
    if isinstance(value, list):
        for child in value:
            assert_no_float_or_int_values(child)


def payload_keys(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, child in value.items():
            keys.append(key)
            keys.extend(payload_keys(child))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for child in value:
            keys.extend(payload_keys(child))
        return tuple(keys)
    return ()


def domain_inputs() -> tuple[object, ...]:
    return (
        feedback_signal(
            domain_key="macro_rates",
            feedback_signal_count=d("4.000000"),
            total_feedback_age_hours=d("40.000000"),
            calibration_update_count=d("2.000000"),
            total_calibration_uptake_delay_hours=d("16.000000"),
            unresolved_conflict_count=d("1.000000"),
            carried_forward_conflict_count=d("0.000000"),
            review_backlog_count=d("1.000000"),
            review_capacity_count=d("4.000000"),
            observed_at=GENERATED_AT - timedelta(hours=3),
        ),
        feedback_signal(
            domain_key="macro_rates",
            feedback_signal_count=d("6.000000"),
            total_feedback_age_hours=d("80.000000"),
            calibration_update_count=d("3.000000"),
            total_calibration_uptake_delay_hours=d("24.000000"),
            unresolved_conflict_count=d("3.000000"),
            carried_forward_conflict_count=d("0.000000"),
            review_backlog_count=d("1.000000"),
            review_capacity_count=d("6.000000"),
            observed_at=GENERATED_AT - timedelta(hours=1),
        ),
        feedback_signal(
            domain_key="sports_soccer",
            feedback_signal_count=d("6.000000"),
            total_feedback_age_hours=d("180.000000"),
            calibration_update_count=d("4.000000"),
            total_calibration_uptake_delay_hours=d("240.000000"),
            unresolved_conflict_count=d("5.000000"),
            carried_forward_conflict_count=d("2.000000"),
            review_backlog_count=d("7.000000"),
            review_capacity_count=d("10.000000"),
        ),
        feedback_signal(
            domain_key="crypto_btc",
            feedback_signal_count=d("3.000000"),
            total_feedback_age_hours=d("240.000000"),
            calibration_update_count=d("2.000000"),
            total_calibration_uptake_delay_hours=d("400.000000"),
            unresolved_conflict_count=d("5.000000"),
            carried_forward_conflict_count=d("4.000000"),
            review_backlog_count=d("10.000000"),
            review_capacity_count=d("10.000000"),
        ),
    )


def test_feedback_loop_latency_aggregates_domain_pass_watch_and_block_rows() -> None:
    module = api()

    result = build_report(*reversed(domain_inputs()))

    assert is_dataclass(result)
    assert module.FEEDBACK_LOOP_LATENCY_STATUSES == ("pass", "watch", "block")
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "research-team-domain-feedback-loop-latency-report-v0"
    assert result.domain_count == d("3.000000")
    assert result.total_feedback_signal_count == d("19.000000")
    assert result.total_calibration_update_count == d("11.000000")
    assert result.total_unresolved_conflict_count == d("14.000000")
    assert result.total_carried_forward_conflict_count == d("6.000000")
    assert result.total_review_backlog_count == d("19.000000")
    assert result.total_review_capacity_count == d("30.000000")
    assert result.aggregate_feedback_age_hours == d("28.421053")
    assert result.aggregate_calibration_uptake_delay_hours == d("61.818182")
    assert result.aggregate_conflict_carry_forward_ratio == d("0.428571")
    assert result.aggregate_review_backlog_pressure == d("0.633333")
    assert result.max_latency_pressure == d("1.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.report_status == "block"
    assert result.reason_codes == (
        "feedback_loop_latency_report_block",
        "feedback_loop_latency_block",
        "feedback_age_block",
        "calibration_uptake_delay_block",
        "conflict_carry_forward_block",
        "review_backlog_pressure_block",
        "latency_pressure_block",
        "feedback_loop_latency_watch",
        "feedback_age_watch",
        "calibration_uptake_delay_watch",
        "conflict_carry_forward_watch",
        "review_backlog_pressure_watch",
        "latency_pressure_watch",
        "feedback_loop_latency_pass",
    )
    assert len(result.derived_validation_digest) == 64

    blocked, watched, passed = result.rows
    assert tuple(row.domain_key for row in result.rows) == (
        "crypto_btc",
        "sports_soccer",
        "macro_rates",
    )
    assert tuple(row.latency_status for row in result.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert blocked.mean_feedback_age_hours == d("80.000000")
    assert blocked.mean_calibration_uptake_delay_hours == d("200.000000")
    assert blocked.conflict_carry_forward_ratio == d("0.800000")
    assert blocked.review_backlog_pressure == d("1.000000")
    assert blocked.latency_pressure == d("1.000000")
    assert blocked.reason_codes == (
        "feedback_loop_latency_block",
        "feedback_age_block",
        "calibration_uptake_delay_block",
        "conflict_carry_forward_block",
        "review_backlog_pressure_block",
        "latency_pressure_block",
    )

    assert watched.mean_feedback_age_hours == d("30.000000")
    assert watched.mean_calibration_uptake_delay_hours == d("60.000000")
    assert watched.conflict_carry_forward_ratio == d("0.400000")
    assert watched.review_backlog_pressure == d("0.700000")
    assert watched.latency_pressure == d("0.554564")
    assert watched.reason_codes == (
        "feedback_loop_latency_watch",
        "feedback_age_watch",
        "calibration_uptake_delay_watch",
        "conflict_carry_forward_watch",
        "review_backlog_pressure_watch",
        "latency_pressure_watch",
    )

    assert passed.feedback_signal_count == d("10.000000")
    assert passed.mean_feedback_age_hours == d("12.000000")
    assert passed.mean_calibration_uptake_delay_hours == d("8.000000")
    assert passed.conflict_carry_forward_ratio == d("0.000000")
    assert passed.review_backlog_pressure == d("0.200000")
    assert passed.observed_at == GENERATED_AT - timedelta(hours=1)
    assert passed.reason_codes == ("feedback_loop_latency_pass",)

    assert result.reason_code_counts[0].reason_code == "feedback_loop_latency_block"
    assert result.reason_code_counts[0].count == d("1.000000")
    assert result.reason_code_counts[0].domain_ratio == d("0.333333")


def test_empty_feedback_latency_report_is_pass_with_decimal_zeroes() -> None:
    result = build_report()

    assert result.domain_count == d("0.000000")
    assert result.total_feedback_signal_count == d("0.000000")
    assert result.total_calibration_update_count == d("0.000000")
    assert result.total_unresolved_conflict_count == d("0.000000")
    assert result.total_carried_forward_conflict_count == d("0.000000")
    assert result.total_review_backlog_count == d("0.000000")
    assert result.total_review_capacity_count == d("0.000000")
    assert result.aggregate_feedback_age_hours == d("0.000000")
    assert result.aggregate_calibration_uptake_delay_hours == d("0.000000")
    assert result.aggregate_conflict_carry_forward_ratio == d("0.000000")
    assert result.aggregate_review_backlog_pressure == d("0.000000")
    assert result.max_latency_pressure == d("0.000000")
    assert result.pass_count == d("0.000000")
    assert result.watch_count == d("0.000000")
    assert result.block_count == d("0.000000")
    assert result.report_status == "pass"
    assert result.reason_codes == ("feedback_loop_latency_empty",)
    assert result.reason_code_counts == ()
    assert result.rows == ()

    populated = build_report(feedback_signal())
    for value in (result, populated, *populated.rows, *populated.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item.name.endswith(("_count", "_hours", "_ratio", "_pressure")):
                assert type(item_value) is Decimal


def test_custom_config_drives_feedback_latency_status_and_reason_codes() -> None:
    custom = config(
        watch_feedback_age_hours=d("10.000000"),
        block_feedback_age_hours=d("90.000000"),
        watch_calibration_uptake_delay_hours=d("6.000000"),
        block_calibration_uptake_delay_hours=d("240.000000"),
        watch_conflict_carry_forward_ratio=d("0.010000"),
        block_conflict_carry_forward_ratio=d("0.900000"),
        watch_review_backlog_pressure=d("0.100000"),
        block_review_backlog_pressure=d("0.950000"),
        watch_latency_pressure=d("0.050000"),
        block_latency_pressure=d("0.950000"),
    )

    result = build_report(feedback_signal(), cfg=custom)

    assert result.report_status == "watch"
    assert result.rows[0].latency_status == "watch"
    assert result.rows[0].reason_codes == (
        "feedback_loop_latency_watch",
        "feedback_age_watch",
        "calibration_uptake_delay_watch",
        "review_backlog_pressure_watch",
        "latency_pressure_watch",
    )


def test_payload_is_deterministic_decimal_only_public_safe_and_digest_checked() -> None:
    module = api()
    first = build_report(
        feedback_signal(
            domain_key="basketball_stats",
            feedback_signal_count=d("6.000000"),
            total_feedback_age_hours=d("180.000000"),
            calibration_update_count=d("4.000000"),
            total_calibration_uptake_delay_hours=d("240.000000"),
            unresolved_conflict_count=d("5.000000"),
            carried_forward_conflict_count=d("2.000000"),
            review_backlog_count=d("7.000000"),
            review_capacity_count=d("10.000000"),
            observed_at=datetime(
                2026,
                7,
                8,
                4,
                30,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        feedback_signal(domain_key="macro_rates"),
        generated_at=datetime(
            2026,
            7,
            8,
            5,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )
    second = build_report(
        feedback_signal(domain_key="macro_rates"),
        feedback_signal(
            domain_key="basketball_stats",
            feedback_signal_count=d("6.000000"),
            total_feedback_age_hours=d("180.000000"),
            calibration_update_count=d("4.000000"),
            total_calibration_uptake_delay_hours=d("240.000000"),
            unresolved_conflict_count=d("5.000000"),
            carried_forward_conflict_count=d("2.000000"),
            review_backlog_count=d("7.000000"),
            review_capacity_count=d("10.000000"),
            observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=UTC),
        ),
    )

    assert first.generated_at == GENERATED_AT
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first.payload == second.payload

    payload = module.research_team_domain_feedback_loop_latency_report_payload(first)
    repeat_payload = module.research_team_domain_feedback_loop_latency_report_payload(
        second,
    )
    assert payload == repeat_payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["domain_count"] == "2.000000"
    assert payload["rows"][0]["domain_key"] == "basketball_stats"
    assert payload["rows"][0]["observed_at"] == "2026-07-08T11:30:00+00:00"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert_no_float_or_int_values(payload)
    json.dumps(payload, sort_keys=True)
    assert module.validate_research_team_domain_feedback_loop_latency_report_payload(
        payload,
    )

    forbidden_fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "source_text",
        "raw_source",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "recommend",
        "sizing",
    )
    assert not any(
        fragment in key.lower()
        for key in payload_keys(payload)
        for fragment in forbidden_fragments
    )
    payload_text = repr(payload).lower()
    assert not any(fragment in payload_text for fragment in forbidden_fragments)

    tampered = dict(payload)
    tampered["pass_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_team_domain_feedback_loop_latency_report_payload(
            tampered,
        )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, pass_count=d("2.000000"))


def test_public_payload_rejects_identifiers_sensitive_surfaces_and_numbers() -> None:
    module = api()
    payload = module.research_team_domain_feedback_loop_latency_report_payload(
        build_report(feedback_signal(domain_key="crypto_eth")),
    )

    for key in (
        "raw_candidate_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet_address",
        "auth_header",
        "order_id",
        "trade_id",
        "live_url",
        "position_sizing",
        "recommendation_id",
    ):
        unsafe = dict(payload)
        unsafe[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            module.research_team_domain_feedback_loop_latency_report_payload(unsafe)

    for value in (
        "candidate id",
        "market slug",
        "market question",
        "source text",
        "dsn",
        "table name",
        "token",
        "wallet signer",
        "auth token",
        "order route",
        "trade route",
        "live execution",
        "recommendation",
        "sizing",
    ):
        unsafe = dict(payload)
        unsafe["reason_codes"] = (value,)
        with pytest.raises(ValueError, match="unsafe public"):
            module.research_team_domain_feedback_loop_latency_report_payload(unsafe)

    numeric = dict(payload)
    numeric["domain_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        module.research_team_domain_feedback_loop_latency_report_payload(numeric)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.research_team_domain_feedback_loop_latency_report_payload(downgraded)


def test_dataclasses_are_frozen_and_validate_exact_types_and_flags() -> None:
    module = api()
    signal = feedback_signal()

    with pytest.raises(FrozenInstanceError):
        signal.feedback_signal_count = d("12.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="feedback_signal_count must be a Decimal"):
        feedback_signal(feedback_signal_count=10)
    with pytest.raises(ValueError, match="review_backlog_count must be a Decimal"):
        feedback_signal(review_backlog_count=1.0)
    with pytest.raises(ValueError, match="total_feedback_age_hours must be a Decimal"):
        feedback_signal(total_feedback_age_hours=_DecimalSubclass("120.000000"))
    with pytest.raises(ValueError, match="feedback_signal_count must be integral"):
        feedback_signal(feedback_signal_count=d("10.500000"))
    with pytest.raises(ValueError, match="review_capacity_count"):
        feedback_signal(review_capacity_count=d("0.000000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(feedback_signal(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        feedback_signal(observed_at=datetime(2026, 7, 8, 11, 45))
    with pytest.raises(ValueError, match="observed_at"):
        feedback_signal(observed_at=_DatetimeSubclass(2026, 7, 8, 11, 45, tzinfo=UTC))
    with pytest.raises(ValueError, match="future"):
        build_report(feedback_signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="domain_key must be a public code"):
        feedback_signal(domain_key="macro rates")
    with pytest.raises(ValueError, match="paper_only"):
        feedback_signal(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_report(feedback_signal(), cfg=object())
    with pytest.raises(ValueError, match="latency_status"):
        module.ResearchTeamDomainFeedbackLoopLatencyRow(
            **{
                **build_report(feedback_signal()).rows[0].__dict__,
                "latency_status": "review",
            },
        )


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    module = api()
    decimal_fields = {
        "watch_feedback_age_hours",
        "block_feedback_age_hours",
        "watch_calibration_uptake_delay_hours",
        "block_calibration_uptake_delay_hours",
        "watch_conflict_carry_forward_ratio",
        "block_conflict_carry_forward_ratio",
        "watch_review_backlog_pressure",
        "block_review_backlog_pressure",
        "watch_latency_pressure",
        "block_latency_pressure",
        "feedback_age_weight",
        "calibration_delay_weight",
        "conflict_carry_forward_weight",
        "review_backlog_weight",
        "feedback_signal_count",
        "total_feedback_age_hours",
        "calibration_update_count",
        "total_calibration_uptake_delay_hours",
        "unresolved_conflict_count",
        "carried_forward_conflict_count",
        "review_backlog_count",
        "review_capacity_count",
        "mean_feedback_age_hours",
        "mean_calibration_uptake_delay_hours",
        "conflict_carry_forward_ratio",
        "review_backlog_pressure",
        "latency_pressure",
        "domain_count",
        "total_feedback_signal_count",
        "total_calibration_update_count",
        "total_unresolved_conflict_count",
        "total_carried_forward_conflict_count",
        "total_review_backlog_count",
        "total_review_capacity_count",
        "aggregate_feedback_age_hours",
        "aggregate_calibration_uptake_delay_hours",
        "aggregate_conflict_carry_forward_ratio",
        "aggregate_review_backlog_pressure",
        "max_latency_pressure",
        "pass_count",
        "watch_count",
        "block_count",
        "count",
        "domain_ratio",
    }

    for cls in (
        module.ResearchTeamDomainFeedbackLoopLatencyConfig,
        module.ResearchTeamDomainFeedbackLoopLatencyInput,
        module.ResearchTeamDomainFeedbackLoopLatencyRow,
        module.ResearchTeamDomainFeedbackLoopLatencyReasonCodeCount,
        module.ResearchTeamDomainFeedbackLoopLatencyReport,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in decimal_fields:
                assert hints[item.name] is Decimal


def test_module_is_report_only_without_external_write_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "candidate",
        "market",
        "slug",
        "question",
        "source_text",
        "raw_source",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
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
        "float",
        "open",
        "request",
        "send",
        "urlopen",
        "write",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
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
