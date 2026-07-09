from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_source_market_memory_alignment_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    *,
    review_packet_label: str = "packet-alpha",
    evidence_alignment_score: str = "0.800000",
    mechanics_alignment_score: str = "0.810000",
    specialist_memory_alignment_score: str = "0.790000",
    mechanics_uncertainty_score: str = "0.050000",
    evidence_observed_at: datetime = GENERATED_AT - timedelta(seconds=1800),
    specialist_memory_observed_at: datetime = GENERATED_AT - timedelta(seconds=7200),
):
    report_api = api()
    return report_api.ResearchStrategySourceMarketMemoryAlignmentInput(
        review_packet_label=review_packet_label,
        evidence_alignment_score=d(evidence_alignment_score),
        mechanics_alignment_score=d(mechanics_alignment_score),
        specialist_memory_alignment_score=d(specialist_memory_alignment_score),
        mechanics_uncertainty_score=d(mechanics_uncertainty_score),
        evidence_observed_at=evidence_observed_at,
        specialist_memory_observed_at=specialist_memory_observed_at,
    )


def build_report(*items, generated_at: datetime = GENERATED_AT, config=None):
    report_api = api()
    return report_api.build_research_strategy_source_market_memory_alignment_report(
        items,
        config=config or report_api.ResearchStrategySourceMarketMemoryAlignmentConfig(),
        generated_at=generated_at,
    )


def test_report_aggregates_pass_watch_and_block_alignment_without_raw_identifiers():
    alignment_report = build_report(
        observation(),
        observation(
            review_packet_label="packet-beta",
            evidence_alignment_score="0.720000",
            mechanics_alignment_score="0.560000",
            specialist_memory_alignment_score="0.660000",
            mechanics_uncertainty_score="0.300000",
            evidence_observed_at=GENERATED_AT - timedelta(seconds=8000),
            specialist_memory_observed_at=GENERATED_AT - timedelta(seconds=90000),
        ),
        observation(
            review_packet_label="packet-gamma",
            evidence_alignment_score="0.900000",
            mechanics_alignment_score="0.500000",
            specialist_memory_alignment_score="0.300000",
            mechanics_uncertainty_score="0.650000",
            evidence_observed_at=GENERATED_AT - timedelta(seconds=30000),
            specialist_memory_observed_at=GENERATED_AT - timedelta(seconds=300000),
        ),
    )

    assert is_dataclass(alignment_report)
    assert alignment_report.generated_at == GENERATED_AT
    assert alignment_report.config_version == (
        "research-strategy-source-market-memory-alignment-report-v0"
    )
    assert alignment_report.observation_count == d("3")
    assert alignment_report.pass_count == d("1")
    assert alignment_report.watch_count == d("1")
    assert alignment_report.block_count == d("1")
    assert alignment_report.status == "block"
    assert alignment_report.average_pairwise_alignment_gap == d("0.260000")
    assert alignment_report.average_component_floor_score == d("0.550000")
    assert alignment_report.average_mechanics_uncertainty_score == d("0.333333")
    assert alignment_report.average_analyst_review_pressure == d("0.550000")
    assert alignment_report.max_analyst_review_pressure == d("1.000000")
    assert alignment_report.paper_only is True
    assert alignment_report.report_only is True
    assert alignment_report.readonly is True

    assert tuple(row.status for row in alignment_report.rows) == (
        "block",
        "watch",
        "pass",
    )
    blocked, watch, passing = alignment_report.rows
    assert blocked.rank == d("1")
    assert blocked.review_packet_label == "packet-gamma"
    assert blocked.pairwise_alignment_gap == d("0.600000")
    assert blocked.component_floor_score == d("0.300000")
    assert blocked.evidence_age_seconds == d("30000.000000")
    assert blocked.evidence_freshness_score == d("0.000000")
    assert blocked.specialist_memory_age_seconds == d("300000.000000")
    assert blocked.specialist_memory_freshness_score == d("0.000000")
    assert blocked.analyst_review_pressure == d("1.000000")
    assert blocked.reason_codes == (
        "source_market_memory_gap_block",
        "alignment_component_floor_block",
        "evidence_freshness_block",
        "specialist_memory_freshness_block",
        "mechanics_uncertainty_block",
        "analyst_review_pressure_block",
    )
    assert watch.reason_codes == (
        "source_market_memory_gap_watch",
        "alignment_component_floor_watch",
        "evidence_freshness_watch",
        "specialist_memory_freshness_watch",
        "mechanics_uncertainty_watch",
        "analyst_review_pressure_watch",
    )
    assert passing.reason_codes == ("source_market_memory_gap_pass",)

    payload = api().research_strategy_source_market_memory_alignment_report_payload(
        alignment_report,
    )
    encoded = json.dumps(payload, sort_keys=True)
    for forbidden in (
        "candidate_id",
        "candidate_slug",
        "market_id",
        "market_slug",
        "market_question",
        "question:",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
    ):
        assert forbidden not in encoded.lower()


