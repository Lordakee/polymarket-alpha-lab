from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
import hashlib
import inspect
import json
from typing import Any

import pytest

import polymarket_alpha_lab.probability_event_forecast_model_disagreement_report as api
from polymarket_alpha_lab.probability_event_forecast_model_disagreement_report import (
    ProbabilityEventForecastModelDisagreementReport,
    build_probability_event_forecast_model_disagreement_report,
    probability_event_forecast_model_disagreement_report_digest,
    probability_event_forecast_model_disagreement_report_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def build_report(**overrides: object) -> ProbabilityEventForecastModelDisagreementReport:
    values = {
        "naive_probability": d("0.520000"),
        "book_imbalance_probability": d("0.550000"),
        "llm_probability": d("0.590000"),
        "specialist_probability": d("0.610000"),
        "max_allowed_spread_probability": d("0.090000"),
    }
    values.update(overrides)
    return build_probability_event_forecast_model_disagreement_report(**values)


def walk_payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(walk_payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_payload_values(item))
        return tuple(values)
    return (value,)


def resign_public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    signed = json.loads(json.dumps(payload))
    signed.pop("payload_digest", None)
    signed["payload_digest"] = hashlib.sha256(
        json.dumps(
            signed,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
    return signed


def test_builds_pass_report_when_model_probabilities_are_within_allowed_spread() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert type(report) is ProbabilityEventForecastModelDisagreementReport
    assert report.disagreement_status == "pass"
    assert report.probability_range == d("0.090000")
    assert report.manual_next_step == "continue_readonly_monitoring"
    assert report.reason_codes == ("forecast_model_disagreement_pass",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.payload_digest) == 64


def test_builds_attention_report_at_moderate_spread_and_blocker_report_above_double_spread() -> None:
    attention = build_report(
        naive_probability=d("0.430000"),
        book_imbalance_probability=d("0.520000"),
        llm_probability=d("0.590000"),
        specialist_probability=d("0.610000"),
        max_allowed_spread_probability=d("0.100000"),
    )
    blocker = build_report(
        naive_probability=d("0.300000"),
        book_imbalance_probability=d("0.500000"),
        llm_probability=d("0.610000"),
        specialist_probability=d("0.640000"),
        max_allowed_spread_probability=d("0.100000"),
    )

    assert attention.disagreement_status == "attention"
    assert attention.probability_range == d("0.180000")
    assert attention.manual_next_step == "manual_review_model_spread"
    assert attention.reason_codes == (
        "forecast_model_disagreement_attention",
        "spread_exceeds_allowed_probability",
    )

    assert blocker.disagreement_status == "blocker"
    assert blocker.probability_range == d("0.340000")
    assert blocker.manual_next_step == "block_and_escalate_model_disagreement"
    assert blocker.reason_codes == (
        "forecast_model_disagreement_blocker",
        "spread_exceeds_double_allowed_probability",
    )


def test_public_payload_is_decimal_string_only_deterministic_and_digest_checked() -> None:
    report = build_report()
    first_payload = report.public_payload
    second_payload = probability_event_forecast_model_disagreement_report_payload(
        build_report(),
    )
    digest = probability_event_forecast_model_disagreement_report_digest(report)

    assert first_payload == second_payload
    assert first_payload == {
        "naive_probability": "0.520000",
        "book_imbalance_probability": "0.550000",
        "llm_probability": "0.590000",
        "specialist_probability": "0.610000",
        "max_allowed_spread_probability": "0.090000",
        "disagreement_status": "pass",
        "probability_range": "0.090000",
        "reason_codes": ["forecast_model_disagreement_pass"],
        "manual_next_step": "continue_readonly_monitoring",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "payload_digest": first_payload["payload_digest"],
    }
    assert digest == {
        "disagreement_status": "pass",
        "probability_range": "0.090000",
        "reason_codes": ["forecast_model_disagreement_pass"],
        "manual_next_step": "continue_readonly_monitoring",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "payload_digest": first_payload["payload_digest"],
    }
    assert not any(
        type(value) in (int, float, Decimal)
        for value in walk_payload_values(first_payload)
    )

    unsigned = dict(first_payload)
    unsigned.pop("payload_digest")
    expected_digest = hashlib.sha256(
        json.dumps(
            unsigned,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
    assert first_payload["payload_digest"] == expected_digest

    tampered = json.loads(json.dumps(first_payload))
    tampered["probability_range"] = "0.999999"
    with pytest.raises(ValueError, match="payload_digest"):
        probability_event_forecast_model_disagreement_report_payload(tampered)


def test_dataclass_is_frozen_decimal_only_and_hard_flags_are_enforced() -> None:
    report = build_report()

    with pytest.raises(FrozenInstanceError):
        report.disagreement_status = "attention"  # type: ignore[misc]

    with pytest.raises(ValueError, match="Decimal"):
        build_report(naive_probability=0.52)

    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    with pytest.raises(ValueError, match="payload_digest"):
        replace(report, probability_range=d("0.010000"))


def test_payload_validator_rejects_actionable_or_unsafe_surfaces_after_resigning() -> None:
    payload = build_report().public_payload

    with pytest.raises(ValueError, match="disagreement_status"):
        probability_event_forecast_model_disagreement_report_payload(
            resign_public_payload({**payload, "disagreement_status": "ready"}),
        )

    with pytest.raises(ValueError, match="manual_next_step"):
        probability_event_forecast_model_disagreement_report_payload(
            resign_public_payload({**payload, "manual_next_step": "execute_order"}),
        )

    with pytest.raises(ValueError, match="public"):
        probability_event_forecast_model_disagreement_report_payload(
            resign_public_payload({**payload, "wallet": "0xabc"}),
        )


def test_public_api_is_narrow_readonly_report_only_and_has_no_io_execution_surface() -> None:
    unsafe_terms = (
        "auth",
        "candidate",
        "condition_id",
        "database",
        "dsn",
        "execute",
        "execution",
        "key",
        "live",
        "market_id",
        "market_slug",
        "network",
        "order",
        "persist",
        "private",
        "secret",
        "signature",
        "signing",
        "source_url",
        "table",
        "token",
        "trade",
        "wallet",
    )
    assert set(api.__all__) == {
        "PROBABILITY_EVENT_FORECAST_MODEL_DISAGREEMENT_STATUSES",
        "ProbabilityEventForecastModelDisagreementReport",
        "build_probability_event_forecast_model_disagreement_report",
        "probability_event_forecast_model_disagreement_report_digest",
        "probability_event_forecast_model_disagreement_report_payload",
    }
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for field in fields(ProbabilityEventForecastModelDisagreementReport):
        lowered = field.name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    tree = ast.parse(inspect.getsource(api))
    imported_modules = {
        node.module.split(".")[0] if isinstance(node, ast.ImportFrom) else alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in (node.names if isinstance(node, ast.Import) else [ast.alias(node.module or "")])
    }
    assert imported_modules.isdisjoint(
        {
            "requests",
            "httpx",
            "urllib",
            "socket",
            "sqlite3",
            "sqlalchemy",
            "psycopg",
            "supabase",
            "web3",
            "ccxt",
            "subprocess",
            "pathlib",
            "open",
        },
    )
