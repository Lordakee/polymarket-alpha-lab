from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_event_breaking_news_sensitivity_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_breaking_news_sensitivity_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def sensitivity_input(**overrides: object) -> Any:
    module = api()
    values = {
        "event_ref": "raw-candidate-alpha-market-slug",
        "observed_at": GENERATED_AT - timedelta(minutes=10),
        "update_count_1h": d("1.000000"),
        "authoritative_source_count": d("4.000000"),
        "total_source_count": d("4.000000"),
        "contradiction_count": d("0.000000"),
        "claim_count": d("4.000000"),
        "probability_movement": d("0.020000"),
        "liquidity_reliability": d("0.850000"),
        "hours_to_resolution": d("72.000000"),
    }
    values.update(overrides)
    return module.ResearchEventBreakingNewsSensitivityInput(**values)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_EVENT_BREAKING_NEWS_SENSITIVITY_CONFIG_VERSION
        ),
        "pass_update_count_1h_ceiling": d("2.000000"),
        "watch_update_count_1h_ceiling": d("4.000000"),
        "pass_authority_mix_floor": d("0.750000"),
        "watch_authority_mix_floor": d("0.500000"),
        "pass_contradiction_pressure_ceiling": d("0.100000"),
        "watch_contradiction_pressure_ceiling": d("0.350000"),
        "pass_probability_movement_ceiling": d("0.050000"),
        "watch_probability_movement_ceiling": d("0.150000"),
        "pass_liquidity_reliability_floor": d("0.700000"),
        "watch_liquidity_reliability_floor": d("0.400000"),
        "pass_hours_to_resolution_floor": d("48.000000"),
        "watch_hours_to_resolution_floor": d("12.000000"),
    }
    values.update(overrides)
    return module.ResearchEventBreakingNewsSensitivityConfig(**values)


def report(*inputs: object, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_research_event_breaking_news_sensitivity_report(
        inputs,
        config=config(),
        generated_at=generated_at,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(walk_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_values(item))
        return tuple(values)
    return (value,)


def assert_public_payload_is_safe(value: Any) -> None:
    forbidden = (
        "candidate",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "raw-candidate",
        "market-slug",
        "://",
        "api_key",
        "apikey",
        "authorization",
        "bearer",
        "credential",
        "private_key",
        "secret",
        "session",
        "sizing",
        "www.",
    )
    payload_text = json.dumps(value, sort_keys=True).lower()
    for term in forbidden:
        assert term not in payload_text


def test_report_triages_breaking_news_sensitivity_across_six_signals() -> None:
    summary = report(
        sensitivity_input(
            event_ref="raw-candidate-block-market-slug",
            update_count_1h=d("6.000000"),
            authoritative_source_count=d("1.000000"),
            total_source_count=d("4.000000"),
            contradiction_count=d("3.000000"),
            claim_count=d("6.000000"),
            probability_movement=d("0.220000"),
            liquidity_reliability=d("0.250000"),
            hours_to_resolution=d("4.000000"),
        ),
        sensitivity_input(
            event_ref="raw-candidate-watch-market-slug",
            update_count_1h=d("3.000000"),
            authoritative_source_count=d("2.000000"),
            total_source_count=d("3.000000"),
            contradiction_count=d("1.000000"),
            claim_count=d("5.000000"),
            probability_movement=d("0.100000"),
            liquidity_reliability=d("0.550000"),
            hours_to_resolution=d("24.000000"),
        ),
        sensitivity_input(event_ref="raw-candidate-pass-market-slug"),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.__dataclass_params__.frozen is True
    assert summary.generated_at == GENERATED_AT
    assert summary.input_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_sensitivity_score == d("0.364259")
    assert summary.max_sensitivity_score == d("0.689444")
    assert summary.mean_update_velocity_score == d("0.555556")
    assert summary.mean_authority_mix_score == d("0.638889")
    assert summary.mean_contradiction_pressure_ratio == d("0.233333")
    assert summary.mean_liquidity_reliability_score == d("0.550000")
    assert summary.max_resolution_proximity_score == d("0.916667")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "update_velocity_review",
        "source_authority_mix_review",
        "contradiction_pressure_review",
        "probability_movement_review",
        "liquidity_reliability_review",
        "resolution_proximity_review",
        "breaking_news_sensitivity_report_block",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.derived_validation_digest) == 64

    blocked, watched, passed = summary.rows
    assert blocked.update_velocity_score == d("1.000000")
    assert blocked.source_authority_mix_score == d("0.250000")
    assert blocked.contradiction_pressure_ratio == d("0.500000")
    assert blocked.probability_movement == d("0.220000")
    assert blocked.liquidity_reliability_score == d("0.250000")
    assert blocked.resolution_proximity_score == d("0.916667")
    assert blocked.breaking_news_sensitivity_score == d("0.689444")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "update_velocity_block",
        "source_authority_mix_block",
        "contradiction_pressure_block",
        "probability_movement_block",
        "liquidity_reliability_block",
        "resolution_proximity_block",
    )

    assert watched.breaking_news_sensitivity_score == d("0.347222")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "update_velocity_watch",
        "source_authority_mix_watch",
        "contradiction_pressure_watch",
        "probability_movement_watch",
        "liquidity_reliability_watch",
        "resolution_proximity_watch",
    )

    assert passed.breaking_news_sensitivity_score == d("0.056111")
    assert passed.status == "pass"
    assert passed.reason_codes == ("breaking_news_sensitivity_pass",)


