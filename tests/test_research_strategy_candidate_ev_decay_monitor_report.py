from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api():
    return import_module(
        "polymarket_alpha_lab.research_strategy_candidate_ev_decay_monitor_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_CANDIDATE_EV_DECAY_MONITOR_REPORT_VERSION
        ),
        "evidence_half_life_seconds": d("3600.000000"),
        "minimum_decayed_ev_bps": d("20.000000"),
        "watch_decay_ratio": d("0.500000"),
        "liquidity_weakness_penalty_bps": d("100.000000"),
        "confidence_haircut_penalty_bps": d("100.000000"),
        "resolution_ambiguity_penalty_bps": d("100.000000"),
    }
    values.update(overrides)
    return module.ResearchStrategyCandidateEvDecayMonitorConfig(**values)


def observation(
    candidate_key: str,
    scope_key: str,
    observed_at: datetime,
    expected_value_bps: str,
    *,
    cost_bps: str = "0.000000",
    liquidity_score: str = "1.000000",
    confidence_haircut: str = "0.000000",
    resolution_ambiguity: str = "0.000000",
    **overrides: object,
):
    module = api()
    values = {
        "candidate_key": candidate_key,
        "scope_key": scope_key,
        "observed_at": observed_at,
        "expected_value_bps": d(expected_value_bps),
        "cost_bps": d(cost_bps),
        "liquidity_score": d(liquidity_score),
        "confidence_haircut": d(confidence_haircut),
        "resolution_ambiguity": d(resolution_ambiguity),
    }
    values.update(overrides)
    return module.ResearchStrategyCandidateEvDecayMonitorObservation(**values)