def test_empty_report_is_blocked_report_only_boundary():
    alignment_report = build_report()

    assert alignment_report.observation_count == d("0")
    assert alignment_report.pass_count == d("0")
    assert alignment_report.watch_count == d("0")
    assert alignment_report.block_count == d("0")
    assert alignment_report.status == "block"
    assert alignment_report.reason_codes == (
        "empty_source_market_memory_alignment_inputs",
    )
    assert alignment_report.reason_code_counts == ()
    assert alignment_report.rows == ()
    assert alignment_report.paper_only is True
    assert alignment_report.report_only is True
    assert alignment_report.readonly is True


def test_public_payload_serializes_decimal_strings_and_validates_sha256_digest():
    report_api = api()
    alignment_report = build_report(observation())

    payload = report_api.research_strategy_source_market_memory_alignment_report_payload(
        alignment_report,
    )
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["observation_count"] == "1"
    assert payload["rows"][0]["evidence_alignment_score"] == "0.800000"
    assert payload["rows"][0]["evidence_age_seconds"] == "1800.000000"
    assert len(payload["public_payload_digest"]) == 64
    assert payload["public_payload_digest"] == alignment_report.public_payload_digest
    assert all(type(value) is not float for value in _walk(payload))
    assert all(type(value) is not int for value in _walk(payload))

    with pytest.raises(ValueError, match="public_payload_digest"):
        replace(alignment_report, public_payload_digest="0" * 64)

    tampered_report = replace(alignment_report)
    object.__setattr__(tampered_report, "public_payload_digest", "0" * 64)
    with pytest.raises(ValueError, match="public_payload_digest"):
        report_api.research_strategy_source_market_memory_alignment_report_payload(
            tampered_report,
        )