def test_empty_report_blocks_for_missing_event_inputs() -> None:
    module = api()
    summary = report()

    assert module.RESEARCH_EVENT_BREAKING_NEWS_SENSITIVITY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert summary.status == "block"
    assert summary.input_count == d("0.000000")
    assert summary.reason_codes == ("breaking_news_sensitivity_report_empty",)
    assert summary.reason_code_counts == (
        module.ResearchEventBreakingNewsSensitivityReasonCodeCount(
            reason_code="breaking_news_sensitivity_report_empty",
            count=d("1.000000"),
            input_ratio=d("0.000000"),
        ),
    )
    assert summary.rows == ()


def test_public_payload_is_deterministic_digest_guarded_and_redacted() -> None:
    module = api()
    generated_at = datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    first_payload = module.research_event_breaking_news_sensitivity_report_payload(
        report(sensitivity_input(), generated_at=generated_at),
    )
    second_payload = module.research_event_breaking_news_sensitivity_report_payload(
        report(sensitivity_input(), generated_at=generated_at),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["input_count"] == "1.000000"
    assert first_payload["rows"][0]["row_number"] == "1.000000"
    assert "event_ref" not in first_payload["rows"][0]
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(type(item) in (int, float, Decimal) for item in walk_values(first_payload))
    assert_public_payload_is_safe(first_payload)

    unsigned = dict(first_payload)
    unsigned.pop("derived_validation_digest")
    expected_digest = sha256(
        json.dumps(
            unsigned,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
    assert first_payload["derived_validation_digest"] == expected_digest
    assert module.validate_research_event_breaking_news_sensitivity_public_payload(
        first_payload,
    )

    tampered = json.loads(json.dumps(first_payload))
    tampered["rows"][0]["breaking_news_sensitivity_score"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_event_breaking_news_sensitivity_report_payload(tampered)

    unexpected_metadata = json.loads(json.dumps(first_payload))
    unexpected_metadata["notes"] = "paper report only"
    unsigned_unexpected_metadata = dict(unexpected_metadata)
    unsigned_unexpected_metadata.pop("derived_validation_digest")
    unexpected_metadata["derived_validation_digest"] = sha256(
        json.dumps(
            unsigned_unexpected_metadata,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
    assert not module.validate_research_event_breaking_news_sensitivity_public_payload(
        unexpected_metadata,
    )
    with pytest.raises(ValueError, match="supported public keys"):
        module.research_event_breaking_news_sensitivity_report_payload(
            unexpected_metadata,
        )


def test_frozen_decimal_only_flags_and_no_external_surfaces() -> None:
    module = api()
    summary = report(sensitivity_input())

    with pytest.raises(FrozenInstanceError):
        summary.status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="Decimal"):
        sensitivity_input(update_count_1h=1)

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(summary.rows[0], readonly=False)

    unsafe_terms = (
        "candidate_id",
        "api_key",
        "apikey",
        "authorization",
        "bearer",
        "credential",
        "market_id",
        "market_slug",
        "private_key",
        "question",
        "secret",
        "session",
        "sizing",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    for public_name in module.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)
    for cls_name in (
        "ResearchEventBreakingNewsSensitivityConfig",
        "ResearchEventBreakingNewsSensitivityInput",
        "ResearchEventBreakingNewsSensitivityReasonCodeCount",
        "ResearchEventBreakingNewsSensitivityRow",
        "ResearchEventBreakingNewsSensitivityReport",
    ):
        for field in fields(getattr(module, cls_name)):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_terms)

    tree = ast.parse(MODULE_PATH.read_text())
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
            "web3",
            "ccxt",
        },
    )
