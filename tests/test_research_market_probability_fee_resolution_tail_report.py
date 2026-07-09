from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from inspect import getsource
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_market_probability_fee_resolution_tail_report"
)


def _api() -> Any:
    return importlib.import_module(MODULE_NAME)


def _observation(**overrides: object) -> Any:
    api = _api()
    values: dict[str, object] = {
        "candidate_id": "raw-candidate-123",
        "market_id": "0x1234abcd",
        "market_slug": "will-fed-cut-rates-in-july",
        "market_question": "Will the Fed cut rates in July?",
        "source_url": "https://example.test/private/source",
        "source_text": "private source text with table_name and token",
        "observed_at": datetime(2026, 7, 9, 12, 0, tzinfo=UTC),
        "probability": Decimal("0.990000"),
        "fee_rate": Decimal("0.090000"),
        "resolution_uncertainty": Decimal("0.410000"),
    }
    values.update(overrides)
    return api.MarketProbabilityFeeResolutionTailObservation(**values)


def _canonical_digest(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("validation_digest")
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"sha256:{sha256(encoded.encode('utf-8')).hexdigest()}"


def _walk_public_values(value: object) -> list[object]:
    if isinstance(value, dict):
        nested: list[object] = []
        for key, item in value.items():
            nested.append(key)
            nested.extend(_walk_public_values(item))
        return nested
    if isinstance(value, (list, tuple)):
        nested = []
        for item in value:
            nested.extend(_walk_public_values(item))
        return nested
    return [value]


def test_public_payload_is_deterministic_redacted_and_digest_validated() -> None:
    api = _api()
    generated_at = datetime(2026, 7, 9, 13, 0, tzinfo=UTC)
    report = api.build_research_market_probability_fee_resolution_tail_report(
        [_observation()],
        generated_at=generated_at,
    )

    payload = api.research_market_probability_fee_resolution_tail_report_payload(report)
    json_payload = api.research_market_probability_fee_resolution_tail_report_payload_json(
        report,
    )
    assert (
        json_payload
        == api.research_market_probability_fee_resolution_tail_report_payload_json(report)
    )

    plain_payload = json.loads(json_payload)
    assert plain_payload == payload
    assert plain_payload["validation_digest"] == _canonical_digest(plain_payload)
    assert (
        api.validate_research_market_probability_fee_resolution_tail_report_payload(
            plain_payload,
        )
        is True
    )

    encoded = json_payload.lower()
    leaked_fragments = (
        "raw-candidate-123",
        "0x1234abcd",
        "will-fed-cut-rates-in-july",
        "will the fed cut rates",
        "https://example.test",
        "private source text",
        "table_name",
        "token",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
    )
    for fragment in leaked_fragments:
        assert fragment not in encoded

    row = plain_payload["rows"][0]
    assert row["research_digest"].startswith("sha256:")
    assert row["status"] == "block"
    assert plain_payload["overall_status"] == "block"


def test_report_dataclasses_are_frozen_and_decimal_only() -> None:
    api = _api()
    report = api.build_research_market_probability_fee_resolution_tail_report(
        [
            _observation(
                candidate_id="candidate-pass",
                market_id="market-pass",
                market_slug="pass-market",
                market_question="Pass market?",
                source_url="https://example.test/pass",
                source_text="pass source",
                probability=Decimal("0.500000"),
                fee_rate=Decimal("0.010000"),
                resolution_uncertainty=Decimal("0.020000"),
            ),
            _observation(
                candidate_id="candidate-watch",
                market_id="market-watch",
                market_slug="watch-market",
                market_question="Watch market?",
                source_url="https://example.test/watch",
                source_text="watch source",
                probability=Decimal("0.900000"),
                fee_rate=Decimal("0.030000"),
                resolution_uncertainty=Decimal("0.100000"),
            ),
        ],
        generated_at=datetime(2026, 7, 9, 13, 0, tzinfo=UTC),
    )

    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])
    with pytest.raises(FrozenInstanceError):
        report.overall_status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]

    decimal_fields = (
        "candidate_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_tail_score",
    )
    for field_name in decimal_fields:
        assert type(getattr(report, field_name)) is Decimal
    for row in report.rows:
        assert type(row.probability) is Decimal
        assert type(row.fee_rate) is Decimal
        assert type(row.resolution_uncertainty) is Decimal
        assert type(row.probability_tail_score) is Decimal
        assert type(row.tail_score) is Decimal

    payload = api.research_market_probability_fee_resolution_tail_report_payload(report)
    for value in _walk_public_values(payload):
        assert not isinstance(value, float)
        assert not (isinstance(value, int) and not isinstance(value, bool))


def test_status_domain_and_payload_immutability_are_enforced() -> None:
    api = _api()
    report = api.build_research_market_probability_fee_resolution_tail_report(
        [_observation()],
        generated_at=datetime(2026, 7, 9, 13, 0, tzinfo=UTC),
    )
    statuses = {row.status for row in report.rows} | {report.overall_status}
    assert statuses <= {"pass", "watch", "block"}

    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="blocked")

    payload = api.research_market_probability_fee_resolution_tail_report_payload(report)
    with pytest.raises(TypeError, match="immutable"):
        payload["overall_status"] = "pass"
    with pytest.raises(TypeError, match="immutable"):
        payload["rows"].append({"status": "pass"})

    tampered = json.loads(
        api.research_market_probability_fee_resolution_tail_report_payload_json(report),
    )
    tampered["overall_status"] = "pass"
    assert (
        api.validate_research_market_probability_fee_resolution_tail_report_payload(
            tampered,
        )
        is False
    )
    tampered["validation_digest"] = _canonical_digest(tampered)
    tampered["rows"][0]["status"] = "blocked"
    tampered["validation_digest"] = _canonical_digest(tampered)
    assert (
        api.validate_research_market_probability_fee_resolution_tail_report_payload(
            tampered,
        )
        is False
    )


def test_hard_report_only_flags_and_runtime_surface_are_constrained() -> None:
    api = _api()
    report = api.build_research_market_probability_fee_resolution_tail_report(
        [_observation()],
        generated_at=datetime(2026, 7, 9, 13, 0, tzinfo=UTC),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in report.rows)

    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report.rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report.rows[0], readonly=False)

    source = getsource(api)
    forbidden_imports = (
        "import psycopg",
        "import requests",
        "import httpx",
        "import socket",
        "import sqlite3",
        "import sqlalchemy",
        "import web3",
        "import ccxt",
        "import subprocess",
    )
    for forbidden in forbidden_imports:
        assert forbidden not in source
