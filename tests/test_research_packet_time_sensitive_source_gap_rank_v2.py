from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import importlib
import inspect
import json

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_packet_time_sensitive_source_gap_rank_v2"


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def gap_input(**overrides: object):
    module = api()
    now = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
    values: dict[str, object] = {
        "packet_id": "packet-alpha",
        "gap_id": "gap-alpha",
        "question_ref": "question-alpha",
        "source_ref": "source-alpha",
        "source_observed_at": now - timedelta(minutes=30),
        "required_by_at": now + timedelta(hours=1),
        "source_relevance_score": d("0.500000"),
        "gap_severity_score": d("0.500000"),
        "time_sensitivity_score": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchPacketTimeSensitiveSourceGapRankV2Input(**values)


def build_report(rows: tuple[object, ...] | None = None):
    module = api()
    now = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
    if rows is None:
        rows = (
            gap_input(
                packet_id="packet-official",
                gap_id="gap-official",
                question_ref="question-official",
                source_ref="source-official",
                source_observed_at=now - timedelta(minutes=5),
                required_by_at=now + timedelta(minutes=5),
                source_relevance_score=d("0.500000"),
                gap_severity_score=d("0.550000"),
                time_sensitivity_score=d("0.700000"),
                official_source_required=True,
                official_source_observed=False,
            ),
            gap_input(
                packet_id="packet-stale",
                gap_id="gap-stale",
                question_ref="question-stale",
                source_ref="source-stale",
                source_observed_at=now - timedelta(hours=2),
                required_by_at=now + timedelta(hours=2),
                source_relevance_score=d("0.500000"),
                gap_severity_score=d("0.500000"),
                time_sensitivity_score=d("0.600000"),
            ),
            gap_input(
                packet_id="packet-low",
                gap_id="gap-low",
                question_ref="question-low",
                source_ref="source-low",
                source_observed_at=now - timedelta(minutes=5),
                required_by_at=now + timedelta(hours=4),
                source_relevance_score=d("0.300000"),
                gap_severity_score=d("0.300000"),
                time_sensitivity_score=d("0.300000"),
            ),
        )
    return module.build_research_packet_time_sensitive_source_gap_rank_v2_report(
        rows,
        generated_at=now,
    )


def test_time_sensitive_source_gap_ranking_and_official_boost() -> None:
    report = build_report()

    assert report.row_count == d("3.000000")
    assert tuple(row.gap_id for row in report.rows) == (
        "gap-official",
        "gap-stale",
        "gap-low",
    )
    assert tuple(row.rank for row in report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert report.rows[0].urgent_official_source_boost == d("0.250000")
    assert report.rows[0].time_sensitive_source_gap_score == d("0.872500")
    assert report.rows[0].status == "urgent"
    assert "urgent_official_source_boost" in report.rows[0].reason_codes
    assert report.urgent_count == d("2.000000")
    assert report.watch_count == d("0.000000")
    assert report.blocked_count == d("1.000000")


def test_source_age_penalties_increase_stale_gap_priority() -> None:
    report = build_report()
    stale = report.rows[1]
    fresh_low = report.rows[2]

    assert stale.source_age_seconds == d("7200.000000")
    assert stale.source_age_penalty == d("0.300000")
    assert fresh_low.source_age_seconds == d("300.000000")
    assert fresh_low.source_age_penalty == d("0.025000")
    assert stale.time_sensitive_source_gap_score > fresh_low.time_sensitive_source_gap_score
    assert "source_age_penalty" in stale.reason_codes


def test_payload_serializes_decimal_values_as_strings_and_validates_digest() -> None:
    module = api()
    report = build_report()
    payload = module.research_packet_time_sensitive_source_gap_rank_v2_payload(report)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["row_count"] == "3.000000"
    assert payload["urgent_count"] == "2.000000"
    assert payload["top_time_sensitive_source_gap_score"] == "0.872500"
    assert payload["rows"][0]["source_age_seconds"] == "300.000000"
    assert payload["rows"][0]["time_sensitive_source_gap_score"] == "0.872500"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert json.loads(json.dumps(payload, sort_keys=True))["row_count"] == "3.000000"
    _assert_no_public_numeric_scalars(payload)

    assert module.research_packet_time_sensitive_source_gap_rank_v2_payload(payload) == payload


def test_frozen_dataclasses_and_hard_phase_flags() -> None:
    module = api()
    subject = gap_input()
    report = build_report()

    assert module.ResearchPacketTimeSensitiveSourceGapRankV2Config.__dataclass_params__.frozen
    assert module.ResearchPacketTimeSensitiveSourceGapRankV2Input.__dataclass_params__.frozen
    assert module.ResearchPacketTimeSensitiveSourceGapRankV2Row.__dataclass_params__.frozen
    assert module.ResearchPacketTimeSensitiveSourceGapRankV2Report.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.packet_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.row_count = d("0.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchPacketTimeSensitiveSourceGapRankV2Config(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(TypeError, match="does not support subclassing"):
        type(
            "ReportSubclass",
            (module.ResearchPacketTimeSensitiveSourceGapRankV2Report,),
            {},
        )


def test_derived_validation_digest_rejects_report_and_payload_tampering() -> None:
    module = api()
    report = build_report()

    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = module.research_packet_time_sensitive_source_gap_rank_v2_payload(report)
    tampered = dict(payload)
    tampered["row_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_packet_time_sensitive_source_gap_rank_v2_payload(tampered)

    missing_flag = dict(payload)
    missing_flag.pop("readonly")
    with pytest.raises(ValueError, match="readonly"):
        module.research_packet_time_sensitive_source_gap_rank_v2_payload(missing_flag)


def test_rejects_unsafe_public_keys_and_values() -> None:
    module = api()
    unsafe_terms = (
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
    )

    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe public payload"):
            gap_input(public_note=f"{term} reference")
        with pytest.raises(ValueError, match="unsafe public payload"):
            module._reject_unsafe_public_payload("payload", {f"{term}_ref": "safe"})

    payload = module.research_packet_time_sensitive_source_gap_rank_v2_payload(build_report())
    unsafe_payload = dict(payload)
    unsafe_payload["wallet_ref"] = "safe"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_packet_time_sensitive_source_gap_rank_v2_payload(unsafe_payload)


def test_validation_rejects_bad_rows_future_sources_and_non_decimal_scores() -> None:
    module = api()
    now = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="rows must be an iterable"):
        module.build_research_packet_time_sensitive_source_gap_rank_v2_report(
            object(),
            generated_at=now,
        )
    with pytest.raises(ValueError, match="config must be"):
        module.build_research_packet_time_sensitive_source_gap_rank_v2_report(
            (),
            generated_at=now,
            config=object(),
        )
    with pytest.raises(ValueError, match="source_relevance_score must be a Decimal"):
        gap_input(source_relevance_score="0.500000")
    with pytest.raises(ValueError, match="time_sensitivity_score must not exceed six"):
        gap_input(time_sensitivity_score=d("0.1234567"))
    with pytest.raises(ValueError, match="source_observed_at must not be after generated_at"):
        module.build_research_packet_time_sensitive_source_gap_rank_v2_report(
            (gap_input(source_observed_at=now + timedelta(seconds=1)),),
            generated_at=now,
        )
    with pytest.raises(ValueError, match="duplicate packet gap keys"):
        module.build_research_packet_time_sensitive_source_gap_rank_v2_report(
            (gap_input(), gap_input(source_ref="source-beta")),
            generated_at=now,
        )


def test_empty_report_is_readonly_report_only_and_digest_backed() -> None:
    module = api()
    report = module.build_research_packet_time_sensitive_source_gap_rank_v2_report(
        (),
        generated_at=datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
    )

    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.top_time_sensitive_source_gap_score == d("0.000000")
    assert report.reason_codes == ("no_time_sensitive_source_gaps",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64


def test_module_exports_are_isolated_and_have_no_unsafe_surfaces() -> None:
    module = api()
    source = inspect.getsource(module)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_TIME_SENSITIVE_SOURCE_GAP_RANK_V2_CONFIG_VERSION",
        "REASON_CODES",
        "ResearchPacketTimeSensitiveSourceGapRankV2Config",
        "ResearchPacketTimeSensitiveSourceGapRankV2Input",
        "ResearchPacketTimeSensitiveSourceGapRankV2Report",
        "ResearchPacketTimeSensitiveSourceGapRankV2Row",
        "STATUSES",
        "build_research_packet_time_sensitive_source_gap_rank_v2_report",
        "research_packet_time_sensitive_source_gap_rank_v2_payload",
    )

    forbidden_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "supabase",
    }
    forbidden_call_names = {
        "authenticate",
        "cancel_order",
        "create_order",
        "open",
        "place_order",
        "read_text",
        "submit_order",
        "write_text",
    }
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom):
            assert node.module is not None
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            call_name = ""
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
            assert call_name not in forbidden_call_names

    public_names = tuple(name for name in module.__all__)
    normalized_public_names = " ".join(public_names).lower()
    for forbidden_fragment in (
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
        assert forbidden_fragment not in normalized_public_names


def _assert_no_public_numeric_scalars(value: object) -> None:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return
    if isinstance(value, (Decimal, float, int)):
        raise AssertionError(f"public numeric value must be serialized as a string: {value!r}")
    if isinstance(value, list):
        for item in value:
            _assert_no_public_numeric_scalars(item)
        return
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_public_numeric_scalars(item)
        return
    raise AssertionError(f"unsupported payload value: {value!r}")
