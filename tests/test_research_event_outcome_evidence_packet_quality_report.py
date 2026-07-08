from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_event_outcome_evidence_packet_quality_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_outcome_evidence_packet_quality_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api() -> Any:
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None, f"{MODULE_NAME} should exist"
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


class _DecimalSubclass(Decimal):
    pass


def packet(
    label: str,
    *,
    official_age_seconds: int = 1800,
    official_source_count: str | Decimal = "2",
    independent_source_count: str | Decimal = "1",
    contradiction_pressure: str | Decimal = "0.050000",
    required_resolution_rule_count: str | Decimal = "4",
    covered_resolution_rule_count: str | Decimal = "4",
) -> Any:
    module = api()
    return module.ResearchEventOutcomeEvidencePacketQualityReportInput(
        evidence_packet_label=label,
        latest_official_evidence_at=GENERATED_AT - timedelta(
            seconds=official_age_seconds,
        ),
        official_source_count=(
            official_source_count
            if isinstance(official_source_count, Decimal)
            else d(official_source_count)
        ),
        independent_source_count=(
            independent_source_count
            if isinstance(independent_source_count, Decimal)
            else d(independent_source_count)
        ),
        contradiction_pressure=(
            contradiction_pressure
            if isinstance(contradiction_pressure, Decimal)
            else d(contradiction_pressure)
        ),
        required_resolution_rule_count=(
            required_resolution_rule_count
            if isinstance(required_resolution_rule_count, Decimal)
            else d(required_resolution_rule_count)
        ),
        covered_resolution_rule_count=(
            covered_resolution_rule_count
            if isinstance(covered_resolution_rule_count, Decimal)
            else d(covered_resolution_rule_count)
        ),
    )


def build_report(*items: Any, config: Any | None = None) -> Any:
    module = api()
    return module.build_research_event_outcome_evidence_packet_quality_report(
        items,
        generated_at=GENERATED_AT,
        config=config
        or module.ResearchEventOutcomeEvidencePacketQualityReportConfig(),
    )


