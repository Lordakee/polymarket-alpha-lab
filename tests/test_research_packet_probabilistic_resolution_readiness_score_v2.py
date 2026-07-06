from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_packet_probabilistic_resolution_readiness_score_v2 import (
    DEFAULT_RESEARCH_PACKET_PROBABILISTIC_RESOLUTION_READINESS_SCORE_V2_CONFIG_VERSION,
    ResearchPacketProbabilisticResolutionReadinessScoreV2Config,
    ResearchPacketProbabilisticResolutionReadinessScoreV2Packet,
    ResearchPacketProbabilisticResolutionReadinessScoreV2Report,
    ResearchPacketProbabilisticResolutionReadinessScoreV2Row,
    build_research_packet_probabilistic_resolution_readiness_score_v2_report,
    research_packet_probabilistic_resolution_readiness_score_v2_payload,
    validate_research_packet_probabilistic_resolution_readiness_score_v2_public_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _unsafe(*parts: str) -> str:
    return "".join(parts)


def assert_no_public_number(value: Any) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) in (int, float, Decimal):
        raise AssertionError("public numeric value found")
    if type(value) is dict:
        for item in value.values():
            assert_no_public_number(item)
    if type(value) in (list, tuple):
        for item in value:
            assert_no_public_number(item)


def _packet(
    packet_id: str = "packet_alpha",
    **overrides: object,
) -> ResearchPacketProbabilisticResolutionReadinessScoreV2Packet:
    values: dict[str, object] = {
        "event_id": f"event_{packet_id}",
        "packet_id": packet_id,
        "event_category": "macro_cpi",
        "captured_at": GENERATED_AT - timedelta(minutes=30),
        "resolution_probability": d("0.950000"),
        "probability_band_width": d("0.030000"),
        "rule_clarity_score": d("0.900000"),
        "primary_source_count": d("1"),
        "independent_source_count": d("2"),
    }
    values.update(overrides)
    return ResearchPacketProbabilisticResolutionReadinessScoreV2Packet(**values)


def _report() -> ResearchPacketProbabilisticResolutionReadinessScoreV2Report:
    return build_research_packet_probabilistic_resolution_readiness_score_v2_report(
        (
            _packet(
                "source_gap_packet",
                resolution_probability=d("0.550000"),
                probability_band_width=d("0.200000"),
                rule_clarity_score=d("0.500000"),
                primary_source_count=d("0"),
                independent_source_count=d("1"),
            ),
            _packet(
                "watch_packet",
                resolution_probability=d("0.820000"),
                probability_band_width=d("0.060000"),
            ),
            _packet("ready_packet"),
        ),
        config=ResearchPacketProbabilisticResolutionReadinessScoreV2Config(),
        generated_at=GENERATED_AT,
    )


