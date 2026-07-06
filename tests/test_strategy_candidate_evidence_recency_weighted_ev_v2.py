from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def api():
    return import_module(
        "polymarket_alpha_lab.strategy_candidate_evidence_recency_weighted_ev_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_CANDIDATE_EVIDENCE_RECENCY_WEIGHTED_EV_V2_VERSION
        ),
        "recency_half_life_seconds": d("3600"),
        "stale_evidence_age_seconds": d("3600"),
        "official_evidence_boost": d("0.200000"),
        "stale_evidence_penalty": d("0.020000"),
        "minimum_candidate_score": d("0.050000"),
    }
    values.update(overrides)
    return module.StrategyCandidateEvidenceRecencyWeightedEvV2Config(**values)


def observation(
    candidate_key: str,
    evidence_key: str,
    observed_at: datetime,
    estimated_probability: str,
    market_probability: str = "0.500000",
    *,
    evidence_kind: str = "analysis",
    confidence: str = "1.000000",
    relevance: str = "1.000000",
    **overrides: object,
):
    module = api()
    values = {
        "candidate_key": candidate_key,
        "evidence_key": evidence_key,
        "evidence_kind": evidence_kind,
        "observed_at": observed_at,
        "estimated_probability": d(estimated_probability),
        "market_probability": d(market_probability),
        "confidence": d(confidence),
        "relevance": d(relevance),
    }
    values.update(overrides)
    return module.StrategyCandidateEvidenceRecencyWeightedEvV2Observation(**values)


