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


class _DateTimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_external_corroboration_gap_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def stamp() -> datetime:
    return datetime(2026, 7, 7, 10, 15, tzinfo=UTC)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_PACKET_EXTERNAL_CORROBORATION_GAP_V2_CONFIG_VERSION
        ),
        "min_independent_family_count": d("2.000000"),
        "fresh_source_max_age_seconds": d("3600.000000"),
        "stale_source_age_seconds": d("86400.000000"),
        "max_duplicate_source_ratio": d("0.500000"),
        "elevated_contradiction_threshold": d("0.250000"),
        "severe_contradiction_threshold": d("0.750000"),
        "material_market_move_threshold": d("0.050000"),
        "large_market_move_threshold": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchPacketExternalCorroborationGapV2Config(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "packet_id": "packet-alpha",
        "claim_id": "claim-alpha",
        "market_id": "market-alpha",
        "captured_at": stamp(),
        "source_count": d("4.000000"),
        "independent_family_count": d("1.000000"),
        "official_source_count": d("0.000000"),
        "latest_source_age_seconds": d("90000.000000"),
        "contradiction_severity": d("0.850000"),
        "market_move_abs": d("0.140000"),
        "market_move_explained": False,
    }
    values.update(overrides)
    return module.ResearchPacketExternalCorroborationGapV2Candidate(**values)