def test_scores_probabilistic_resolution_readiness_with_decimal_counts() -> None:
    report = _report()

    assert isinstance(report, ResearchPacketProbabilisticResolutionReadinessScoreV2Report)
    assert (
        report.config_version
        == DEFAULT_RESEARCH_PACKET_PROBABILISTIC_RESOLUTION_READINESS_SCORE_V2_CONFIG_VERSION
    )
    assert report.report_status == "not_ready"
    assert report.packet_count == d("3.000000")
    assert report.ready_packet_count == d("1.000000")
    assert report.watch_packet_count == d("1.000000")
    assert report.not_ready_packet_count == d("1.000000")
    assert report.attention_packet_count == d("2.000000")
    assert report.probability_confidence_gap_packet_count == d("1.000000")
    assert report.probability_band_gap_packet_count == d("1.000000")
    assert report.rule_clarity_gap_packet_count == d("1.000000")
    assert report.primary_source_gap_packet_count == d("1.000000")
    assert report.source_quorum_gap_packet_count == d("1.000000")
    assert report.readiness_score_gap_packet_count == d("2.000000")
    assert report.average_readiness_score == d("0.677667")
    assert report.min_readiness_score_observed == d("0.245000")
    assert tuple((row.packet_id, row.readiness_status) for row in report.rows) == (
        ("source_gap_packet", "not_ready"),
        ("watch_packet", "watch"),
        ("ready_packet", "ready"),
    )
    assert report.rows[0] == ResearchPacketProbabilisticResolutionReadinessScoreV2Row(
        event_id="event_source_gap_packet",
        packet_id="source_gap_packet",
        event_category="macro_cpi",
        captured_at=GENERATED_AT - timedelta(minutes=30),
        resolution_probability=d("0.550000"),
        probability_band_width=d("0.200000"),
        rule_clarity_score=d("0.500000"),
        primary_source_count=d("0.000000"),
        independent_source_count=d("1.000000"),
        probability_confidence_score=d("0.100000"),
        probability_band_component_score=d("0.000000"),
        rule_clarity_component_score=d("0.625000"),
        primary_source_score=d("0.000000"),
        source_quorum_score=d("0.500000"),
        readiness_score=d("0.245000"),
        readiness_status="not_ready",
        reason_codes=(
            "research_packet_probabilistic_resolution_readiness_score_v2_probability_confidence_weak",
            "research_packet_probabilistic_resolution_readiness_score_v2_probability_band_wide",
            "research_packet_probabilistic_resolution_readiness_score_v2_rule_clarity_weak",
            "research_packet_probabilistic_resolution_readiness_score_v2_primary_source_missing",
            "research_packet_probabilistic_resolution_readiness_score_v2_source_quorum_short",
            "research_packet_probabilistic_resolution_readiness_score_v2_readiness_score_short",
        ),
        derived_validation_digest=report.rows[0].derived_validation_digest,
    )
    assert report.reason_code_counts[-1].reason_code.endswith("readiness_score_short")
    assert report.reason_code_counts[-1].packet_count == d("2.000000")
    assert report.reason_code_counts[-1].packet_ratio == d("0.666667")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)


def test_rule_clarity_penalty_and_source_quorum_requirements() -> None:
    config = ResearchPacketProbabilisticResolutionReadinessScoreV2Config()

    unclear_report = build_research_packet_probabilistic_resolution_readiness_score_v2_report(
        (_packet("unclear_packet", rule_clarity_score=d("0.500000")),),
        config=config,
        generated_at=GENERATED_AT,
    )
    assert unclear_report.report_status == "not_ready"
    assert unclear_report.rule_clarity_gap_packet_count == d("1.000000")
    assert unclear_report.rows[0].rule_clarity_component_score == d("0.625000")
    assert unclear_report.rows[0].readiness_score == d("0.865000")
    assert unclear_report.rows[0].readiness_status == "not_ready"

    quorum_report = build_research_packet_probabilistic_resolution_readiness_score_v2_report(
        (_packet("thin_packet", independent_source_count=d("1")),),
        config=config,
        generated_at=GENERATED_AT,
    )
    assert quorum_report.report_status == "not_ready"
    assert quorum_report.source_quorum_gap_packet_count == d("1.000000")
    assert quorum_report.rows[0].source_quorum_score == d("0.500000")
    assert quorum_report.rows[0].readiness_status == "not_ready"