def build_report(*items, cfg=None):
    return api().build_strategy_candidate_evidence_recency_weighted_ev_v2(
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


def test_recency_weighted_ev_scores_candidates_and_penalizes_stale_evidence() -> None:
    report = build_report(
        observation(
            "alpha-candidate",
            "alpha-official",
            GENERATED_AT,
            "0.600000",
            evidence_kind="official",
        ),
        observation(
            "alpha-candidate",
            "alpha-stale",
            GENERATED_AT - timedelta(seconds=7200),
            "0.600000",
        ),
        observation(
            "beta-candidate",
            "beta-stale",
            GENERATED_AT - timedelta(seconds=7200),
            "0.550000",
        ),
    )

    assert report.observation_count == d("3")
    assert report.candidate_count == d("2")
    assert report.candidate_status == "watch"
    assert report.candidate_candidate_count == d("1")
    assert report.watch_candidate_count == d("0")
    assert report.blocked_candidate_count == d("1")
    assert report.reason_codes == (
        "candidate_clear",
        "candidate_blocked",
        "official_evidence_boost_applied",
        "stale_evidence_penalty_applied",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_public_numbers_are_decimal(report)

    alpha = report.rows[0]
    assert alpha.candidate_ref.startswith("candidate:")
    assert alpha.evidence_count == d("2")
    assert alpha.latest_evidence_at == GENERATED_AT
    assert alpha.newest_evidence_age_seconds == d("0.000000")
    assert alpha.total_raw_expected_value == d("0.200000")
    assert alpha.recency_weighted_expected_value == d("0.153333")
    assert alpha.official_evidence_boost == d("0.020000")
    assert alpha.stale_evidence_penalty == d("0.020000")
    assert alpha.recency_weighted_ev_score == d("0.153333")
    assert alpha.candidate_status == "candidate"
    assert alpha.reason_codes == (
        "candidate_clear",
        "official_evidence_boost_applied",
        "stale_evidence_penalty_applied",
    )
    assert alpha.derived_validation_digest

    beta = report.rows[1]
    assert beta.evidence_count == d("1")
    assert beta.total_raw_expected_value == d("0.050000")
    assert beta.recency_weighted_expected_value == d("0.016667")
    assert beta.official_evidence_boost == d("0.000000")
    assert beta.stale_evidence_penalty == d("0.020000")
    assert beta.recency_weighted_ev_score == d("-0.003333")
    assert beta.candidate_status == "blocked"
    assert beta.reason_codes == (
        "candidate_blocked",
        "stale_evidence_penalty_applied",
    )


def test_recent_official_evidence_boosts_score_without_stale_penalty() -> None:
    report = build_report(
        observation(
            "official-candidate",
            "fresh-official",
            GENERATED_AT,
            "0.600000",
            evidence_kind="official",
        ),
    )

    row = report.rows[0]
    assert row.total_raw_expected_value == d("0.100000")
    assert row.recency_weighted_expected_value == d("0.120000")
    assert row.official_evidence_boost == d("0.020000")
    assert row.stale_evidence_penalty == d("0.000000")
    assert row.recency_weighted_ev_score == d("0.120000")
    assert row.candidate_status == "candidate"
    assert row.reason_codes == (
        "candidate_clear",
        "official_evidence_boost_applied",
    )


def test_payload_serializes_decimals_as_strings_and_redacts_raw_evidence() -> None:
    module = api()
    report = build_report(
        observation(
            "secret-alpha-candidate",
            "secret-alpha-evidence",
            GENERATED_AT,
            "0.600000",
            evidence_kind="official",
        ),
    )

    payload = module.strategy_candidate_evidence_recency_weighted_ev_v2_payload(report)

    assert payload == report.payload
    assert payload["observation_count"] == "1"
    assert payload["rows"][0]["recency_weighted_ev_score"] == "0.120000"
    assert payload["rows"][0]["official_evidence_boost"] == "0.020000"
    assert payload["rows"][0]["candidate_ref"].startswith("candidate:")
    assert payload["rows"][0]["evidence_refs"][0].startswith("evidence:")
    assert "secret-alpha-candidate" not in repr(payload)
    assert "secret-alpha-evidence" not in repr(payload)
    assert "candidate_key" not in repr(payload)
    assert "evidence_key" not in repr(payload)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)


def test_dataclasses_are_frozen_and_hard_flags_are_revalidated() -> None:
    module = api()
    subject = observation(
        "alpha-candidate",
        "alpha-evidence",
        GENERATED_AT,
        "0.600000",
    )
    report = build_report(subject)

    assert is_dataclass(subject)
    assert is_dataclass(report)
    assert (
        module.StrategyCandidateEvidenceRecencyWeightedEvV2Config
        .__dataclass_params__
        .frozen
    )
    assert (
        module.StrategyCandidateEvidenceRecencyWeightedEvV2Observation
        .__dataclass_params__
        .frozen
    )
    assert (
        module.StrategyCandidateEvidenceRecencyWeightedEvV2Row
        .__dataclass_params__
        .frozen
    )
    assert (
        module.StrategyCandidateEvidenceRecencyWeightedEvV2Report
        .__dataclass_params__
        .frozen
    )

    with pytest.raises(FrozenInstanceError):
        subject.candidate_key = "other-candidate"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.candidate_status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        observation(
            "alpha-candidate",
            "alpha-evidence",
            GENERATED_AT,
            "0.600000",
            report_only=False,
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        module.strategy_candidate_evidence_recency_weighted_ev_v2_payload(
            {**report.payload, "paper_only": False},
        )


def test_derived_validation_digest_rejects_tampered_public_payloads() -> None:
    module = api()
    report = build_report(
        observation(
            "alpha-candidate",
            "alpha-evidence",
            GENERATED_AT,
            "0.600000",
        ),
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report.rows[0], derived_validation_digest="not-the-derived-digest")

    tampered = report.payload
    tampered["rows"][0]["recency_weighted_ev_score"] = "0.999000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_candidate_evidence_recency_weighted_ev_v2_payload(tampered)

    tampered_report = report.payload
    tampered_report["candidate_count"] = "9"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_candidate_evidence_recency_weighted_ev_v2_payload(
            tampered_report,
        )


def test_unsafe_public_keys_and_values_are_rejected() -> None:
    module = api()
    report = build_report(
        observation(
            "alpha-candidate",
            "alpha-evidence",
            GENERATED_AT,
            "0.600000",
        ),
    )

    with pytest.raises(ValueError, match="unsafe public value"):
        observation(
            "alpha-wallet-candidate",
            "alpha-evidence",
            GENERATED_AT,
            "0.600000",
        )

    for unsafe_key in (
        "live_mode",
        "auth_token",
        "wallet_id",
        "order_id",
        "network_url",
        "database_uri",
        "persist_path",
        "signing_key",
        "mutation_name",
        "buy_action",
        "sell_action",
        "trade_action",
    ):
        payload = report.payload
        payload[unsafe_key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public field"):
            module.strategy_candidate_evidence_recency_weighted_ev_v2_payload(payload)

    for unsafe_value in (
        "enable live mode",
        "auth token here",
        "wallet controlled",
        "place order",
        "network endpoint",
        "database connection",
        "persist this",
        "signing secret",
        "mutation route",
        "buy this",
        "sell this",
        "trade this",
    ):
        payload = report.payload
        payload["public_note"] = unsafe_value
        with pytest.raises(ValueError, match="unsafe public value"):
            module.strategy_candidate_evidence_recency_weighted_ev_v2_payload(payload)


def test_input_validation_is_decimal_only_timezone_aware_and_consistent() -> None:
    module = api()

    with pytest.raises(ValueError, match="observations must be a list or tuple"):
        module.build_strategy_candidate_evidence_recency_weighted_ev_v2(
            object(),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="observations must contain"):
        build_report(object())
    with pytest.raises(ValueError, match="config must be"):
        module.build_strategy_candidate_evidence_recency_weighted_ev_v2(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_candidate_evidence_recency_weighted_ev_v2(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        build_report(
            observation(
                "alpha-candidate",
                "alpha-future",
                GENERATED_AT + timedelta(seconds=1),
                "0.600000",
            ),
        )
    with pytest.raises(ValueError, match="estimated_probability must be a Decimal"):
        module.StrategyCandidateEvidenceRecencyWeightedEvV2Observation(
            candidate_key="alpha-candidate",
            evidence_key="alpha-evidence",
            evidence_kind="analysis",
            observed_at=GENERATED_AT,
            estimated_probability=0.6,
            market_probability=d("0.500000"),
            confidence=d("1.000000"),
            relevance=d("1.000000"),
        )
    with pytest.raises(ValueError, match="market_probability must be between 0 and 1"):
        observation(
            "alpha-candidate",
            "alpha-evidence",
            GENERATED_AT,
            "0.600000",
            market_probability=d("1.000001"),
        )
    with pytest.raises(ValueError, match="confidence must be between 0 and 1"):
        observation(
            "alpha-candidate",
            "alpha-evidence",
            GENERATED_AT,
            "0.600000",
            confidence="1.000001",
        )
    with pytest.raises(ValueError, match="evidence_kind must be one of"):
        observation(
            "alpha-candidate",
            "alpha-evidence",
            GENERATED_AT,
            "0.600000",
            evidence_kind="rumor",
        )


def test_module_exports_are_local_and_has_no_unsafe_execution_surface() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_STRATEGY_CANDIDATE_EVIDENCE_RECENCY_WEIGHTED_EV_V2_VERSION",
        "EVIDENCE_KINDS",
        "CANDIDATE_STATUSES",
        "StrategyCandidateEvidenceRecencyWeightedEvV2Config",
        "StrategyCandidateEvidenceRecencyWeightedEvV2Observation",
        "StrategyCandidateEvidenceRecencyWeightedEvV2Row",
        "StrategyCandidateEvidenceRecencyWeightedEvV2Report",
        "build_strategy_candidate_evidence_recency_weighted_ev_v2",
        "strategy_candidate_evidence_recency_weighted_ev_v2_payload",
    )

    source = inspect.getsource(module)
    lowered = source.lower()
    for unsafe_public_term in (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    ):
        assert unsafe_public_term not in lowered
        assert all(unsafe_public_term not in name.lower() for name in module.__all__)

    tree = ast.parse(source)
    imported_modules: list[str] = []
    public_names = set(module.__all__)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            if node.name in public_names:
                assert all(term not in node.name.lower() for term in ("buy", "sell"))

    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "typing",
    }
