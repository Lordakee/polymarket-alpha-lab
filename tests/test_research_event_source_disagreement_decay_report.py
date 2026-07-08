from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def _api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_event_source_disagreement_decay_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> object:
    module = _api()
    values = {
        "fresh_contradiction_age_seconds": d("3600.000000"),
        "stale_contradiction_age_seconds": d("86400.000000"),
        "watch_persistence_score": d("0.350000"),
        "block_persistence_score": d("0.650000"),
        "watch_source_reliability_floor": d("0.700000"),
        "block_source_reliability_floor": d("0.400000"),
        "watch_evidence_freshness": d("0.400000"),
        "block_evidence_freshness": d("0.750000"),
        "watch_catalyst_pressure": d("0.400000"),
        "block_catalyst_pressure": d("0.750000"),
        "watch_resolution_proximity": d("0.400000"),
        "block_resolution_proximity": d("0.750000"),
        "watch_contradiction_persistence_score": d("0.250000"),
        "block_contradiction_persistence_score": d("0.900000"),
        "contradiction_age_weight": d("0.300000"),
        "source_reliability_weight": d("0.250000"),
        "evidence_freshness_weight": d("0.150000"),
        "catalyst_pressure_weight": d("0.150000"),
        "resolution_proximity_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchEventSourceDisagreementDecayConfig(**values)


def _input(
    event_domain: str = "weather",
    *,
    aggregate_contradiction_age_seconds: Decimal = d("100000.000000"),
    source_reliability: Decimal = d("0.900000"),
    evidence_freshness: Decimal = d("0.100000"),
    catalyst_pressure: Decimal = d("0.100000"),
    resolution_proximity: Decimal = d("0.100000"),
    contradictory_source_count: Decimal = d("1.000000"),
    source_count: Decimal = d("4.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> object:
    return _api().ResearchEventSourceDisagreementDecayInput(
        event_domain=event_domain,
        aggregate_contradiction_age_seconds=aggregate_contradiction_age_seconds,
        source_reliability=source_reliability,
        evidence_freshness=evidence_freshness,
        catalyst_pressure=catalyst_pressure,
        resolution_proximity=resolution_proximity,
        contradictory_source_count=contradictory_source_count,
        source_count=source_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    rows: tuple[object, ...],
    *,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> object:
    return _api().build_research_event_source_disagreement_decay_report(
        rows,
        config=cfg or _config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_as_public_report_only_workflow() -> None:
    module = _api()

    report = _report(
        (),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert type(report) is module.ResearchEventSourceDisagreementDecayReport
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.domain_count == ZERO
    assert report.input_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.average_persistence_score == ZERO
    assert report.max_persistence_score == ZERO
    assert report.min_aggregate_contradiction_age_seconds == ZERO
    assert report.average_source_reliability is None
    assert report.rows == ()
    assert report.reason_codes == (
        "research_event_source_disagreement_decay_report_no_inputs",
    )
    assert report.reason_code_counts == (
        module.ResearchEventSourceDisagreementDecayReasonCodeCount(
            reason_code="research_event_source_disagreement_decay_report_no_inputs",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.public_digest) == 64


def test_summarizes_disagreement_decay_by_event_domain_deterministically() -> None:
    module = _api()

    rows = (
        _input(
            "sports",
            aggregate_contradiction_age_seconds=d("1800.000000"),
            source_reliability=d("0.350000"),
            evidence_freshness=d("0.900000"),
            catalyst_pressure=d("0.800000"),
            resolution_proximity=d("0.850000"),
            contradictory_source_count=d("4.000000"),
            source_count=d("5.000000"),
        ),
        _input("weather"),
        _input(
            "policy",
            aggregate_contradiction_age_seconds=d("43200.000000"),
            source_reliability=d("0.650000"),
            evidence_freshness=d("0.450000"),
            catalyst_pressure=d("0.550000"),
            resolution_proximity=d("0.400000"),
            contradictory_source_count=d("2.000000"),
            source_count=d("4.000000"),
        ),
        _input("weather"),
    )
    forward = _report(rows)
    reverse = _report(tuple(reversed(rows)))

    assert module.STATUSES == ("pass", "watch", "block")
    assert forward == reverse
    assert forward.status == "block"
    assert forward.domain_count == d("3.000000")
    assert forward.input_count == d("4.000000")
    assert forward.pass_count == d("1.000000")
    assert forward.watch_count == d("1.000000")
    assert forward.block_count == d("1.000000")
    assert forward.average_persistence_score == d("0.456341")
    assert forward.max_persistence_score == d("0.845000")
    assert forward.min_aggregate_contradiction_age_seconds == d("1800.000000")
    assert forward.average_source_reliability == d("0.633333")
    assert forward.max_catalyst_pressure == d("0.800000")
    assert forward.max_resolution_proximity == d("0.850000")
    assert tuple(row.event_domain for row in forward.rows) == (
        "policy",
        "sports",
        "weather",
    )

    watched = forward.rows[0]
    assert type(watched) is module.ResearchEventSourceDisagreementDecayRow
    assert watched.status == "watch"
    assert watched.observation_count == d("1.000000")
    assert watched.aggregate_contradiction_age_seconds == d("43200.000000")
    assert watched.source_reliability == d("0.650000")
    assert watched.evidence_freshness == d("0.450000")
    assert watched.catalyst_pressure == d("0.550000")
    assert watched.resolution_proximity == d("0.400000")
    assert watched.contradictory_source_count == d("2.000000")
    assert watched.source_count == d("4.000000")
    assert watched.source_disagreement_share == d("0.500000")
    assert watched.contradiction_persistence_score == d("0.521739")
    assert watched.source_reliability_risk_score == d("0.350000")
    assert watched.persistence_score == d("0.454022")
    assert watched.reason_codes == (
        "research_event_source_disagreement_decay_report_contradiction_persistence_watch",
        "research_event_source_disagreement_decay_report_source_reliability_watch",
        "research_event_source_disagreement_decay_report_evidence_freshness_watch",
        "research_event_source_disagreement_decay_report_catalyst_pressure_watch",
        "research_event_source_disagreement_decay_report_resolution_proximity_watch",
        "research_event_source_disagreement_decay_report_score_watch",
    )

    blocked = forward.rows[1]
    assert blocked.event_domain == "sports"
    assert blocked.status == "block"
    assert blocked.contradiction_persistence_score == d("1.000000")
    assert blocked.source_reliability_risk_score == d("0.650000")
    assert blocked.persistence_score == d("0.845000")
    assert blocked.reason_codes == (
        "research_event_source_disagreement_decay_report_contradiction_persistence_block",
        "research_event_source_disagreement_decay_report_source_reliability_block",
        "research_event_source_disagreement_decay_report_evidence_freshness_block",
        "research_event_source_disagreement_decay_report_catalyst_pressure_block",
        "research_event_source_disagreement_decay_report_resolution_proximity_block",
        "research_event_source_disagreement_decay_report_score_block",
    )

    passed = forward.rows[2]
    assert passed.event_domain == "weather"
    assert passed.status == "pass"
    assert passed.observation_count == d("2.000000")
    assert passed.persistence_score == d("0.070000")
    assert passed.reason_codes == (
        "research_event_source_disagreement_decay_report_pass",
    )


def test_payload_digest_decimal_strings_and_public_identifier_safety() -> None:
    module = _api()
    rows = (
        _input(
            "z-domain",
            aggregate_contradiction_age_seconds=d("1800.000000"),
            source_reliability=d("0.350000"),
            evidence_freshness=d("0.900000"),
            catalyst_pressure=d("0.800000"),
            resolution_proximity=d("0.850000"),
        ),
        _input("a-domain"),
    )

    first = _report(rows)
    second = _report(tuple(reversed(rows)))
    first_payload = module.research_event_source_disagreement_decay_report_public_payload(
        first,
    )
    second_payload = module.research_event_source_disagreement_decay_report_public_payload(
        second,
    )
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_payload["rows"][0]["event_domain"] == "a-domain"
    assert first_payload["rows"][1]["persistence_score"] == "0.845000"
    assert first_payload["public_digest"] == first.public_digest
    assert first.public_digest == second.public_digest
    assert first.public_digest == (
        module.research_event_source_disagreement_decay_report_public_digest(first)
    )
    assert first.public_digest == (
        module.research_event_source_disagreement_decay_report_public_digest(
            first_payload,
        )
    )
    assert len(first.public_digest) == 64
    assert not any(isinstance(value, (Decimal, datetime, float)) for value in _walk(first_payload))
    assert ": 1.0" not in encoded
    for leaked in (
        "event_id",
        "market_id",
        "market_slug",
        "source_id",
        "source_name",
        "source_url",
        "raw_text",
        "private",
    ):
        assert leaked not in encoded.lower()

    tampered_payload = dict(first_payload)
    tampered_payload["status"] = "pass"
    with pytest.raises(ValueError, match="public_digest"):
        module.research_event_source_disagreement_decay_report_public_payload(
            tampered_payload,
        )

    leaky_payload = dict(first_payload)
    leaky_payload["event_id"] = "abc"
    with pytest.raises(ValueError, match="unsafe public payload key"):
        module.research_event_source_disagreement_decay_report_public_payload(
            leaky_payload,
        )

    leaky_payload = dict(first_payload)
    leaky_payload["workflow_note"] = "buy recommendation with position sizing"
    with pytest.raises(ValueError, match="unsafe public payload value"):
        module.research_event_source_disagreement_decay_report_public_payload(
            leaky_payload,
        )

    numeric_payload = dict(first_payload)
    numeric_payload["domain_count"] = 2
    with pytest.raises(ValueError, match="Decimal strings"):
        module.research_event_source_disagreement_decay_report_public_payload(
            numeric_payload,
        )


def test_validation_rejects_non_decimal_bad_status_leakage_and_impure_flags() -> None:
    module = _api()

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("research-event-source-disagreement-decay-report-v0"))
    with pytest.raises(ValueError, match="fresh_contradiction_age_seconds"):
        _config(fresh_contradiction_age_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="stale_contradiction_age_seconds"):
        _config(
            fresh_contradiction_age_seconds=d("86400.000000"),
            stale_contradiction_age_seconds=d("3600.000000"),
        )
    with pytest.raises(ValueError, match="watch_persistence_score"):
        _config(watch_persistence_score=d("0.700000"))
    with pytest.raises(ValueError, match="contradiction_age_weight"):
        _config(contradiction_age_weight=d("0.200000"))
    with pytest.raises(ValueError, match="source_reliability"):
        _input(source_reliability=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="event_domain"):
        _input(event_domain=_StringSubclass("weather"))
    with pytest.raises(ValueError, match="event_domain"):
        _input(event_domain="market_id-hidden")
    with pytest.raises(ValueError, match="source_count"):
        _input(source_count=d("0.000000"))
    with pytest.raises(ValueError, match="contradictory_source_count"):
        _input(
            contradictory_source_count=d("5.000000"),
            source_count=d("4.000000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        _input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        _input(readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        _report((), generated_at=_DatetimeSubclass(2026, 7, 8, 18, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="config"):
        module.build_research_event_source_disagreement_decay_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="inputs"):
        _report((object(),))

    report = _report((_input(),))
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="clear")
    with pytest.raises(ValueError, match="status"):
        replace(report, status="blocked")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            report.rows[0],
            reason_codes=(
                "research_event_source_disagreement_decay_report_pass",
                "research_event_source_disagreement_decay_report_score_watch",
            ),
        )
    with pytest.raises(ValueError, match="persistence_score"):
        replace(report.rows[0], persistence_score=d("0.500000"))
    with pytest.raises(ValueError, match="public_digest"):
        replace(report, public_digest="0" * 64)

    frozen_input = _input("frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_input.event_domain = "changed"  # type: ignore[misc]


def test_dataclasses_are_frozen_decimal_only_and_module_has_no_side_effect_surface() -> None:
    module = _api()
    report = _report((_input(),))

    for public_record in (
        _config(),
        _input("dataclass"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            value = getattr(public_record, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal, field.name

    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_event_source_disagreement_decay_report.py"
    )
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    forbidden_import_roots = {
        "aiohttp",
        "asyncio",
        "httpx",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_call_names = {
        "cancel_order",
        "connect",
        "execute",
        "get",
        "open",
        "post",
        "put",
        "replace_order",
        "send",
        "submit_order",
        "trade",
        "write",
        "write_text",
        "write_bytes",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", maxsplit=1)[0])
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            if isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
    assert imported_roots.isdisjoint(forbidden_import_roots)

    lowered = source.lower()
    for forbidden in (
        "private_key",
        "wallet",
        "auth",
        "order",
        "trade",
        "live execution",
        "market_slug",
        "market_id",
        "source_url",
        "raw_text",
        "recommend",
        "sizing",
        "position",
    ):
        assert forbidden not in lowered


def _walk(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in _walk(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in _walk(child))
    return (value,)