def test_public_payload_redacts_packet_label_and_binds_digest_to_public_json():
    report_api = api()
    raw_label = "will-fed-cut-rates-in-july"
    alignment_report = build_report(observation(review_packet_label=raw_label))

    payload = report_api.research_strategy_source_market_memory_alignment_report_payload(
        alignment_report,
    )
    encoded = json.dumps(payload, sort_keys=True).lower()
    row_payload = payload["rows"][0]
    expected_label_digest = (
        "sha256:" + hashlib.sha256(raw_label.encode("utf-8")).hexdigest()
    )
    payload_without_digest = dict(payload)
    public_payload_digest = payload_without_digest.pop("public_payload_digest")
    expected_public_digest = hashlib.sha256(
        json.dumps(
            payload_without_digest,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()

    assert raw_label not in encoded
    assert "review_packet_label" not in row_payload
    assert row_payload["review_packet_label_digest"] == expected_label_digest
    assert alignment_report.public_payload_digest == expected_public_digest
    assert public_payload_digest == expected_public_digest


def test_datetimes_normalize_to_utc_and_reject_invalid_time_values():
    eastern = timezone(timedelta(hours=-4))
    alignment_report = build_report(
        observation(
            evidence_observed_at=datetime(2026, 7, 8, 7, 0, tzinfo=eastern),
            specialist_memory_observed_at=datetime(2026, 7, 8, 6, 0, tzinfo=eastern),
        ),
        generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=UTC),
    )

    assert alignment_report.rows[0].evidence_observed_at == datetime(
        2026,
        7,
        8,
        11,
        0,
        tzinfo=UTC,
    )
    assert alignment_report.rows[0].specialist_memory_observed_at == datetime(
        2026,
        7,
        8,
        10,
        0,
        tzinfo=UTC,
    )
    assert alignment_report.rows[0].evidence_age_seconds == d("3600.000000")
    assert alignment_report.rows[0].specialist_memory_age_seconds == d("7200.000000")

    class DateTimeSubclass(datetime):
        pass

    class NoneOffsetTz(tzinfo):
        def utcoffset(self, dt):
            return None

        def dst(self, dt):
            return None

    with pytest.raises(ValueError, match="evidence_observed_at must be timezone-aware"):
        observation(evidence_observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_report(
            observation(),
            generated_at=DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="specialist_memory_observed_at must be timezone-aware"):
        observation(
            specialist_memory_observed_at=datetime(
                2026,
                7,
                8,
                12,
                0,
                tzinfo=NoneOffsetTz(),
            ),
        )
    with pytest.raises(ValueError, match="evidence_observed_at must not be after"):
        build_report(
            observation(evidence_observed_at=GENERATED_AT + timedelta(seconds=1)),
        )
    with pytest.raises(ValueError, match="specialist_memory_observed_at must not be after"):
        build_report(
            observation(
                specialist_memory_observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )


def test_validation_rejects_floats_nonfinite_decimals_flags_and_restricted_labels():
    report_api = api()

    with pytest.raises(ValueError, match="evidence_alignment_score must be a Decimal"):
        report_api.ResearchStrategySourceMarketMemoryAlignmentInput(
            review_packet_label="packet-alpha",
            evidence_alignment_score=0.5,
            mechanics_alignment_score=d("0.500000"),
            specialist_memory_alignment_score=d("0.500000"),
            mechanics_uncertainty_score=d("0.000000"),
            evidence_observed_at=GENERATED_AT,
            specialist_memory_observed_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="evidence_alignment_score must be finite"):
        observation(evidence_alignment_score="NaN")
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(observation(), paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        report_api.ResearchStrategySourceMarketMemoryAlignmentConfig(readonly=False)
    with pytest.raises(ValueError, match="watch_alignment_gap"):
        report_api.ResearchStrategySourceMarketMemoryAlignmentConfig(
            watch_alignment_gap=d("0.400000"),
            block_alignment_gap=d("0.300000"),
        )
    with pytest.raises(ValueError, match="restricted references"):
        observation(review_packet_label="market_slug:raw-value")


@pytest.mark.parametrize(
    "unsafe_label",
    (
        "Packet-Alpha",
        "packet alpha",
        "packet-alpha-buy",
        "packet-alpha-sell",
        "packet-alpha-recommendation",
        "packet-alpha-execution",
        "packet-alpha-sizing",
        "packet-alpha-live",
    ),
)
def test_validation_rejects_nonpublic_or_execution_surface_packet_labels(
    unsafe_label: str,
):
    with pytest.raises(ValueError, match="review_packet_label"):
        observation(review_packet_label=unsafe_label)


def test_public_dataclasses_are_frozen_and_decimal_types_are_strict():
    report_api = api()

    class DecimalSubclass(Decimal):
        pass

    row = observation()
    with pytest.raises(FrozenInstanceError):
        row.evidence_alignment_score = d("0.100000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="mechanics_alignment_score must be a Decimal"):
        report_api.ResearchStrategySourceMarketMemoryAlignmentInput(
            review_packet_label="packet-alpha",
            evidence_alignment_score=d("0.500000"),
            mechanics_alignment_score=DecimalSubclass("0.500000"),
            specialist_memory_alignment_score=d("0.500000"),
            mechanics_uncertainty_score=d("0.000000"),
            evidence_observed_at=GENERATED_AT,
            specialist_memory_observed_at=GENERATED_AT,
        )


def test_public_report_rejects_nondeterministic_row_sequence_and_reason_codes():
    report_api = api()
    alignment_report = build_report(
        observation(
            review_packet_label="packet-gamma",
            evidence_alignment_score="0.900000",
            mechanics_alignment_score="0.500000",
            specialist_memory_alignment_score="0.300000",
            mechanics_uncertainty_score="0.650000",
            evidence_observed_at=GENERATED_AT - timedelta(seconds=30000),
            specialist_memory_observed_at=GENERATED_AT - timedelta(seconds=300000),
        ),
        observation(),
    )

    with pytest.raises(ValueError, match="rows must use deterministic sequence"):
        replace(alignment_report, rows=tuple(reversed(alignment_report.rows)))
    with pytest.raises(ValueError, match="reason_codes must use deterministic sequence"):
        report_api.ResearchStrategySourceMarketMemoryAlignmentRow(
            rank=d("1"),
            review_packet_label="packet-beta",
            status="watch",
            evidence_alignment_score=d("0.720000"),
            mechanics_alignment_score=d("0.560000"),
            specialist_memory_alignment_score=d("0.660000"),
            mechanics_uncertainty_score=d("0.300000"),
            pairwise_alignment_gap=d("0.160000"),
            component_floor_score=d("0.560000"),
            evidence_observed_at=GENERATED_AT - timedelta(seconds=8000),
            evidence_age_seconds=d("8000.000000"),
            evidence_freshness_score=d("0.629630"),
            specialist_memory_observed_at=GENERATED_AT - timedelta(seconds=90000),
            specialist_memory_age_seconds=d("90000.000000"),
            specialist_memory_freshness_score=d("0.652778"),
            analyst_review_pressure=d("0.440000"),
            reason_codes=(
                "analyst_review_pressure_watch",
                "source_market_memory_gap_watch",
                "alignment_component_floor_watch",
                "evidence_freshness_watch",
                "specialist_memory_freshness_watch",
                "mechanics_uncertainty_watch",
            ),
        )


def test_module_scope_has_no_forbidden_execution_surfaces_or_literal_float_constants():
    source_text = Path(
        "src/polymarket_alpha_lab/research_strategy_source_market_memory_alignment_report.py",
    ).read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "order",
        "trade",
        "broker",
        "signing",
        "submit",
        "cancel",
        "database",
        "open(",
        "requests",
        "http",
        "socket",
        "scrap",
        "live",
        "sizing",
        "recommendation",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def _walk(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)
    else:
        yield value
