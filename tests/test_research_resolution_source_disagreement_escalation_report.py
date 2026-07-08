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


GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def _api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_resolution_source_disagreement_escalation_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> object:
    module = _api()
    values = {
        "watch_escalation_score": d("0.350000"),
        "block_escalation_score": d("0.650000"),
        "low_oracle_clarity_floor": d("0.500000"),
        "deadline_pressure_watch_hours": d("72.000000"),
        "deadline_pressure_block_hours": d("24.000000"),
    }
    values.update(overrides)
    return module.ResearchResolutionSourceDisagreementEscalationConfig(**values)


def _input(
    bucket_id: str = "bucket-a",
    *,
    evidence_conflict_score: Decimal = d("0.100000"),
    weakest_source_class_reliability: Decimal = d("0.900000"),
    strongest_source_class_reliability: Decimal = d("0.950000"),
    oracle_clarity_score: Decimal = d("0.900000"),
    hours_to_deadline: Decimal = d("168.000000"),
    aggregate_evidence_count: Decimal = d("8"),
    disagreeing_source_class_count: Decimal = d("1"),
    source_class_count: Decimal = d("4"),
    observed_at: datetime = GENERATED_AT - timedelta(hours=1),
) -> object:
    return _api().ResearchResolutionSourceDisagreementEscalationInput(
        bucket_id=bucket_id,
        evidence_conflict_score=evidence_conflict_score,
        weakest_source_class_reliability=weakest_source_class_reliability,
        strongest_source_class_reliability=strongest_source_class_reliability,
        oracle_clarity_score=oracle_clarity_score,
        hours_to_deadline=hours_to_deadline,
        aggregate_evidence_count=aggregate_evidence_count,
        disagreeing_source_class_count=disagreeing_source_class_count,
        source_class_count=source_class_count,
        observed_at=observed_at,
    )


