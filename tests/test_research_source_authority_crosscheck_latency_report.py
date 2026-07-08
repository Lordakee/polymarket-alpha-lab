from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_authority_crosscheck_latency_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "target_high_rank_latency_seconds": d("900.000000"),
        "max_high_rank_latency_seconds": d("1800.000000"),
        "freshness_watch_age_seconds": d("1800.000000"),
        "freshness_block_age_seconds": d("3600.000000"),
        "deadline_watch_seconds_remaining": d("1800.000000"),
        "deadline_block_seconds_remaining": d("600.000000"),
        "high_source_rank_threshold": d("0.800000"),
        "source_rank_watch_threshold": d("0.550000"),
        "source_rank_block_threshold": d("0.350000"),
        "corroboration_watch_threshold": d("0.600000"),
        "corroboration_block_threshold": d("0.400000"),
        "contradiction_watch_threshold": d("0.300000"),
        "contradiction_block_threshold": d("0.600000"),
    }
    values.update(overrides)
    return module.ResearchSourceAuthorityCrosscheckLatencyConfig(**values)


def crosscheck(
    source_family: str,
    *,
    source_rank_score: Decimal = d("0.800000"),
    crosscheck_latency_seconds: Decimal = d("600.000000"),
    corroboration_score: Decimal = d("0.900000"),
    contradiction_pressure_score: Decimal = d("0.100000"),
    evidence_freshness_seconds: Decimal = d("900.000000"),
    deadline_seconds_remaining: Decimal = d("3600.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceAuthorityCrosscheckLatencyInput(
        source_family=source_family,
        source_rank_score=source_rank_score,
        crosscheck_latency_seconds=crosscheck_latency_seconds,
        corroboration_score=corroboration_score,
        contradiction_pressure_score=contradiction_pressure_score,
        evidence_freshness_seconds=evidence_freshness_seconds,
        deadline_seconds_remaining=deadline_seconds_remaining,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_authority_crosscheck_latency_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def test_empty_report_is_pass_readonly_digest_validated_and_decimal_only() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourceAuthorityCrosscheckLatencyReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.source_family_count == d("0.000000")
    assert report.pass_source_family_count == d("0.000000")
    assert report.watch_source_family_count == d("0.000000")
    assert report.block_source_family_count == d("0.000000")
    assert report.low_source_rank_count == d("0.000000")
    assert report.late_high_rank_source_count == d("0.000000")
    assert report.thin_corroboration_source_count == d("0.000000")
    assert report.contradiction_pressure_source_count == d("0.000000")
    assert report.stale_crosscheck_source_count == d("0.000000")
    assert report.deadline_proximity_source_count == d("0.000000")
    assert report.highest_crosscheck_latency_risk_score == d("0.000000")
    assert report.slowest_crosscheck_latency_seconds == d("0.000000")
    assert report.lowest_source_rank_score == d("0.000000")
    assert report.lowest_corroboration_score == d("0.000000")
    assert report.highest_contradiction_pressure_score == d("0.000000")
    assert report.nearest_deadline_seconds_remaining == d("0.000000")
    assert report.reason_codes == ("research_source_authority_crosscheck_latency_empty",)
    assert report.rows == ()
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    assert (
        report.derived_validation_digest
        == module.research_source_authority_crosscheck_latency_report_digest(report)
    )
    module.validate_research_source_authority_crosscheck_latency_report_digest(report)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_latency_report_scores_authority_latency_freshness_and_deadline_pressure() -> None:
    report = build_report(
        crosscheck(
            "wire.confirmed",
            source_rank_score=d("0.800000"),
            crosscheck_latency_seconds=d("600.000000"),
            corroboration_score=d("0.900000"),
            contradiction_pressure_score=d("0.100000"),
            evidence_freshness_seconds=d("900.000000"),
            deadline_seconds_remaining=d("3600.000000"),
        ),
        crosscheck(
            "community.fast",
            source_rank_score=d("0.500000"),
            crosscheck_latency_seconds=d("1000.000000"),
            corroboration_score=d("0.550000"),
            contradiction_pressure_score=d("0.350000"),
            evidence_freshness_seconds=d("2400.000000"),
            deadline_seconds_remaining=d("1200.000000"),
        ),
        crosscheck(
            "official.filing",
            source_rank_score=d("0.950000"),
            crosscheck_latency_seconds=d("2400.000000"),
            corroboration_score=d("0.350000"),
            contradiction_pressure_score=d("0.700000"),
            evidence_freshness_seconds=d("4200.000000"),
            deadline_seconds_remaining=d("300.000000"),
        ),
    )

    assert report.status == "block"
    assert report.source_family_count == d("3.000000")
    assert report.pass_source_family_count == d("1.000000")
    assert report.watch_source_family_count == d("1.000000")
    assert report.block_source_family_count == d("1.000000")
    assert report.low_source_rank_count == d("1.000000")
    assert report.late_high_rank_source_count == d("1.000000")
    assert report.thin_corroboration_source_count == d("2.000000")
    assert report.contradiction_pressure_source_count == d("2.000000")
    assert report.stale_crosscheck_source_count == d("2.000000")
    assert report.deadline_proximity_source_count == d("2.000000")
    assert report.highest_crosscheck_latency_risk_score == d("0.670000")
    assert report.slowest_crosscheck_latency_seconds == d("2400.000000")
    assert report.lowest_source_rank_score == d("0.500000")
    assert report.lowest_corroboration_score == d("0.350000")
    assert report.highest_contradiction_pressure_score == d("0.700000")
    assert report.nearest_deadline_seconds_remaining == d("300.000000")
    assert report.reason_codes == (
        "late_authoritative_crosscheck_block",
        "thin_corroboration_block",
        "contradiction_pressure_block",
        "stale_crosscheck_block",
        "deadline_proximity_block",
        "low_authority_watch",
        "thin_corroboration_watch",
        "contradiction_pressure_watch",
        "stale_crosscheck_watch",
        "deadline_proximity_watch",
    )

    assert tuple(row.source_family for row in report.rows) == (
        "official.filing",
        "community.fast",
        "wire.confirmed",
    )

    blocked = report.rows[0]
    assert blocked.status == "block"
    assert blocked.source_rank_band == "high"
    assert blocked.latency_band == "critical"
    assert blocked.freshness_band == "stale"
    assert blocked.deadline_proximity_band == "immediate"
    assert blocked.latency_pressure_score == d("0.975000")
    assert blocked.deadline_pressure_score == d("0.833333")
    assert blocked.crosscheck_latency_risk_score == d("0.670000")
    assert blocked.reason_codes == (
        "late_authoritative_crosscheck_block",
        "thin_corroboration_block",
        "contradiction_pressure_block",
        "stale_crosscheck_block",
        "deadline_proximity_block",
    )

    watched = report.rows[1]
    assert watched.status == "watch"
    assert watched.source_rank_band == "low"
    assert watched.latency_band == "late"
    assert watched.freshness_band == "aging"
    assert watched.deadline_proximity_band == "near"
    assert watched.latency_pressure_score == d("0.416667")
    assert watched.deadline_pressure_score == d("0.333333")
    assert watched.crosscheck_latency_risk_score == d("0.444583")
    assert watched.reason_codes == (
        "low_authority_watch",
        "thin_corroboration_watch",
        "contradiction_pressure_watch",
        "stale_crosscheck_watch",
        "deadline_proximity_watch",
    )

    passed = report.rows[2]
    assert passed.status == "pass"
    assert passed.source_rank_band == "high"
    assert passed.latency_band == "fast"
    assert passed.freshness_band == "fresh"
    assert passed.deadline_proximity_band == "open"
    assert passed.crosscheck_latency_risk_score == d("0.177500")
    assert passed.reason_codes == ("source_authority_crosscheck_latency_healthy",)


def test_watch_thresholds_are_statused_without_blocking() -> None:
    report = build_report(
        crosscheck(
            "filing.secondary",
            source_rank_score=d("0.500000"),
            crosscheck_latency_seconds=d("1000.000000"),
            corroboration_score=d("0.550000"),
            contradiction_pressure_score=d("0.350000"),
            evidence_freshness_seconds=d("2400.000000"),
            deadline_seconds_remaining=d("1200.000000"),
        ),
    )

    assert report.status == "watch"
    assert report.watch_source_family_count == d("1.000000")
    assert report.block_source_family_count == d("0.000000")
    assert report.reason_codes == (
        "low_authority_watch",
        "thin_corroboration_watch",
        "contradiction_pressure_watch",
        "stale_crosscheck_watch",
        "deadline_proximity_watch",
    )
    assert report.rows[0].status == "watch"
    assert report.rows[0].reason_codes == report.reason_codes


def test_payload_and_digest_are_deterministic_json_ready_and_public_safe() -> None:
    module = api()
    report_a = build_report(
        crosscheck("wire.confirmed"),
        crosscheck(
            "official.filing",
            source_rank_score=d("0.950000"),
            crosscheck_latency_seconds=d("2400.000000"),
            corroboration_score=d("0.350000"),
            contradiction_pressure_score=d("0.700000"),
            evidence_freshness_seconds=d("4200.000000"),
            deadline_seconds_remaining=d("300.000000"),
        ),
    )
    report_b = build_report(
        crosscheck(
            "official.filing",
            source_rank_score=d("0.950000"),
            crosscheck_latency_seconds=d("2400.000000"),
            corroboration_score=d("0.350000"),
            contradiction_pressure_score=d("0.700000"),
            evidence_freshness_seconds=d("4200.000000"),
            deadline_seconds_remaining=d("300.000000"),
        ),
        crosscheck("wire.confirmed"),
    )

    payload_a = module.research_source_authority_crosscheck_latency_report_payload(report_a)
    payload_b = module.research_source_authority_crosscheck_latency_report_payload(report_b)
    digest_a = module.research_source_authority_crosscheck_latency_report_digest(report_a)
    digest_b = module.research_source_authority_crosscheck_latency_report_digest(report_b)

    assert payload_a == payload_b
    assert digest_a == digest_b
    assert payload_a["derived_validation_digest"] == digest_a
    assert len(digest_a) == 64
    int(digest_a, 16)
    assert payload_a["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload_a["source_family_count"] == "2.000000"
    assert payload_a["rows"][0]["crosscheck_latency_risk_score"] >= payload_a["rows"][1][
        "crosscheck_latency_risk_score"
    ]
    json.dumps(payload_a, sort_keys=True)
    assert_no_float_values(payload_a)

    unsafe_keys = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "url",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "live_surface",
    }
    keys = {field.name for cls in (type(report_a), type(report_a.rows[0])) for field in fields(cls)}
    assert unsafe_keys.isdisjoint(keys)
    assert_payload_has_no_leaked_values(payload_a)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)


def test_validation_rejects_public_numeric_non_decimals_flags_and_statuses() -> None:
    module = api()

    with pytest.raises(ValueError, match="max_high_rank_latency_seconds must be a Decimal"):
        config(max_high_rank_latency_seconds=_DecimalSubclass("1800.000000"))
    with pytest.raises(ValueError, match="source_rank_score must be a Decimal"):
        crosscheck("wire.confirmed", source_rank_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="crosscheck_latency_seconds must be a Decimal"):
        crosscheck("wire.confirmed", crosscheck_latency_seconds=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="deadline_seconds_remaining must be nonnegative"):
        crosscheck("wire.confirmed", deadline_seconds_remaining=d("-1.000000"))
    with pytest.raises(ValueError, match="target_high_rank_latency_seconds must be positive"):
        config(target_high_rank_latency_seconds=d("0.000000"))
    with pytest.raises(ValueError, match="source_family contains unsafe text"):
        crosscheck("http://source.example/path")
    with pytest.raises(ValueError, match="source_family contains unsafe text"):
        crosscheck("market.slug")
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_authority_crosscheck_latency_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="paper_only"):
        crosscheck("wire.confirmed", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        crosscheck("wire.confirmed", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        crosscheck("wire.confirmed", readonly=False)

    report = build_report(crosscheck("wire.confirmed"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="clear")
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="ready")


def test_exports_frozen_dataclasses_and_status_vocabulary() -> None:
    module = api()
    report = build_report(crosscheck("wire.confirmed"))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_AUTHORITY_CROSSCHECK_LATENCY_REPORT_CONFIG_VERSION",
        "RESEARCH_SOURCE_AUTHORITY_CROSSCHECK_LATENCY_STATUSES",
        "ResearchSourceAuthorityCrosscheckLatencyConfig",
        "ResearchSourceAuthorityCrosscheckLatencyInput",
        "ResearchSourceAuthorityCrosscheckLatencyReport",
        "ResearchSourceAuthorityCrosscheckLatencyRow",
        "build_research_source_authority_crosscheck_latency_report",
        "research_source_authority_crosscheck_latency_report_digest",
        "research_source_authority_crosscheck_latency_report_payload",
        "validate_research_source_authority_crosscheck_latency_report_digest",
    )
    assert module.RESEARCH_SOURCE_AUTHORITY_CROSSCHECK_LATENCY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert is_dataclass(config())
    assert is_dataclass(crosscheck("wire.confirmed"))
    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().max_high_rank_latency_seconds = d("1.000000")


def test_module_scope_is_pure_public_safe_report_only() -> None:
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


def assert_no_float_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_values(item)
    else:
        assert type(value) is not float


def assert_payload_has_no_leaked_values(value: object) -> None:
    forbidden_fragments = (
        "http://",
        "https://",
        "postgres://",
        "candidate-",
        "market-",
        "token",
        "wallet",
        "order",
        "trade",
        "question",
        "table",
        "dsn",
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