def assert_no_public_numeric_scalars(value: object) -> None:
    if value is None or type(value) is bool or type(value) is str:
        return
    if isinstance(value, (Decimal, int, float)):
        raise AssertionError(f"public payload contains numeric scalar: {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_public_numeric_scalars(item)
        return
    if type(value) is list:
        for item in value:
            assert_no_public_numeric_scalars(item)
        return
    raise AssertionError(f"unexpected public payload value: {value!r}")


def test_quality_report_aggregates_pass_watch_and_block_packets() -> None:
    report = build_report(
        packet(
            "alpha-block",
            official_age_seconds=21600,
            official_source_count="0",
            independent_source_count="0",
            contradiction_pressure="0.800000",
            covered_resolution_rule_count="1",
        ),
        packet(
            "bravo-watch",
            official_age_seconds=7200,
            official_source_count="1",
            independent_source_count="1",
            contradiction_pressure="0.200000",
            covered_resolution_rule_count="3",
        ),
        packet("charlie-pass"),
    )

    assert is_dataclass(report)
    assert report.status == "block"
    assert report.packet_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.max_official_evidence_age_seconds == d("21600.000000")
    assert report.min_source_quorum_score == d("0.000000")
    assert report.max_contradiction_pressure == d("0.800000")
    assert report.min_resolution_rule_coverage_ratio == d("0.250000")
    assert report.average_quality_pressure_score == d("0.541667")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    block_row, watch_row, pass_row = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert block_row.packet_public_label == "evidence-packet-001"
    assert watch_row.packet_public_label == "evidence-packet-002"
    assert pass_row.packet_public_label == "evidence-packet-003"

    assert block_row.official_evidence_age_seconds == d("21600.000000")
    assert block_row.official_freshness_pressure == d("1.000000")
    assert block_row.source_quorum_score == d("0.000000")
    assert block_row.resolution_rule_coverage_ratio == d("0.250000")
    assert block_row.quality_pressure_score == d("1.000000")
    assert block_row.reason_codes == (
        "official_evidence_freshness_block",
        "official_source_quorum_block",
        "independent_source_quorum_block",
        "contradiction_pressure_block",
        "resolution_rule_coverage_block",
        "evidence_packet_quality_block",
    )

    assert watch_row.official_freshness_pressure == d("0.500000")
    assert watch_row.source_quorum_score == d("0.500000")
    assert watch_row.quality_pressure_score == d("0.500000")
    assert watch_row.reason_codes == (
        "official_evidence_freshness_watch",
        "official_source_quorum_watch",
        "contradiction_pressure_watch",
        "resolution_rule_coverage_watch",
        "evidence_packet_quality_watch",
    )

    assert pass_row.official_freshness_pressure == d("0.125000")
    assert pass_row.source_quorum_score == d("1.000000")
    assert pass_row.quality_pressure_score == d("0.125000")
    assert pass_row.reason_codes == ("evidence_packet_quality_pass",)


def test_empty_report_blocks_without_live_or_mutating_surfaces() -> None:
    module = api()
    report = build_report()

    assert report.status == "block"
    assert report.reason_codes == (
        "evidence_packet_quality_empty",
        "evidence_packet_quality_block",
    )
    assert report.packet_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.rows == ()
    assert report.average_quality_pressure_score == d("1.000000")

    payload = module.research_event_outcome_evidence_packet_quality_report_public_payload(
        report,
    )
    json.dumps(payload, sort_keys=True)
    assert payload["status"] == "block"
    assert payload["packet_count"] == "0"
    assert payload["average_quality_pressure_score"] == "1.000000"
    assert payload["public_digest"] == report.public_digest
    assert_no_public_numeric_scalars(payload)


def test_public_payload_is_deterministic_digest_backed_and_redacted() -> None:
    module = api()
    first = build_report(
        packet("charlie-pass"),
        packet("alpha-block", official_age_seconds=21600, official_source_count="0"),
        packet("bravo-watch", official_age_seconds=7200, official_source_count="1"),
    )
    second = build_report(
        packet("bravo-watch", official_age_seconds=7200, official_source_count="1"),
        packet("charlie-pass"),
        packet("alpha-block", official_age_seconds=21600, official_source_count="0"),
    )

    first_payload = module.research_event_outcome_evidence_packet_quality_report_public_payload(
        first,
    )
    second_payload = module.research_event_outcome_evidence_packet_quality_report_public_payload(
        second,
    )
    encoded_payload = json.dumps(first_payload, sort_keys=True)

    assert first.public_digest == second.public_digest
    assert first_payload == second_payload
    assert first_payload["public_digest"] == first.public_digest
    assert module.research_event_outcome_evidence_packet_quality_report_public_digest(
        first,
    ) == first.public_digest
    assert len(first.public_digest) == 64
    assert all(character in "0123456789abcdef" for character in first.public_digest)
    assert_no_public_numeric_scalars(first_payload)

    for raw_label in ("alpha-block", "bravo-watch", "charlie-pass"):
        assert raw_label not in encoded_payload
    for unsafe_fragment in (
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "http://",
        "https://",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
    ):
        assert unsafe_fragment not in encoded_payload.lower()

    numeric_payload = dict(first_payload)
    numeric_payload["packet_count"] = 3
    with pytest.raises(ValueError, match="Decimal strings"):
        module.validate_research_event_outcome_evidence_packet_quality_report_public_payload(
            numeric_payload,
        )

    invalid_status_payload = dict(first_payload)
    invalid_status_payload["status"] = "blocked"
    with pytest.raises(ValueError, match="status"):
        module.validate_research_event_outcome_evidence_packet_quality_report_public_payload(
            invalid_status_payload,
        )

    for key, value in (
        ("market_slug", "secret-market"),
        ("source_url", "https://example.invalid/source"),
        ("safe_key", "source_text leaked"),
        ("safe_key", "wallet token order"),
        ("safe_key", "buy sell trade sizing recommendation"),
    ):
        tampered = dict(first_payload)
        tampered[key] = value
        with pytest.raises(ValueError, match="unsafe public payload"):
            module.validate_research_event_outcome_evidence_packet_quality_report_public_payload(
                tampered,
            )

    tampered_status = dict(first_payload)
    tampered_status["status"] = "watch"
    with pytest.raises(ValueError, match="public_digest must match"):
        module.validate_research_event_outcome_evidence_packet_quality_report_public_payload(
            tampered_status,
        )

    with pytest.raises(ValueError, match="public_digest"):
        replace(first, public_digest="0" * 64)


def test_dataclasses_are_frozen_and_hard_flags_are_enforced() -> None:
    module = api()
    report = build_report(packet("charlie-pass"))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    for class_name in (
        "ResearchEventOutcomeEvidencePacketQualityReportConfig",
        "ResearchEventOutcomeEvidencePacketQualityReportInput",
        "ResearchEventOutcomeEvidencePacketQualityReportRow",
        "ResearchEventOutcomeEvidencePacketQualityReport",
    ):
        cls = getattr(module, class_name)
        with pytest.raises(TypeError):
            type(f"Bad{class_name}", (cls,), {})

    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchEventOutcomeEvidencePacketQualityReportConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        packet("report-only-flag", official_source_count=d("2")).__class__(
            evidence_packet_label="report-only-flag",
            latest_official_evidence_at=GENERATED_AT,
            official_source_count=d("2"),
            independent_source_count=d("1"),
            contradiction_pressure=d("0.100000"),
            required_resolution_rule_count=d("2"),
            covered_resolution_rule_count=d("2"),
            report_only=False,
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_inputs_require_decimal_only_numerics_and_valid_time_order() -> None:
    module = api()

    with pytest.raises(ValueError, match="Decimal"):
        module.ResearchEventOutcomeEvidencePacketQualityReportConfig(
            max_pass_official_evidence_age_seconds=3600,
        )

    with pytest.raises(ValueError, match="Decimal"):
        module.ResearchEventOutcomeEvidencePacketQualityReportInput(
            evidence_packet_label="bad-count",
            latest_official_evidence_at=GENERATED_AT,
            official_source_count=1,
            independent_source_count=d("1"),
            contradiction_pressure=d("0.100000"),
            required_resolution_rule_count=d("2"),
            covered_resolution_rule_count=d("2"),
        )

    with pytest.raises(ValueError, match="exact Decimal"):
        module.ResearchEventOutcomeEvidencePacketQualityReportInput(
            evidence_packet_label="bad-decimal-subclass",
            latest_official_evidence_at=GENERATED_AT,
            official_source_count=_DecimalSubclass("1"),
            independent_source_count=d("1"),
            contradiction_pressure=d("0.100000"),
            required_resolution_rule_count=d("2"),
            covered_resolution_rule_count=d("2"),
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        module.ResearchEventOutcomeEvidencePacketQualityReportInput(
            evidence_packet_label="bad-time",
            latest_official_evidence_at=datetime(2026, 7, 8, 12, 0),
            official_source_count=d("1"),
            independent_source_count=d("1"),
            contradiction_pressure=d("0.100000"),
            required_resolution_rule_count=d("2"),
            covered_resolution_rule_count=d("2"),
        )

    with pytest.raises(ValueError, match="covered_resolution_rule_count"):
        packet(
            "bad-coverage",
            required_resolution_rule_count="2",
            covered_resolution_rule_count="3",
        )

    with pytest.raises(ValueError, match="latest_official_evidence_at"):
        build_report(packet("future-packet", official_age_seconds=-1))


def test_public_api_and_source_keep_report_only_boundaries() -> None:
    module = api()
    assert module.STATUSES == ("pass", "watch", "block")

    unsafe_name_fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "auth",
        "live",
        "network",
        "database",
        "raw",
    )
    for public_name in module.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in unsafe_name_fragments)

    for class_name in (
        "ResearchEventOutcomeEvidencePacketQualityReportConfig",
        "ResearchEventOutcomeEvidencePacketQualityReportInput",
        "ResearchEventOutcomeEvidencePacketQualityReportRow",
        "ResearchEventOutcomeEvidencePacketQualityReport",
    ):
        for field in fields(getattr(module, class_name)):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in unsafe_name_fragments)

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    forbidden_import_roots = {
        "boto3",
        "ccxt",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "urllib",
        "web3",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
