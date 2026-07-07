from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_probability_move_source_gap_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def stamp() -> datetime:
    return datetime(2026, 7, 7, 9, 30, tzinfo=UTC)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_PACKET_PROBABILITY_MOVE_SOURCE_GAP_V2_CONFIG_VERSION
        ),
        "medium_move_threshold": d("0.050000"),
        "large_move_threshold": d("0.100000"),
        "required_source_count": d("2"),
        "fresh_source_max_age_seconds": d("3600.000000"),
        "stale_source_age_seconds": d("7200.000000"),
        "elevated_contradiction_threshold": d("0.250000"),
        "severe_contradiction_threshold": d("0.750000"),
        "thin_liquidity_depth_usd": d("100.000000"),
        "deep_liquidity_depth_usd": d("1000.000000"),
    }
    values.update(overrides)
    return module.ResearchPacketProbabilityMoveSourceGapV2Config(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "packet_id": "packet-alpha",
        "market_id": "market-alpha",
        "event_title": "Alpha probability jump",
        "previous_probability": d("0.400000"),
        "current_probability": d("0.530000"),
        "source_count": d("1"),
        "official_source_count": d("0"),
        "latest_source_age_seconds": d("10800.000000"),
        "contradiction_severity": d("0.800000"),
        "liquidity_depth_usd": d("75.000000"),
    }
    values.update(overrides)
    return module.ResearchPacketProbabilityMoveSourceGapV2Candidate(**values)


def build_report(*rows: object, **config_overrides: object):
    module = api()
    source_rows = rows or (
        candidate(),
        candidate(
            packet_id="packet-beta",
            market_id="market-beta",
            event_title="Beta source-backed drift",
            previous_probability=d("0.550000"),
            current_probability=d("0.590000"),
            source_count=d("3"),
            official_source_count=d("1"),
            latest_source_age_seconds=d("900.000000"),
            contradiction_severity=d("0.000000"),
            liquidity_depth_usd=d("1500.000000"),
        ),
        candidate(
            packet_id="packet-gamma",
            market_id="market-gamma",
            event_title="Gamma partial source move",
            previous_probability=d("0.720000"),
            current_probability=d("0.650000"),
            source_count=d("1"),
            official_source_count=d("1"),
            latest_source_age_seconds=d("5000.000000"),
            contradiction_severity=d("0.300000"),
            liquidity_depth_usd=d("400.000000"),
        ),
    )
    return module.build_research_packet_probability_move_source_gap_v2(
        source_rows,
        config=config(**config_overrides),
        generated_at=stamp(),
    )


def walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        values: list[object] = []
        for key, item in value.items():
            values.append(key)
            values.extend(walk(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk(item))
        return tuple(values)
    return (value,)


def unsafe_terms() -> tuple[str, ...]:
    return (
        "li" + "ve",
        "au" + "th",
        "wal" + "let",
        "or" + "der",
        "net" + "work",
        "data" + "base",
        "per" + "sist",
        "sign" + "ing",
        "muta" + "tion",
        "b" + "uy",
        "se" + "ll",
        "tra" + "de",
    )


def test_builds_deterministic_source_gap_report_for_unbacked_probability_moves() -> None:
    module = api()

    report = build_report()
    replayed = build_report(
        candidate(
            packet_id="packet-beta",
            market_id="market-beta",
            event_title="Beta source-backed drift",
            previous_probability=d("0.550000"),
            current_probability=d("0.590000"),
            source_count=d("3"),
            official_source_count=d("1"),
            latest_source_age_seconds=d("900.000000"),
            contradiction_severity=d("0.000000"),
            liquidity_depth_usd=d("1500.000000"),
        ),
        candidate(),
        candidate(
            packet_id="packet-gamma",
            market_id="market-gamma",
            event_title="Gamma partial source move",
            previous_probability=d("0.720000"),
            current_probability=d("0.650000"),
            source_count=d("1"),
            official_source_count=d("1"),
            latest_source_age_seconds=d("5000.000000"),
            contradiction_severity=d("0.300000"),
            liquidity_depth_usd=d("400.000000"),
        ),
    )

    assert report.payload == replayed.payload
    assert report.derived_validation_digest == replayed.derived_validation_digest
    assert report.candidate_count == d("3")
    assert report.pass_candidate_count == d("1")
    assert report.watch_candidate_count == d("1")
    assert report.blocked_candidate_count == d("1")
    assert report.unsupported_move_count == d("2")
    assert report.unsupported_move_ratio == d("0.666667")
    assert report.large_move_count == d("1")
    assert report.insufficient_source_count == d("2")
    assert report.official_source_missing_count == d("1")
    assert report.source_recency_gap_count == d("2")
    assert report.severe_contradiction_count == d("1")
    assert report.thin_liquidity_count == d("1")
    assert report.max_move_magnitude == d("0.130000")
    assert report.max_contradiction_severity == d("0.800000")
    assert report.min_liquidity_depth_usd == d("75.000000")
    assert report.report_status == "blocked"
    assert report.reason_codes == (
        "probability_move_source_gap_v2_blocked",
        "move_large_present",
        "move_medium_present",
        "source_count_low_present",
        "official_source_missing_present",
        "source_recency_stale_present",
        "source_recency_watch_present",
        "contradiction_elevated_present",
        "contradiction_severe_present",
        "liquidity_thin_present",
    )

    assert tuple(row.packet_id for row in report.rows) == (
        "packet-alpha",
        "packet-gamma",
        "packet-beta",
    )

    blocked = report.rows[0]
    assert blocked.rank == d("1")
    assert blocked.move_magnitude == d("0.130000")
    assert blocked.move_direction == "up"
    assert blocked.move_band == "large"
    assert blocked.source_gap_count == d("1")
    assert blocked.official_source_present is False
    assert blocked.source_recency_status == "stale"
    assert blocked.contradiction_status == "severe"
    assert blocked.liquidity_context == "thin"
    assert blocked.gap_status == "blocked"
    assert blocked.reason_codes == (
        "move_large",
        "source_count_low",
        "official_source_missing",
        "source_recency_stale",
        "contradiction_severe",
        "liquidity_thin",
    )

    watched = report.rows[1]
    assert watched.move_magnitude == d("0.070000")
    assert watched.move_direction == "down"
    assert watched.move_band == "medium"
    assert watched.gap_status == "watch"
    assert watched.reason_codes == (
        "move_medium",
        "source_count_low",
        "official_source_present",
        "source_recency_watch",
        "contradiction_elevated",
        "liquidity_normal",
    )

    passed = report.rows[2]
    assert passed.move_band == "small"
    assert passed.gap_status == "pass"
    assert passed.reason_codes == (
        "move_small",
        "source_count_sufficient",
        "official_source_present",
        "source_recency_fresh",
        "contradiction_none",
        "liquidity_deep",
    )

    payload = report.payload
    assert payload == module.research_packet_probability_move_source_gap_v2_payload(report)
    assert payload["generated_at"] == "2026-07-07T09:30:00Z"
    assert payload["candidate_count"] == "3"
    assert payload["unsupported_move_ratio"] == "0.666667"
    assert payload["rows"][0]["move_magnitude"] == "0.130000"
    assert payload["rows"][0]["source_gap_count"] == "1"
    assert payload["rows"][0]["official_source_present"] is False
    assert payload["rows"][0]["reason_codes"] == list(blocked.reason_codes)
    assert (
        module.derive_research_packet_probability_move_source_gap_v2_digest(payload)
        == report.derived_validation_digest
    )
    assert not any(type(value) is Decimal for value in walk(payload))
    assert not any(type(value) is float for value in walk(payload))
    assert not any(type(value) is int for value in walk(payload))
    json.dumps(payload, sort_keys=True)


def test_validation_requires_decimal_inputs_frozen_dataclasses_and_hard_flags() -> None:
    module = api()
    report = build_report()

    for value in (config(), candidate(), report.rows[0], report):
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="previous_probability must be a Decimal"):
        candidate(previous_probability=_DecimalSubclass("0.400000"))
    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        candidate(source_count=1)
    with pytest.raises(ValueError, match="liquidity_depth_usd must be a Decimal"):
        candidate(liquidity_depth_usd=75.0)
    with pytest.raises(ValueError, match="latest_source_age_seconds must be a Decimal"):
        candidate(latest_source_age_seconds=1)
    with pytest.raises(ValueError, match="source_count must be nonnegative"):
        candidate(source_count=d("-1"))
    with pytest.raises(ValueError, match="readonly"):
        candidate(readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="medium_move_threshold"):
        config(medium_move_threshold=d("0.110000"))
    with pytest.raises(ValueError, match="gap_status must match"):
        replace(report.rows[0], gap_status="pass")
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="candidate rows"):
        module.build_research_packet_probability_move_source_gap_v2(
            [object()],
            config=config(),
            generated_at=stamp(),
        )