def test_payload_serializes_decimal_strings_and_rejects_public_tampering() -> None:
    report = build_research_packet_probabilistic_resolution_readiness_score_v2_report(
        (
            _packet(
                "offset_packet",
                captured_at=datetime(2026, 7, 6, 7, 30, tzinfo=timezone(timedelta(hours=-4))),
            ),
        ),
        config=ResearchPacketProbabilisticResolutionReadinessScoreV2Config(),
        generated_at=datetime(2026, 7, 6, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = research_packet_probabilistic_resolution_readiness_score_v2_payload(report)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["packet_count"] == "1.000000"
    assert payload["average_readiness_score"] == "0.940000"
    assert payload["rows"][0]["captured_at"] == "2026-07-06T11:30:00+00:00"
    assert payload["rows"][0]["resolution_probability"] == "0.950000"
    assert payload["rows"][0]["probability_confidence_score"] == "0.900000"
    assert payload["rows"][0]["derived_validation_digest"] == report.rows[0].derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_number(payload)
    assert validate_research_packet_probabilistic_resolution_readiness_score_v2_public_payload(
        payload,
    )

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_packet_probabilistic_resolution_readiness_score_v2_public_payload(
            missing_digest,
        )

    tampered_payload = dict(payload)
    tampered_payload["packet_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_packet_probabilistic_resolution_readiness_score_v2_payload(tampered_payload)

    tampered_row_payload = dict(payload)
    tampered_row_payload["rows"] = [dict(payload["rows"][0])]
    tampered_row_payload["rows"][0]["readiness_score"] = "0.500000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_packet_probabilistic_resolution_readiness_score_v2_payload(
            tampered_row_payload,
        )

    unsafe_key_payload = dict(payload)
    unsafe_key_payload[_unsafe("wal", "let", "_id")] = "redacted"
    with pytest.raises(ValueError, match="public"):
        research_packet_probabilistic_resolution_readiness_score_v2_payload(
            unsafe_key_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["analyst_note"] = _unsafe("needs_", "tra", "de", "_desk")
    with pytest.raises(ValueError, match="public"):
        research_packet_probabilistic_resolution_readiness_score_v2_payload(
            unsafe_value_payload,
        )


def test_frozen_decimal_only_inputs_flags_and_dataclass_tamper_revalidation() -> None:
    with pytest.raises(ValueError, match="config_version"):
        ResearchPacketProbabilisticResolutionReadinessScoreV2Config(
            config_version=_StringSubclass(
                DEFAULT_RESEARCH_PACKET_PROBABILISTIC_RESOLUTION_READINESS_SCORE_V2_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="min_primary_source_count"):
        ResearchPacketProbabilisticResolutionReadinessScoreV2Config(
            min_primary_source_count=1,
        )
    with pytest.raises(ValueError, match="min_independent_source_count"):
        ResearchPacketProbabilisticResolutionReadinessScoreV2Config(
            min_independent_source_count=_DecimalSubclass("2"),
        )
    with pytest.raises(ValueError, match="resolution_probability"):
        _packet("float_packet", resolution_probability=0.95)
    with pytest.raises(ValueError, match="primary_source_count"):
        _packet("numeric_packet", primary_source_count=1)
    with pytest.raises(ValueError, match="event_id"):
        _packet("unsafe_packet", event_id=_unsafe("au", "th", "_reference"))
    with pytest.raises(ValueError, match="captured_at"):
        _packet("naive_packet", captured_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_research_packet_probabilistic_resolution_readiness_score_v2_report(
            (_packet("packet"),),
            config=ResearchPacketProbabilisticResolutionReadinessScoreV2Config(),
            generated_at=_DateTimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(ResearchPacketProbabilisticResolutionReadinessScoreV2Config(), paper_only=False)

    report = _report()
    with pytest.raises(FrozenInstanceError):
        report.report_status = "ready"
    with pytest.raises(ValueError, match="readonly"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    tampered_report = _report()
    object.__setattr__(tampered_report.rows[0], "readiness_score", d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest|readiness_score"):
        research_packet_probabilistic_resolution_readiness_score_v2_payload(tampered_report)

    tampered_count_report = _report()
    object.__setattr__(tampered_count_report, "packet_count", d("4.000000"))
    with pytest.raises(ValueError, match="packet_count|derived_validation_digest"):
        research_packet_probabilistic_resolution_readiness_score_v2_payload(
            tampered_count_report,
        )

    for public_type in (
        ResearchPacketProbabilisticResolutionReadinessScoreV2Config,
        ResearchPacketProbabilisticResolutionReadinessScoreV2Packet,
        ResearchPacketProbabilisticResolutionReadinessScoreV2Row,
        ResearchPacketProbabilisticResolutionReadinessScoreV2Report,
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):

            class _Subclass(public_type):  # type: ignore[misc, valid-type]
                pass


def test_module_scope_is_readonly_report_only_and_has_no_external_surface() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.research_packet_probabilistic_resolution_readiness_score_v2",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    lowered_source = source.lower()

    forbidden_surface_tokens = (
        _unsafe("li", "ve"),
        _unsafe("au", "th"),
        _unsafe("wal", "let"),
        _unsafe("ord", "er"),
        _unsafe("net", "work"),
        _unsafe("data", "base"),
        _unsafe("per", "sist"),
        _unsafe("sign", "ing"),
        _unsafe("muta", "tion"),
        _unsafe("bu", "y"),
        _unsafe("se", "ll"),
        _unsafe("tra", "de"),
    )
    assert not any(token in lowered_source for token in forbidden_surface_tokens)
    assert not hasattr(module, "client")
    assert not hasattr(module, "session")

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "asyncio",
        "http",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