def _report(
    *rows: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> object:
    return _api().build_research_resolution_source_disagreement_escalation_report(
        rows,
        config=cfg or _config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_public_safe_blocked_report() -> None:
    module = _api()

    report = _report(generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))))

    assert type(report) is module.ResearchResolutionSourceDisagreementEscalationReport
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        "research-resolution-source-disagreement-escalation-report-v0"
    )
    assert report.status == "block"
    assert report.input_count == d("0")
    assert report.row_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.max_escalation_score == d("0.000000")
    assert report.average_escalation_score is None
    assert report.rows == ()
    assert report.reason_codes == (
        "resolution_source_disagreement_escalation_empty",
    )
    assert report.reason_code_counts == (
        module.ResearchResolutionSourceDisagreementEscalationReasonCodeCount(
            reason_code="resolution_source_disagreement_escalation_empty",
            count=d("1"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.report_digest) == 64


def test_escalates_using_conflict_reliability_oracle_clarity_and_deadline_pressure() -> None:
    module = _api()

    report = _report(
        _input(
            "bucket-clear",
            evidence_conflict_score=d("0.100000"),
            weakest_source_class_reliability=d("0.880000"),
            strongest_source_class_reliability=d("0.920000"),
            oracle_clarity_score=d("0.900000"),
            hours_to_deadline=d("120.000000"),
            aggregate_evidence_count=d("8"),
            disagreeing_source_class_count=d("1"),
            source_class_count=d("4"),
        ),
        _input(
            "bucket-watch",
            evidence_conflict_score=d("0.420000"),
            weakest_source_class_reliability=d("0.510000"),
            strongest_source_class_reliability=d("0.820000"),
            oracle_clarity_score=d("0.600000"),
            hours_to_deadline=d("60.000000"),
            aggregate_evidence_count=d("6"),
            disagreeing_source_class_count=d("2"),
            source_class_count=d("4"),
        ),
        _input(
            "bucket-block",
            evidence_conflict_score=d("0.780000"),
            weakest_source_class_reliability=d("0.200000"),
            strongest_source_class_reliability=d("0.900000"),
            oracle_clarity_score=d("0.300000"),
            hours_to_deadline=d("12.000000"),
            aggregate_evidence_count=d("10"),
            disagreeing_source_class_count=d("4"),
            source_class_count=d("5"),
        ),
    )

    assert module.PUBLIC_STATUSES == ("pass", "watch", "block")
    assert report.status == "block"
    assert report.input_count == d("3")
    assert report.row_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.max_escalation_score == d("0.748000")
    assert report.average_escalation_score == d("0.433333")
    assert report.aggregate_evidence_count == d("24")
    assert report.disagreeing_source_class_count == d("7")
    assert report.source_class_count == d("13")
    assert report.max_deadline_pressure_score == d("1.000000")
    assert report.average_oracle_clarity_score == d("0.600000")
    assert report.average_source_class_reliability_spread == d("0.350000")

    assert tuple(
        (
            row.bucket_id,
            row.status,
            row.evidence_conflict_score,
            row.source_class_reliability_spread,
            row.deadline_pressure_score,
            row.escalation_score,
        )
        for row in report.rows
    ) == (
        (
            "bucket-block",
            "block",
            d("0.780000"),
            d("0.700000"),
            d("1.000000"),
            d("0.748000"),
        ),
        (
            "bucket-watch",
            "watch",
            d("0.420000"),
            d("0.310000"),
            d("0.500000"),
            d("0.374000"),
        ),
        (
            "bucket-clear",
            "pass",
            d("0.100000"),
            d("0.040000"),
            d("0.000000"),
            d("0.178000"),
        ),
    )
    assert report.rows[0].reason_codes == (
        "deadline_pressure_block",
        "high_aggregate_evidence_conflict",
        "low_oracle_clarity",
        "resolution_source_disagreement_block",
        "source_class_reliability_gap",
    )
    assert report.rows[1].reason_codes == (
        "deadline_pressure_watch",
        "moderate_aggregate_evidence_conflict",
        "resolution_source_disagreement_watch",
        "source_class_reliability_gap",
    )
    assert report.rows[2].reason_codes == (
        "resolution_source_disagreement_pass",
    )


def test_rows_reason_codes_payload_and_digest_are_deterministic() -> None:
    observations = (
        _input(
            "bucket-b",
            evidence_conflict_score=d("0.420000"),
            weakest_source_class_reliability=d("0.510000"),
            strongest_source_class_reliability=d("0.820000"),
            oracle_clarity_score=d("0.600000"),
            hours_to_deadline=d("60.000000"),
            aggregate_evidence_count=d("6"),
            disagreeing_source_class_count=d("2"),
            source_class_count=d("4"),
        ),
        _input(
            "bucket-a",
            evidence_conflict_score=d("0.780000"),
            weakest_source_class_reliability=d("0.200000"),
            strongest_source_class_reliability=d("0.900000"),
            oracle_clarity_score=d("0.300000"),
            hours_to_deadline=d("12.000000"),
            aggregate_evidence_count=d("10"),
            disagreeing_source_class_count=d("4"),
            source_class_count=d("5"),
        ),
    )
    forward = _report(*observations)
    reverse = _report(*reversed(observations))

    assert forward == reverse
    assert tuple(row.bucket_id for row in forward.rows) == ("bucket-a", "bucket-b")
    assert tuple(row.reason_codes for row in forward.rows) == tuple(
        tuple(sorted(row.reason_codes)) for row in forward.rows
    )

    payload = _api().research_resolution_source_disagreement_escalation_report_payload(
        forward,
    )
    payload_again = _api().research_resolution_source_disagreement_escalation_report_payload(
        reverse,
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == payload_again
    assert payload["report_digest"] == forward.report_digest
    assert payload["rows"][0]["escalation_score"] == "0.748000"
    assert not any(isinstance(value, (Decimal, datetime, float)) for value in _walk(payload))
    for leaked in (
        "source_id",
        "source_name",
        "source_url",
        "url",
        "raw_text",
        "market_id",
        "market_slug",
        "market_identifier",
    ):
        assert leaked not in encoded.lower()


def test_validation_rejects_non_decimal_inputs_bad_statuses_leakage_and_impure_flags() -> None:
    module = _api()

    with pytest.raises(ValueError, match="watch_escalation_score must be a Decimal"):
        _config(watch_escalation_score=0.35)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_conflict_score must be a Decimal"):
        _input(evidence_conflict_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="source_class_count must be positive"):
        _input(source_class_count=d("0"))
    with pytest.raises(ValueError, match="disagreeing_source_class_count"):
        _input(disagreeing_source_class_count=d("5"), source_class_count=d("4"))
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        _report(_input(), generated_at=_DatetimeSubclass(2026, 7, 8, 16, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        _report(_input(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="bucket_id"):
        _input(bucket_id="market_slug-hidden")
    with pytest.raises(ValueError, match="paper_only"):
        replace(_input(), paper_only=False)

    report = _report(_input())
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="clear")
    with pytest.raises(ValueError, match="status"):
        replace(report, status="blocked")
    with pytest.raises(ValueError, match="report_digest"):
        replace(report, report_digest="0" * 64)
    with pytest.raises(ValueError, match="config"):
        module.build_research_resolution_source_disagreement_escalation_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    frozen_input = _input("frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_input.bucket_id = "changed"  # type: ignore[misc]


def test_dataclasses_are_frozen_decimal_only_and_module_has_no_live_side_effect_surface() -> None:
    module = _api()
    report = _report(_input())

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
        / "research_resolution_source_disagreement_escalation_report.py"
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
        "live execution",
        "market_slug",
        "market_id",
        "source_url",
        "raw_text",
        "recommend",
        "sizing",
    ):
        assert forbidden not in lowered


def _walk(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in _walk(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in _walk(child))
    return (value,)