def test_derived_validation_digest_rejects_report_and_payload_tampering() -> None:
    module = api()
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, blocked_candidate_count=d("0"))

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(
            report,
            rows=(
                replace(report.rows[0], event_title="Alpha probability revision"),
                report.rows[1],
                report.rows[2],
            ),
        )

    payload = report.payload
    tampered_payload = {
        **payload,
        "rows": [
            {**payload["rows"][0], "current_probability": "0.540000"},
            payload["rows"][1],
            payload["rows"][2],
        ],
    }
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.research_packet_probability_move_source_gap_v2_payload(tampered_payload)

    refreshed_payload = {
        **tampered_payload,
        "derived_validation_digest": module.derive_research_packet_probability_move_source_gap_v2_digest(
            tampered_payload,
        ),
    }
    assert (
        module.research_packet_probability_move_source_gap_v2_payload(
            refreshed_payload,
        )["rows"][0]["current_probability"]
        == "0.540000"
    )


def test_public_payload_rejects_unsafe_text_numeric_scalars_and_unknown_fields() -> None:
    module = api()
    payload = build_report().payload

    for term in unsafe_terms():
        with pytest.raises(ValueError, match="unsafe public payload key"):
            module.research_packet_probability_move_source_gap_v2_payload(
                {**payload, f"{term}_hint": "blocked"},
            )
        with pytest.raises(ValueError, match="unsafe public payload value"):
            module.research_packet_probability_move_source_gap_v2_payload(
                {**payload, "config_version": f"mentions {term}"},
            )
        with pytest.raises(ValueError, match="contains unsafe text"):
            candidate(packet_id=f"packet-{term}")

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.research_packet_probability_move_source_gap_v2_payload(
            {**payload, "max_move_magnitude": 0.13},
        )
    with pytest.raises(ValueError, match="JSON numeric value must use Decimal"):
        module.research_packet_probability_move_source_gap_v2_payload(
            {**payload, "candidate_count": 3},
        )
    with pytest.raises(ValueError, match="payload must be readonly"):
        module.research_packet_probability_move_source_gap_v2_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="payload field is not supported"):
        module.research_packet_probability_move_source_gap_v2_payload(
            {**payload, "unexpected_field": "not supported"},
        )


def test_public_api_and_module_scope_stay_pure_phase_one_report_only() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_PROBABILITY_MOVE_SOURCE_GAP_V2_CONFIG_VERSION",
        "ResearchPacketProbabilityMoveSourceGapV2Candidate",
        "ResearchPacketProbabilityMoveSourceGapV2Config",
        "ResearchPacketProbabilityMoveSourceGapV2Report",
        "ResearchPacketProbabilityMoveSourceGapV2Row",
        "build_research_packet_probability_move_source_gap_v2",
        "derive_research_packet_probability_move_source_gap_v2_digest",
        "research_packet_probability_move_source_gap_v2_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    source = Path(
        "src/polymarket_alpha_lab/research_packet_probability_move_source_gap_v2.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "ccxt",
        "http",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "subprocess",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "commit",
        "connect",
        "delete",
        "execute",
        "executemany",
        "float",
        "open",
        "patch",
        "post",
        "put",
        "request",
        "rollback",
        "send",
        "submit",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls
