from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


GENERATED_AT = datetime(2026, 7, 8, 15, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_decision_readiness_memory_scorecard_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_strategy_decision_readiness_memory_scorecard_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def memory_signal(**overrides: object):
    module = api()
    values = {
        "memory_signal_key": "macro_policy_signal_alpha",
        "domain_key": "macro_policy",
        "observed_at": GENERATED_AT - timedelta(minutes=30),
        "calibration_age_hours": d("12.000000"),
        "evidence_completeness_ratio": d("0.900000"),
        "prior_error_absorption_ratio": d("0.850000"),
        "liquidity_cost_pressure_ratio": d("0.100000"),
        "review_backlog_ratio": d("0.050000"),
    }
    values.update(overrides)
    return module.ResearchStrategyDecisionReadinessMemoryScorecardInput(**values)


def config(**overrides: object):
    module = api()
    return module.ResearchStrategyDecisionReadinessMemoryScorecardConfig(**overrides)


def build_report(
    *signals: object,
    config_override=None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_research_strategy_decision_readiness_memory_scorecard_report(
        signals,
        generated_at=generated_at,
        config=config() if config_override is None else config_override,
    )


def sample_signals() -> tuple[object, ...]:
    return (
        memory_signal(
            memory_signal_key="macro_policy_signal_alpha",
            domain_key="macro_policy",
            calibration_age_hours=d("12.000000"),
            evidence_completeness_ratio=d("0.900000"),
            prior_error_absorption_ratio=d("0.850000"),
            liquidity_cost_pressure_ratio=d("0.100000"),
            review_backlog_ratio=d("0.050000"),
        ),
        memory_signal(
            memory_signal_key="earnings_cycle_signal_beta",
            domain_key="earnings_cycle",
            calibration_age_hours=d("72.000000"),
            evidence_completeness_ratio=d("0.650000"),
            prior_error_absorption_ratio=d("0.600000"),
            liquidity_cost_pressure_ratio=d("0.400000"),
            review_backlog_ratio=d("0.350000"),
        ),
        memory_signal(
            memory_signal_key="sports_liquidity_signal_gamma",
            domain_key="sports_soccer",
            calibration_age_hours=d("168.000000"),
            evidence_completeness_ratio=d("0.400000"),
            prior_error_absorption_ratio=d("0.300000"),
            liquidity_cost_pressure_ratio=d("0.800000"),
            review_backlog_ratio=d("0.900000"),
        ),
    )


def test_readiness_scoring_rolls_up_pass_watch_and_block_rows() -> None:
    module = api()

    report = build_report(*reversed(sample_signals()))
    payload = (
        module.research_strategy_decision_readiness_memory_scorecard_report_payload(
            report,
        )
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        "research-strategy-decision-readiness-memory-scorecard-report-v0"
    )
    assert report.report_status == "block"
    assert report.signal_count == d("3.000000")
    assert report.domain_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_calibration_freshness_score == d("0.500000")
    assert report.average_evidence_completeness_ratio == d("0.650000")
    assert report.average_prior_error_absorption_ratio == d("0.583333")
    assert report.average_liquidity_cost_pressure_ratio == d("0.433333")
    assert report.average_review_backlog_ratio == d("0.433333")
    assert report.average_decision_readiness_score == d("0.578333")
    assert report.max_calibration_age_hours == d("168.000000")
    assert report.max_liquidity_cost_pressure_ratio == d("0.800000")
    assert report.max_review_backlog_ratio == d("0.900000")
    assert len(report.public_payload_digest) == 64

    blocked, watched, passed = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.rank for row in report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert blocked.domain_key == "sports_soccer"
    assert blocked.calibration_freshness_score == d("0.000000")
    assert blocked.decision_readiness_score == d("0.220000")
    assert blocked.readiness_pressure == d("0.780000")
    assert blocked.reason_codes == (
        "decision_readiness_memory_block",
        "calibration_freshness_block",
        "evidence_completeness_block",
        "prior_error_absorption_block",
        "liquidity_cost_pressure_block",
        "review_backlog_block",
    )

    assert watched.domain_key == "earnings_cycle"
    assert watched.calibration_freshness_score == d("0.571429")
    assert watched.decision_readiness_score == d("0.612857")
    assert watched.readiness_pressure == d("0.387143")
    assert watched.reason_codes == (
        "decision_readiness_memory_watch",
        "calibration_freshness_watch",
        "evidence_completeness_watch",
        "prior_error_absorption_watch",
        "liquidity_cost_pressure_watch",
        "review_backlog_watch",
    )

    assert passed.domain_key == "macro_policy"
    assert passed.calibration_freshness_score == d("0.928571")
    assert passed.decision_readiness_score == d("0.902143")
    assert passed.readiness_pressure == d("0.097857")
    assert passed.reason_codes == (
        "decision_readiness_memory_pass",
        "calibration_freshness_fresh",
        "evidence_completeness_complete",
        "prior_error_absorption_absorbed",
        "liquidity_cost_pressure_low",
        "review_backlog_clear",
    )
    assert all(row.paper_only and row.report_only and row.readonly for row in report.rows)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert payload["rows"][0]["memory_signal_digest"].startswith("sha256:")
    assert payload["rows"][0]["rank"] == "1.000000"
    assert_no_decimal_objects(payload)
    assert_no_float_or_int_values(payload)


def test_memory_boundary_thresholds_watch_at_threshold_and_block_at_threshold() -> None:
    watch_boundary = memory_signal(
        memory_signal_key="freshness_watch_boundary",
        calibration_age_hours=d("72.000000"),
        evidence_completeness_ratio=d("0.850000"),
        prior_error_absorption_ratio=d("0.850000"),
        liquidity_cost_pressure_ratio=d("0.100000"),
        review_backlog_ratio=d("0.050000"),
    )
    block_boundary = memory_signal(
        memory_signal_key="freshness_block_boundary",
        domain_key="policy_rules",
        calibration_age_hours=d("168.000000"),
        evidence_completeness_ratio=d("0.850000"),
        prior_error_absorption_ratio=d("0.850000"),
        liquidity_cost_pressure_ratio=d("0.100000"),
        review_backlog_ratio=d("0.050000"),
    )
    pressure_boundary = memory_signal(
        memory_signal_key="pressure_block_boundary",
        domain_key="liquidity_pressure",
        calibration_age_hours=d("12.000000"),
        evidence_completeness_ratio=d("0.850000"),
        prior_error_absorption_ratio=d("0.850000"),
        liquidity_cost_pressure_ratio=d("0.700000"),
        review_backlog_ratio=d("0.750000"),
    )

    report = build_report(watch_boundary, block_boundary, pressure_boundary)
    rows_by_domain = {row.domain_key: row for row in report.rows}
    pressure = rows_by_domain["liquidity_pressure"]
    blocked = rows_by_domain["policy_rules"]
    watched = rows_by_domain["macro_policy"]

    assert pressure.status == "block"
    assert pressure.liquidity_cost_pressure_ratio == d("0.700000")
    assert pressure.review_backlog_ratio == d("0.750000")
    assert "liquidity_cost_pressure_block" in pressure.reason_codes
    assert "review_backlog_block" in pressure.reason_codes
    assert blocked.status == "block"
    assert blocked.calibration_age_hours == d("168.000000")
    assert blocked.calibration_freshness_score == d("0.000000")
    assert "calibration_freshness_block" in blocked.reason_codes
    assert watched.status == "watch"
    assert watched.calibration_age_hours == d("72.000000")
    assert watched.calibration_freshness_score == d("0.571429")
    assert "calibration_freshness_watch" in watched.reason_codes


def test_digest_is_deterministic_and_payload_validation_rejects_tampering() -> None:
    module = api()
    report = build_report(*sample_signals())
    permuted = build_report(*reversed(sample_signals()))

    payload = (
        module.research_strategy_decision_readiness_memory_scorecard_report_payload(
            report,
        )
    )
    permuted_payload = (
        module.research_strategy_decision_readiness_memory_scorecard_report_payload(
            permuted,
        )
    )
    assert payload == permuted_payload
    assert report.public_payload_digest == (
        module.research_strategy_decision_readiness_memory_scorecard_report_digest(
            report,
        )
    )

    digest_payload = dict(payload)
    digest_payload.pop("public_payload_digest")
    expected_digest = hashlib.sha256(
        json.dumps(
            digest_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
    assert payload["public_payload_digest"] == expected_digest

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="public_payload_digest"):
        replace(report, public_payload_digest="0" * 64)

    tampered = dict(payload)
    tampered["report_status"] = "watch"
    with pytest.raises(ValueError, match="public_payload_digest"):
        module.validate_research_strategy_decision_readiness_memory_scorecard_public_payload(
            tampered,
        )


def test_public_payload_hashes_private_memory_keys_and_rejects_leaky_payloads() -> None:
    module = api()
    raw_private_key = (
        "candidate-123 market_id=abc market_slug=raw-question "
        "source_url=https://example.invalid token wallet order trade live"
    )
    report = build_report(
        memory_signal(
            memory_signal_key=raw_private_key,
            domain_key="macro_policy",
        ),
    )

    payload = (
        module.research_strategy_decision_readiness_memory_scorecard_report_payload(
            report,
        )
    )
    encoded = json.dumps(payload, sort_keys=True).lower()

    assert raw_private_key.lower() not in encoded
    for forbidden in (
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "auth",
        "recommend",
        "sizing",
    ):
        assert forbidden not in encoded

    leaky_payload = dict(payload)
    leaky_payload["market_id"] = "raw-market"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_strategy_decision_readiness_memory_scorecard_report_payload(
            leaky_payload,
        )


def test_public_payload_validation_rejects_contract_tampering_with_fresh_digest() -> None:
    module = api()
    payload = (
        module.research_strategy_decision_readiness_memory_scorecard_report_payload(
            build_report(memory_signal()),
        )
    )

    nested_flag = redigested_payload(
        payload,
        lambda item: item["rows"][0].__setitem__("paper_only", False),
    )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.validate_research_strategy_decision_readiness_memory_scorecard_public_payload(
            nested_flag,
        )

    report_status = redigested_payload(
        payload,
        lambda item: item.__setitem__("report_status", "hold"),
    )
    with pytest.raises(ValueError, match="report_status must be one of"):
        module.validate_research_strategy_decision_readiness_memory_scorecard_public_payload(
            report_status,
        )

    row_status = redigested_payload(
        payload,
        lambda item: item["rows"][0].__setitem__("status", "hold"),
    )
    with pytest.raises(ValueError, match="status must be one of"):
        module.validate_research_strategy_decision_readiness_memory_scorecard_public_payload(
            row_status,
        )

    raw_memory_ref = redigested_payload(
        payload,
        lambda item: item["rows"][0].__setitem__(
            "memory_signal_digest",
            "not_a_digest",
        ),
    )
    with pytest.raises(ValueError, match="memory_signal_digest"):
        module.validate_research_strategy_decision_readiness_memory_scorecard_public_payload(
            raw_memory_ref,
        )


def test_custom_config_validation_changes_scoring_and_rejects_invalid_config() -> None:
    strict_config = config(
        pass_readiness_score=d("0.920000"),
        block_readiness_score=d("0.400000"),
        watch_calibration_age_hours=d("48.000000"),
        block_calibration_age_hours=d("120.000000"),
        watch_liquidity_cost_pressure_ratio=d("0.200000"),
        block_liquidity_cost_pressure_ratio=d("0.500000"),
        watch_review_backlog_ratio=d("0.200000"),
        block_review_backlog_ratio=d("0.600000"),
    )
    report = build_report(
        memory_signal(
            memory_signal_key="strict_policy_memory",
            domain_key="policy_rules",
            calibration_age_hours=d("60.000000"),
            evidence_completeness_ratio=d("0.900000"),
            prior_error_absorption_ratio=d("0.850000"),
            liquidity_cost_pressure_ratio=d("0.250000"),
            review_backlog_ratio=d("0.250000"),
        ),
        config_override=strict_config,
    )

    assert report.report_status == "watch"
    assert report.rows[0].status == "watch"
    assert "calibration_freshness_watch" in report.rows[0].reason_codes
    assert "liquidity_cost_pressure_watch" in report.rows[0].reason_codes
    assert "review_backlog_watch" in report.rows[0].reason_codes

    with pytest.raises(ValueError, match="pass_readiness_score must exceed"):
        config(pass_readiness_score=d("0.300000"), block_readiness_score=d("0.400000"))
    with pytest.raises(ValueError, match="block_calibration_age_hours must exceed"):
        config(
            watch_calibration_age_hours=d("120.000000"),
            block_calibration_age_hours=d("48.000000"),
        )
    with pytest.raises(
        ValueError,
        match="block_liquidity_cost_pressure_ratio must exceed",
    ):
        config(
            watch_liquidity_cost_pressure_ratio=d("0.600000"),
            block_liquidity_cost_pressure_ratio=d("0.500000"),
        )
    with pytest.raises(ValueError, match="block_review_backlog_ratio must exceed"):
        config(
            watch_review_backlog_ratio=d("0.600000"),
            block_review_backlog_ratio=d("0.500000"),
        )
    with pytest.raises(ValueError, match="pass_readiness_score must be exactly Decimal"):
        config(pass_readiness_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="calibration_age_hours must be exactly Decimal"):
        memory_signal(calibration_age_hours=_DecimalSubclass("12.000000"))
    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        memory_signal(
            observed_at=_DatetimeSubclass(2026, 7, 8, 14, 30, tzinfo=UTC),
        )

    module = api()
    for public_type in (
        module.ResearchStrategyDecisionReadinessMemoryScorecardConfig,
        module.ResearchStrategyDecisionReadinessMemoryScorecardInput,
        module.ResearchStrategyDecisionReadinessMemoryScorecardRow,
        module.ResearchStrategyDecisionReadinessMemoryScorecardReasonCodeCount,
        module.ResearchStrategyDecisionReadinessMemoryScorecardReport,
    ):
        assert is_dataclass(public_type)
        assert public_type.__dataclass_params__.frozen is True
        hints = get_type_hints(public_type)
        for item in fields(public_type):
            if is_numeric_public_field(item.name):
                assert hints[item.name] is Decimal

    for instance in (
        config(),
        memory_signal(),
        build_report(memory_signal()).rows[0],
        build_report(memory_signal()).reason_code_counts[0],
        build_report(memory_signal()),
    ):
        for item in fields(instance):
            if is_numeric_public_field(item.name):
                assert type(getattr(instance, item.name)) is Decimal


def test_module_scope_is_static_report_only_public_safe_without_action_surfaces() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "trading",
        "live",
        "database",
        "network",
        "requests",
        "socket",
        "postgres",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "supabase",
        "execute(",
        "open(",
        "recommend",
        "recommendation",
        "position sizing",
        "sizing",
    ):
        assert forbidden not in lowered


def assert_no_decimal_objects(value: Any) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload must not contain Decimal objects")
    if isinstance(value, dict):
        for nested in value.values():
            assert_no_decimal_objects(nested)
    elif isinstance(value, list):
        for nested in value:
            assert_no_decimal_objects(nested)


def assert_no_float_or_int_values(value: Any) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (float, int)):
        raise AssertionError(f"payload must not contain numeric JSON values: {value!r}")
    if isinstance(value, dict):
        for nested in value.values():
            assert_no_float_or_int_values(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            assert_no_float_or_int_values(nested)


def redigested_payload(
    payload: dict[str, Any],
    mutator,
) -> dict[str, Any]:
    cloned = json.loads(json.dumps(payload, sort_keys=True))
    mutator(cloned)
    digest_values = dict(cloned)
    digest_values.pop("public_payload_digest")
    cloned["public_payload_digest"] = hashlib.sha256(
        json.dumps(
            digest_values,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
    return cloned


def is_numeric_public_field(name: str) -> bool:
    return (
        name.endswith("_count")
        or name.endswith("_ratio")
        or name.endswith("_score")
        or name.endswith("_hours")
        or name == "rank"
    )