def build_report(*rows: object, **config_overrides: object):
    module = api()
    source_rows = rows or (
        candidate(),
        candidate(
            packet_id="packet-beta",
            claim_id="claim-beta",
            market_id="market-beta",
            source_count=d("3.000000"),
            independent_family_count=d("2.000000"),
            official_source_count=d("1.000000"),
            latest_source_age_seconds=d("5000.000000"),
            contradiction_severity=d("0.300000"),
            market_move_abs=d("0.060000"),
            market_move_explained=False,
        ),
        candidate(
            packet_id="packet-gamma",
            claim_id="claim-gamma",
            market_id="market-gamma",
            source_count=d("4.000000"),
            independent_family_count=d("4.000000"),
            official_source_count=d("1.000000"),
            latest_source_age_seconds=d("600.000000"),
            contradiction_severity=d("0.000000"),
            market_move_abs=d("0.010000"),
            market_move_explained=True,
        ),
    )
    return module.build_research_packet_external_corroboration_gap_v2_report(
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


def test_builds_deterministic_phase_one_external_corroboration_gap_report() -> None:
    module = api()

    report = build_report()
    replayed = build_report(
        candidate(
            packet_id="packet-gamma",
            claim_id="claim-gamma",
            market_id="market-gamma",
            source_count=d("4.000000"),
            independent_family_count=d("4.000000"),
            official_source_count=d("1.000000"),
            latest_source_age_seconds=d("600.000000"),
            contradiction_severity=d("0.000000"),
            market_move_abs=d("0.010000"),
            market_move_explained=True,
        ),
        candidate(
            packet_id="packet-beta",
            claim_id="claim-beta",
            market_id="market-beta",
            source_count=d("3.000000"),
            independent_family_count=d("2.000000"),
            official_source_count=d("1.000000"),
            latest_source_age_seconds=d("5000.000000"),
            contradiction_severity=d("0.300000"),
            market_move_abs=d("0.060000"),
            market_move_explained=False,
        ),
        candidate(),
    )

    assert report.payload == replayed.payload
    assert report.derived_validation_digest == replayed.derived_validation_digest
    assert report.config_version == (
        module.DEFAULT_RESEARCH_PACKET_EXTERNAL_CORROBORATION_GAP_V2_CONFIG_VERSION
    )
    assert report.report_status == "blocked"
    assert report.candidate_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.blocked_count == d("1.000000")
    assert report.attention_count == d("2.000000")
    assert report.attention_ratio == d("0.666667")
    assert report.weak_independent_family_count == d("1.000000")
    assert report.missing_official_source_count == d("1.000000")
    assert report.high_duplicate_source_ratio_count == d("1.000000")
    assert report.source_age_gap_count == d("2.000000")
    assert report.stale_source_age_count == d("1.000000")
    assert report.contradiction_gap_count == d("2.000000")
    assert report.severe_contradiction_count == d("1.000000")
    assert report.unexplained_market_move_count == d("2.000000")
    assert report.large_market_move_count == d("1.000000")
    assert report.max_duplicate_source_ratio == d("0.750000")
    assert report.max_contradiction_severity == d("0.850000")
    assert report.max_market_move_abs == d("0.140000")
    assert report.min_independent_family_count_observed == d("1.000000")
    assert report.reason_codes == (
        "research_packet_external_corroboration_gap_v2_weak_independent_family_count",
        "research_packet_external_corroboration_gap_v2_missing_official_source",
        "research_packet_external_corroboration_gap_v2_high_duplicate_source_ratio",
        "research_packet_external_corroboration_gap_v2_source_age_watch",
        "research_packet_external_corroboration_gap_v2_source_age_stale",
        "research_packet_external_corroboration_gap_v2_contradiction_elevated",
        "research_packet_external_corroboration_gap_v2_contradiction_severe",
        "research_packet_external_corroboration_gap_v2_unexplained_market_move_material",
        "research_packet_external_corroboration_gap_v2_unexplained_market_move_large",
    )

    assert tuple(row.packet_id for row in report.rows) == (
        "packet-alpha",
        "packet-beta",
        "packet-gamma",
    )

    blocked = report.rows[0]
    assert blocked.gap_rank == d("1.000000")
    assert blocked.duplicate_source_count == d("3.000000")
    assert blocked.duplicate_source_ratio == d("0.750000")
    assert blocked.official_source_status == "missing"
    assert blocked.source_age_status == "stale"
    assert blocked.contradiction_status == "severe"
    assert blocked.market_move_status == "large"
    assert blocked.gap_score == d("0.706667")
    assert blocked.gap_status == "blocked"
    assert blocked.reason_codes == (
        "research_packet_external_corroboration_gap_v2_weak_independent_family_count",
        "research_packet_external_corroboration_gap_v2_missing_official_source",
        "research_packet_external_corroboration_gap_v2_high_duplicate_source_ratio",
        "research_packet_external_corroboration_gap_v2_source_age_stale",
        "research_packet_external_corroboration_gap_v2_contradiction_severe",
        "research_packet_external_corroboration_gap_v2_unexplained_market_move_large",
    )

    watched = report.rows[1]
    assert watched.gap_rank == d("2.000000")
    assert watched.duplicate_source_count == d("1.000000")
    assert watched.duplicate_source_ratio == d("0.333333")
    assert watched.official_source_status == "present"
    assert watched.source_age_status == "watch"
    assert watched.contradiction_status == "elevated"
    assert watched.market_move_status == "material"
    assert watched.gap_score == d("0.198889")
    assert watched.gap_status == "watch"
    assert watched.reason_codes == (
        "research_packet_external_corroboration_gap_v2_source_age_watch",
        "research_packet_external_corroboration_gap_v2_contradiction_elevated",
        "research_packet_external_corroboration_gap_v2_unexplained_market_move_material",
    )

    passed = report.rows[2]
    assert passed.gap_rank == d("3.000000")
    assert passed.duplicate_source_ratio == d("0.000000")
    assert passed.source_age_status == "fresh"
    assert passed.contradiction_status == "none"
    assert passed.market_move_status == "quiet"
    assert passed.gap_score == d("0.001667")
    assert passed.gap_status == "pass"
    assert passed.reason_codes == (
        "research_packet_external_corroboration_gap_v2_passed",
    )

    payload = report.payload
    assert payload == module.research_packet_external_corroboration_gap_v2_payload(report)
    assert payload["generated_at"] == "2026-07-07T10:15:00Z"
    assert payload["candidate_count"] == "3.000000"
    assert payload["attention_ratio"] == "0.666667"
    assert payload["rows"][0]["gap_score"] == "0.706667"
    assert payload["rows"][0]["duplicate_source_ratio"] == "0.750000"
    assert payload["rows"][0]["reason_codes"] == list(blocked.reason_codes)
    assert (
        module.derive_research_packet_external_corroboration_gap_v2_digest(payload)
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

    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        candidate(source_count=4)
    with pytest.raises(ValueError, match="market_move_abs must be a Decimal"):
        candidate(market_move_abs=0.1)
    with pytest.raises(ValueError, match="contradiction_severity must be a Decimal"):
        candidate(contradiction_severity=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="captured_at must be timezone-aware"):
        candidate(captured_at=datetime(2026, 7, 7, 10, 15))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_research_packet_external_corroboration_gap_v2_report(
            (candidate(),),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 7, 10, 15, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="independent_family_count must not exceed"):
        candidate(independent_family_count=d("5.000000"))
    with pytest.raises(ValueError, match="official_source_count must not exceed"):
        candidate(official_source_count=d("5.000000"))
    with pytest.raises(ValueError, match="latest_source_age_seconds must be absent"):
        candidate(
            source_count=d("0.000000"),
            independent_family_count=d("0.000000"),
            official_source_count=d("0.000000"),
            latest_source_age_seconds=d("1.000000"),
        )
    with pytest.raises(ValueError, match="readonly"):
        candidate(readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="fresh_source_max_age_seconds"):
        config(fresh_source_max_age_seconds=d("90000.000000"))
    with pytest.raises(ValueError, match="gap_status must match"):
        replace(report.rows[0], gap_status="pass")
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="candidate rows"):
        module.build_research_packet_external_corroboration_gap_v2_report(
            [object()],
            config=config(),
            generated_at=stamp(),
        )


def test_payload_rejects_digest_tampering_unsafe_terms_numeric_values_and_unknown_fields() -> None:
    module = api()
    report = build_report()
    payload = report.payload

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, blocked_count=d("0.000000"))

    tampered_payload = {**payload, "candidate_count": "4.000000"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_packet_external_corroboration_gap_v2_payload(tampered_payload)

    refreshed_payload = {
        **tampered_payload,
        "derived_validation_digest": module.derive_research_packet_external_corroboration_gap_v2_digest(
            tampered_payload,
        ),
    }
    assert (
        module.research_packet_external_corroboration_gap_v2_payload(
            refreshed_payload,
        )["candidate_count"]
        == "4.000000"
    )

    for term in unsafe_terms():
        with pytest.raises(ValueError, match="unsafe public payload key"):
            module.research_packet_external_corroboration_gap_v2_payload(
                {**payload, f"{term}_hint": "blocked"},
            )
        with pytest.raises(ValueError, match="unsafe public payload value"):
            module.research_packet_external_corroboration_gap_v2_payload(
                {**payload, "config_version": f"mentions {term}"},
            )
        with pytest.raises(ValueError, match="contains unsafe text"):
            candidate(packet_id=f"packet-{term}")

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.research_packet_external_corroboration_gap_v2_payload(
            {**payload, "max_market_move_abs": 0.14},
        )
    with pytest.raises(ValueError, match="JSON numeric value must use Decimal"):
        module.research_packet_external_corroboration_gap_v2_payload(
            {**payload, "candidate_count": 3},
        )
    with pytest.raises(ValueError, match="payload must be readonly"):
        module.research_packet_external_corroboration_gap_v2_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="payload field is not supported"):
        module.research_packet_external_corroboration_gap_v2_payload(
            {**payload, "unexpected_field": "not supported"},
        )


def test_public_api_and_module_scope_stay_pure_phase_one_report_only() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_EXTERNAL_CORROBORATION_GAP_V2_CONFIG_VERSION",
        "ResearchPacketExternalCorroborationGapV2Candidate",
        "ResearchPacketExternalCorroborationGapV2Config",
        "ResearchPacketExternalCorroborationGapV2Report",
        "ResearchPacketExternalCorroborationGapV2Row",
        "build_research_packet_external_corroboration_gap_v2_report",
        "derive_research_packet_external_corroboration_gap_v2_digest",
        "research_packet_external_corroboration_gap_v2_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    source = Path(
        "src/polymarket_alpha_lab/research_packet_external_corroboration_gap_v2.py",
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