def build_report(*items, cfg=None):
    return api().build_research_strategy_candidate_ev_decay_monitor_report(
        items,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def assert_public_numbers_are_decimal(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if type(value) is bool:
            continue
        assert type(value) is not float
        assert type(value) is not int
        if isinstance(value, tuple):
            for item in value:
                if is_dataclass(item):
                    assert_public_numbers_are_decimal(item)


def test_ev_decay_monitor_scores_age_cost_liquidity_confidence_and_resolution() -> None:
    report = build_report(
        observation(
            "alpha-candidate",
            "alpha-scope",
            GENERATED_AT - timedelta(seconds=7200),
            "80.000000",
            cost_bps="5.000000",
            liquidity_score="1.000000",
            confidence_haircut="0.050000",
            resolution_ambiguity="0.050000",
        ),
        observation(
            "alpha-candidate",
            "alpha-scope",
            GENERATED_AT - timedelta(seconds=3600),
            "70.000000",
            cost_bps="8.000000",
            liquidity_score="0.700000",
            confidence_haircut="0.150000",
            resolution_ambiguity="0.100000",
        ),
        observation("beta-candidate", "beta-scope", GENERATED_AT, "80.000000"),
        observation(
            "gamma-candidate",
            "gamma-scope",
            GENERATED_AT - timedelta(seconds=60),
            "55.000000",
            cost_bps="5.000000",
            liquidity_score="1.000000",
            confidence_haircut="0.050000",
            resolution_ambiguity="0.050000",
        ),
        observation(
            "gamma-candidate",
            "gamma-scope",
            GENERATED_AT,
            "50.000000",
            cost_bps="10.000000",
            liquidity_score="0.900000",
            confidence_haircut="0.100000",
            resolution_ambiguity="0.100000",
        ),
    )

    assert report.observation_count == d("5")
    assert report.candidate_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.report_status == "block"
    assert report.average_decayed_ev_bps == d("30.666667")
    assert report.max_total_decay_bps == d("93.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_public_numbers_are_decimal(report)

    alpha = report.rows[0]
    assert alpha.candidate_ref.startswith("candidate:")
    assert alpha.scope_ref.startswith("scope:")
    assert alpha.observation_count == d("2")
    assert alpha.evidence_age_seconds == d("3600.000000")
    assert alpha.starting_expected_value_bps == d("80.000000")
    assert alpha.latest_expected_value_bps == d("70.000000")
    assert alpha.observed_ev_decay_bps == d("10.000000")
    assert alpha.evidence_age_penalty_bps == d("35.000000")
    assert alpha.cost_move_bps == d("3.000000")
    assert alpha.liquidity_weakening_bps == d("30.000000")
    assert alpha.confidence_haircut_rise_bps == d("10.000000")
    assert alpha.resolution_ambiguity_change_bps == d("5.000000")
    assert alpha.total_decay_bps == d("93.000000")
    assert alpha.decay_ratio == d("1.162500")
    assert alpha.decayed_ev_bps == d("-13.000000")
    assert alpha.status == "block"
    assert alpha.reason_codes == (
        "decayed_ev_block",
        "evidence_age_penalty",
        "cost_move_penalty",
        "liquidity_weakness_penalty",
        "confidence_haircut_penalty",
        "resolution_ambiguity_penalty",
    )

    beta = report.rows[1]
    assert beta.total_decay_bps == d("0.000000")
    assert beta.decayed_ev_bps == d("80.000000")
    assert beta.status == "pass"

    gamma = report.rows[2]
    assert gamma.total_decay_bps == d("30.000000")
    assert gamma.decay_ratio == d("0.545455")
    assert gamma.decayed_ev_bps == d("25.000000")
    assert gamma.status == "watch"
    assert set(gamma.reason_codes) == {
        "decayed_ev_watch",
        "cost_move_penalty",
        "liquidity_weakness_penalty",
        "confidence_haircut_penalty",
        "resolution_ambiguity_penalty",
    }


def test_payload_serializes_decimals_and_redacts_raw_identifiers() -> None:
    module = api()
    report = build_report(
        observation(
            "secret-alpha-candidate",
            "secret-alpha-scope",
            GENERATED_AT,
            "42.000000",
        ),
    )

    payload = module.research_strategy_candidate_ev_decay_monitor_report_payload(report)

    assert payload == report.payload
    assert payload["observation_count"] == "1"
    assert payload["rows"][0]["latest_expected_value_bps"] == "42.000000"
    assert payload["rows"][0]["candidate_ref"].startswith("candidate:")
    assert payload["rows"][0]["scope_ref"].startswith("scope:")
    assert "secret-alpha-candidate" not in repr(payload)
    assert "secret-alpha-scope" not in repr(payload)
    assert "candidate_key" not in repr(payload)
    assert "scope_key" not in repr(payload)
    assert "candidate_id" not in repr(payload)
    assert "market_id" not in repr(payload)
    assert "market_slug" not in repr(payload)
    assert "question" not in repr(payload)
    assert "url" not in repr(payload)
    assert "dsn" not in repr(payload)
    assert "table" not in repr(payload)
    assert "token" not in repr(payload)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)


def test_dataclasses_are_frozen_and_hard_flags_are_revalidated() -> None:
    module = api()
    subject = observation("alpha-candidate", "alpha-scope", GENERATED_AT, "42.000000")
    report = build_report(subject)

    assert module.MONITOR_STATUSES == ("pass", "watch", "block")
    assert is_dataclass(subject)
    assert is_dataclass(report)
    assert module.ResearchStrategyCandidateEvDecayMonitorConfig.__dataclass_params__.frozen
    assert module.ResearchStrategyCandidateEvDecayMonitorObservation.__dataclass_params__.frozen
    assert module.ResearchStrategyCandidateEvDecayMonitorRow.__dataclass_params__.frozen
    assert module.ResearchStrategyCandidateEvDecayMonitorReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.candidate_key = "other-candidate"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.report_status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        observation(
            "alpha-candidate",
            "alpha-scope",
            GENERATED_AT,
            "42.000000",
            report_only=False,
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        module.research_strategy_candidate_ev_decay_monitor_report_payload(
            {**report.payload, "paper_only": False},
        )


def test_derived_validation_digest_rejects_tampering() -> None:
    module = api()
    report = build_report(
        observation("alpha-candidate", "alpha-scope", GENERATED_AT, "42.000000"),
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report.rows[0], derived_validation_digest="0" * 64)

    tampered_row = report.payload
    tampered_row["rows"][0]["decayed_ev_bps"] = "999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_candidate_ev_decay_monitor_report_payload(tampered_row)

    tampered_report = report.payload
    tampered_report["candidate_count"] = "9"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_candidate_ev_decay_monitor_report_payload(
            tampered_report,
        )


def test_validation_requires_decimal_inputs_and_time_consistency() -> None:
    module = api()

    with pytest.raises(ValueError, match="observations must be a list or tuple"):
        module.build_research_strategy_candidate_ev_decay_monitor_report(
            object(),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="observations must contain"):
        build_report(object())
    with pytest.raises(ValueError, match="config must be"):
        module.build_research_strategy_candidate_ev_decay_monitor_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_strategy_candidate_ev_decay_monitor_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        build_report(
            observation(
                "alpha-candidate",
                "alpha-scope",
                GENERATED_AT + timedelta(seconds=1),
                "42.000000",
            ),
        )
    with pytest.raises(ValueError, match="expected_value_bps must be a Decimal"):
        module.ResearchStrategyCandidateEvDecayMonitorObservation(
            candidate_key="alpha-candidate",
            scope_key="alpha-scope",
            observed_at=GENERATED_AT,
            expected_value_bps=42.0,
            cost_bps=d("0.000000"),
            liquidity_score=d("1.000000"),
            confidence_haircut=d("0.000000"),
            resolution_ambiguity=d("0.000000"),
        )
    with pytest.raises(ValueError, match="liquidity_score must be between 0 and 1"):
        observation(
            "alpha-candidate",
            "alpha-scope",
            GENERATED_AT,
            "42.000000",
            liquidity_score="1.000001",
        )
    with pytest.raises(ValueError, match="duplicate observation"):
        build_report(
            observation("alpha-candidate", "alpha-scope", GENERATED_AT, "42.000000"),
            observation("alpha-candidate", "alpha-scope", GENERATED_AT, "41.000000"),
        )


def test_unsafe_public_payload_fields_values_and_module_exports() -> None:
    module = api()
    report = build_report(
        observation("alpha-candidate", "alpha-scope", GENERATED_AT, "42.000000"),
    )

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_CANDIDATE_EV_DECAY_MONITOR_REPORT_VERSION",
        "MONITOR_STATUSES",
        "ResearchStrategyCandidateEvDecayMonitorConfig",
        "ResearchStrategyCandidateEvDecayMonitorObservation",
        "ResearchStrategyCandidateEvDecayMonitorRow",
        "ResearchStrategyCandidateEvDecayMonitorReport",
        "build_research_strategy_candidate_ev_decay_monitor_report",
        "research_strategy_candidate_ev_decay_monitor_report_payload",
    )

    for unsafe_key in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_dsn",
        "source_table",
        "api_token",
        "wallet_ref",
        "order_ref",
        "trade_ref",
        "live_surface",
    ):
        payload = report.payload
        payload[unsafe_key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            module.research_strategy_candidate_ev_decay_monitor_report_payload(payload)

    for unsafe_value in (
        "contains candidate_id",
        "contains market_slug",
        "contains source url",
        "contains source dsn",
        "contains api token",
        "contains wallet surface",
        "contains order surface",
        "contains trade surface",
        "contains live surface",
    ):
        payload = report.payload
        payload["public_note"] = unsafe_value
        with pytest.raises(ValueError, match="unsafe public"):
            module.research_strategy_candidate_ev_decay_monitor_report_payload(payload)

    source = inspect.getsource(module)
    tree = ast.parse(source)
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}

    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
