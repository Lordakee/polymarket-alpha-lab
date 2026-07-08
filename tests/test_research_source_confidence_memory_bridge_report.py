from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_confidence_memory_bridge_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    triage_group: str = "event.cluster.alpha",
    *,
    evidence_family_label: str = "official.filing",
    specialist_label: str = "macro.desk",
    observed_seconds_ago: int = 600,
    authority_score: Decimal = d("0.900000"),
    corroboration_score: Decimal = d("0.850000"),
    contradiction_score: Decimal = d("0.050000"),
    specialist_memory_confidence_score: Decimal = d("0.900000"),
    calibration_evidence_score: Decimal = d("0.800000"),
    unresolved_caveat_score: Decimal = d("0.050000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceConfidenceMemoryBridgeObservation(
        triage_group=triage_group,
        evidence_family_label=evidence_family_label,
        specialist_label=specialist_label,
        observed_at=GENERATED_AT - timedelta(seconds=observed_seconds_ago),
        authority_score=authority_score,
        corroboration_score=corroboration_score,
        contradiction_score=contradiction_score,
        specialist_memory_confidence_score=specialist_memory_confidence_score,
        calibration_evidence_score=calibration_evidence_score,
        unresolved_caveat_score=unresolved_caveat_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_confidence_memory_bridge_report(
        rows,
        config=cfg,
        generated_at=GENERATED_AT,
    )


def test_pass_row_bridges_source_and_memory_confidence() -> None:
    module = api()
    report = build_report(observation())

    assert type(report) is module.ResearchSourceConfidenceMemoryBridgeReport
    assert is_dataclass(report)
    assert report.status == "pass"
    assert report.observation_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.reason_codes == ("source_confidence_memory_bridge_report_clear",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    row = report.rows[0]
    assert row.status == "pass"
    assert row.reason_codes == ("source_confidence_memory_bridge_clear",)
    assert row.observation_age_seconds == d("600.000000")
    assert row.freshness_score == d("1.000000")
    assert row.source_confidence_score == d("0.925000")
    assert row.memory_confidence_score == d("0.883333")
    assert row.bridge_confidence_score == d("0.904166")
    assert row.triage_pressure_score == d("0.109167")
    assert report.average_source_confidence_score == d("0.925000")
    assert report.average_memory_confidence_score == d("0.883333")
    assert report.average_bridge_confidence_score == d("0.904166")
    assert report.lowest_bridge_confidence_score == d("0.904166")
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    assert (
        report.derived_validation_digest
        == module.research_source_confidence_memory_bridge_report_digest(report)
    )
    module.validate_research_source_confidence_memory_bridge_report_digest(report)


def test_block_row_surfaces_all_confidence_memory_bridge_failures() -> None:
    report = build_report(
        observation(
            "event.cluster.beta",
            evidence_family_label="thin.social",
            specialist_label="sports.desk",
            observed_seconds_ago=7200,
            authority_score=d("0.300000"),
            corroboration_score=d("0.400000"),
            contradiction_score=d("0.700000"),
            specialist_memory_confidence_score=d("0.450000"),
            calibration_evidence_score=d("0.400000"),
            unresolved_caveat_score=d("0.400000"),
        ),
    )

    assert report.status == "block"
    assert report.block_count == d("1.000000")
    assert report.freshness_gap_count == d("1.000000")
    assert report.authority_gap_count == d("1.000000")
    assert report.corroboration_gap_count == d("1.000000")
    assert report.contradiction_gap_count == d("1.000000")
    assert report.calibration_evidence_gap_count == d("1.000000")
    assert report.unresolved_caveat_gap_count == d("1.000000")
    assert report.bridge_confidence_gap_count == d("1.000000")
    assert report.highest_contradiction_score == d("0.700000")
    assert report.highest_unresolved_caveat_score == d("0.400000")
    assert report.oldest_observation_age_seconds == d("7200.000000")
    assert report.reason_codes == (
        "source_confidence_memory_bridge_block_present",
        "freshness_gap_present",
        "authority_gap_present",
        "corroboration_gap_present",
        "contradiction_gap_present",
        "calibration_evidence_gap_present",
        "unresolved_caveats_present",
        "bridge_confidence_gap_present",
    )

    row = report.rows[0]
    assert row.freshness_score == d("0.000000")
    assert row.source_confidence_score == d("0.250000")
    assert row.memory_confidence_score == d("0.483333")
    assert row.bridge_confidence_score == d("0.366666")
    assert row.triage_pressure_score == d("0.586667")
    assert row.reason_codes == (
        "freshness_block",
        "authority_block",
        "corroboration_block",
        "contradiction_block",
        "calibration_evidence_block",
        "unresolved_caveats_block",
        "bridge_confidence_block",
    )


def test_watch_thresholds_are_statused_without_blocking() -> None:
    report = build_report(
        observation(
            "event.cluster.gamma",
            observed_seconds_ago=4500,
            authority_score=d("0.550000"),
            corroboration_score=d("0.550000"),
            contradiction_score=d("0.200000"),
            specialist_memory_confidence_score=d("0.700000"),
            calibration_evidence_score=d("0.600000"),
            unresolved_caveat_score=d("0.200000"),
        ),
    )

    assert report.status == "watch"
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("0.000000")
    assert report.reason_codes == (
        "source_confidence_memory_bridge_watch_present",
        "freshness_gap_present",
        "authority_gap_present",
        "corroboration_gap_present",
        "contradiction_gap_present",
        "calibration_evidence_gap_present",
        "unresolved_caveats_present",
        "bridge_confidence_gap_present",
    )
    assert report.rows[0].status == "watch"
    assert report.rows[0].freshness_score == d("0.500000")
    assert report.rows[0].bridge_confidence_score == d("0.650000")
    assert report.rows[0].reason_codes == (
        "freshness_watch",
        "authority_watch",
        "corroboration_watch",
        "contradiction_watch",
        "calibration_evidence_watch",
        "unresolved_caveats_watch",
        "bridge_confidence_watch",
    )


def test_payload_digest_are_deterministic_json_ready_and_public_safe() -> None:
    module = api()
    report_a = build_report(
        observation("event.cluster.safe_a"),
        observation(
            "event.cluster.safe_b",
            evidence_family_label="independent.archive",
            specialist_label="policy.desk",
            observed_seconds_ago=7200,
            authority_score=d("0.300000"),
            corroboration_score=d("0.400000"),
            contradiction_score=d("0.700000"),
            specialist_memory_confidence_score=d("0.450000"),
            calibration_evidence_score=d("0.400000"),
            unresolved_caveat_score=d("0.400000"),
        ),
    )
    report_b = build_report(
        observation(
            "event.cluster.safe_b",
            evidence_family_label="independent.archive",
            specialist_label="policy.desk",
            observed_seconds_ago=7200,
            authority_score=d("0.300000"),
            corroboration_score=d("0.400000"),
            contradiction_score=d("0.700000"),
            specialist_memory_confidence_score=d("0.450000"),
            calibration_evidence_score=d("0.400000"),
            unresolved_caveat_score=d("0.400000"),
        ),
        observation("event.cluster.safe_a"),
    )

    payload_a = module.research_source_confidence_memory_bridge_report_payload(report_a)
    payload_b = report_b.payload
    digest_a = module.research_source_confidence_memory_bridge_report_digest(report_a)
    digest_b = module.research_source_confidence_memory_bridge_report_digest(report_b)

    assert payload_a == payload_b
    assert digest_a == digest_b
    assert payload_a["derived_validation_digest"] == digest_a
    assert len(digest_a) == 64
    int(digest_a, 16)
    assert payload_a["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload_a["observation_count"] == "2.000000"
    assert payload_a["rows"][0]["triage_pressure_score"] >= payload_a["rows"][1][
        "triage_pressure_score"
    ]
    json.dumps(payload_a, sort_keys=True)
    assert_no_decimal_or_float_values(payload_a)
    assert_payload_has_no_leaked_values(payload_a)

    unsafe_keys = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_id",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
    }
    keys = {field.name for cls in (type(report_a), type(report_a.rows[0])) for field in fields(cls)}
    assert unsafe_keys.isdisjoint(keys)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)


def test_validation_rejects_non_decimal_dates_flags_statuses_and_unsafe_labels() -> None:
    module = api()

    with pytest.raises(ValueError, match="fresh_age_seconds must be a Decimal"):
        module.ResearchSourceConfidenceMemoryBridgeConfig(
            fresh_age_seconds=_DecimalSubclass("1800.000000"),
        )
    with pytest.raises(ValueError, match="authority_score must be a Decimal"):
        observation(authority_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="contradiction_score must be a Decimal"):
        observation(contradiction_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fresh_age_seconds must be positive"):
        module.ResearchSourceConfidenceMemoryBridgeConfig(
            fresh_age_seconds=d("0.000000"),
        )
    with pytest.raises(ValueError, match="public label"):
        observation("https://unsafe.example/path")
    with pytest.raises(ValueError, match="contains unsafe text"):
        observation("candidate.alpha")
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_confidence_memory_bridge_report(
            (),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        module.ResearchSourceConfidenceMemoryBridgeObservation(
            triage_group="event.cluster.alpha",
            evidence_family_label="official.filing",
            specialist_label="macro.desk",
            observed_at=datetime(2026, 7, 8, 11, 0),
            authority_score=d("0.900000"),
            corroboration_score=d("0.850000"),
            contradiction_score=d("0.050000"),
            specialist_memory_confidence_score=d("0.900000"),
            calibration_evidence_score=d("0.800000"),
            unresolved_caveat_score=d("0.050000"),
        )
    with pytest.raises(ValueError, match="observed_at must not be in the future"):
        build_report(observation(observed_seconds_ago=-1))
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        observation(readonly=False)

    report = build_report(observation())
    with pytest.raises(ValueError, match="status"):
        replace(report, status="ready")
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="clear")


def test_empty_report_exports_frozen_dataclasses_and_status_vocabulary() -> None:
    module = api()
    report = build_report()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_CONFIDENCE_MEMORY_BRIDGE_REPORT_CONFIG_VERSION",
        "RESEARCH_SOURCE_CONFIDENCE_MEMORY_BRIDGE_STATUSES",
        "ResearchSourceConfidenceMemoryBridgeConfig",
        "ResearchSourceConfidenceMemoryBridgeObservation",
        "ResearchSourceConfidenceMemoryBridgeReport",
        "ResearchSourceConfidenceMemoryBridgeRow",
        "build_research_source_confidence_memory_bridge_report",
        "research_source_confidence_memory_bridge_report_digest",
        "research_source_confidence_memory_bridge_report_payload",
        "validate_research_source_confidence_memory_bridge_report_digest",
    )
    assert module.RESEARCH_SOURCE_CONFIDENCE_MEMORY_BRIDGE_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert report.status == "pass"
    assert report.observation_count == d("0.000000")
    assert report.reason_codes == ("source_confidence_memory_bridge_empty",)
    assert report.rows == ()
    assert report.derived_validation_digest == module.research_source_confidence_memory_bridge_report_digest(report)
    assert is_dataclass(module.ResearchSourceConfidenceMemoryBridgeConfig())
    assert is_dataclass(observation())
    assert is_dataclass(report)

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        module.ResearchSourceConfidenceMemoryBridgeConfig().fresh_age_seconds = d(
            "1.000000",
        )

    with pytest.raises(TypeError):

        class BadConfig(module.ResearchSourceConfidenceMemoryBridgeConfig):
            pass


def test_module_scope_is_report_only_and_has_no_live_surface_imports_or_calls() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
                "send",
                "trade",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def assert_no_decimal_or_float_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_decimal_or_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_decimal_or_float_values(item)
    else:
        assert type(value) is not Decimal
        assert type(value) is not float


def assert_payload_has_no_leaked_values(value: object) -> None:
    forbidden_fragments = (
        "http://",
        "https://",
        "postgres://",
        "candidate-",
        "candidate",
        "market-",
        "market",
        "token",
        "wallet",
        "order",
        "trade",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
    )
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)
