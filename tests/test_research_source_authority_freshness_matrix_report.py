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
        "polymarket_alpha_lab.research_source_authority_freshness_matrix_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "fresh_update_age_seconds": d("900.000000"),
        "fresh_age_seconds": d("3600.000000"),
        "stale_age_seconds": d("7200.000000"),
        "high_source_rank_threshold": d("0.800000"),
        "low_source_rank_threshold": d("0.500000"),
        "critical_low_source_rank_threshold": d("0.300000"),
        "independence_watch_threshold": d("0.700000"),
        "independence_block_threshold": d("0.500000"),
        "contradiction_watch_threshold": d("0.300000"),
        "contradiction_block_threshold": d("0.600000"),
    }
    values.update(overrides)
    return module.ResearchSourceAuthorityFreshnessMatrixConfig(**values)


def evidence(
    source_family: str,
    *,
    observed_seconds_ago: int = 1200,
    source_rank_score: Decimal = d("0.750000"),
    independence_score: Decimal = d("0.850000"),
    contradiction_risk_score: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceAuthorityFreshnessMatrixInput(
        source_family=source_family,
        evidence_observed_at=GENERATED_AT - timedelta(seconds=observed_seconds_ago),
        source_rank_score=source_rank_score,
        independence_score=independence_score,
        contradiction_risk_score=contradiction_risk_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_authority_freshness_matrix_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def test_empty_report_is_pass_readonly_digest_validated_and_decimal_only() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourceAuthorityFreshnessMatrixReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.source_family_count == d("0.000000")
    assert report.evidence_count == d("0.000000")
    assert report.pass_source_family_count == d("0.000000")
    assert report.watch_source_family_count == d("0.000000")
    assert report.block_source_family_count == d("0.000000")
    assert report.stale_high_source_rank_count == d("0.000000")
    assert report.low_source_rank_fast_update_count == d("0.000000")
    assert report.low_independence_count == d("0.000000")
    assert report.contradiction_risk_count == d("0.000000")
    assert report.highest_matrix_risk_score == d("0.000000")
    assert report.oldest_latest_evidence_age_seconds == d("0.000000")
    assert report.lowest_average_source_rank_score == d("0.000000")
    assert report.lowest_average_independence_score == d("0.000000")
    assert report.highest_contradiction_risk_score == d("0.000000")
    assert report.reason_codes == ("research_source_authority_freshness_matrix_empty",)
    assert report.rows == ()
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    assert report.derived_validation_digest == module.research_source_authority_freshness_matrix_report_digest(report)
    module.validate_research_source_authority_freshness_matrix_report_digest(report)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_matrix_highlights_stale_high_rank_fast_low_rank_and_contradictions() -> None:
    report = build_report(
        evidence(
            "official.statistics",
            observed_seconds_ago=10800,
            source_rank_score=d("0.900000"),
            independence_score=d("0.900000"),
            contradiction_risk_score=d("0.200000"),
        ),
        evidence(
            "social.fast",
            observed_seconds_ago=300,
            source_rank_score=d("0.250000"),
            independence_score=d("0.400000"),
            contradiction_risk_score=d("0.750000"),
        ),
        evidence("wire.confirmed"),
    )

    assert report.status == "block"
    assert report.source_family_count == d("3.000000")
    assert report.evidence_count == d("3.000000")
    assert report.pass_source_family_count == d("1.000000")
    assert report.watch_source_family_count == d("0.000000")
    assert report.block_source_family_count == d("2.000000")
    assert report.stale_high_source_rank_count == d("1.000000")
    assert report.low_source_rank_fast_update_count == d("1.000000")
    assert report.low_independence_count == d("1.000000")
    assert report.contradiction_risk_count == d("1.000000")
    assert report.highest_matrix_risk_score == d("0.495000")
    assert report.oldest_latest_evidence_age_seconds == d("10800.000000")
    assert report.lowest_average_source_rank_score == d("0.250000")
    assert report.lowest_average_independence_score == d("0.400000")
    assert report.highest_contradiction_risk_score == d("0.750000")
    assert report.reason_codes == (
        "stale_high_source_rank_block",
        "low_source_rank_fast_update_block",
        "low_independence_block",
        "contradiction_risk_block",
    )

    assert tuple(row.source_family for row in report.rows) == (
        "social.fast",
        "official.statistics",
        "wire.confirmed",
    )

    fast_low_rank = report.rows[0]
    assert fast_low_rank.status == "block"
    assert fast_low_rank.source_rank_band == "low"
    assert fast_low_rank.freshness_band == "fast"
    assert fast_low_rank.independence_band == "low"
    assert fast_low_rank.latest_evidence_age_seconds == d("300.000000")
    assert fast_low_rank.average_source_rank_score == d("0.250000")
    assert fast_low_rank.average_independence_score == d("0.400000")
    assert fast_low_rank.contradiction_risk_score == d("0.750000")
    assert fast_low_rank.matrix_risk_score == d("0.495000")
    assert fast_low_rank.reason_codes == (
        "low_source_rank_fast_update_block",
        "low_independence_block",
        "contradiction_risk_block",
    )

    stale_high_rank = report.rows[1]
    assert stale_high_rank.status == "block"
    assert stale_high_rank.source_rank_band == "high"
    assert stale_high_rank.freshness_band == "stale"
    assert stale_high_rank.independence_band == "independent"
    assert stale_high_rank.matrix_risk_score == d("0.340000")
    assert stale_high_rank.reason_codes == ("stale_high_source_rank_block",)

    passed = report.rows[2]
    assert passed.status == "pass"
    assert passed.source_rank_band == "medium"
    assert passed.freshness_band == "current"
    assert passed.independence_band == "independent"
    assert passed.matrix_risk_score == d("0.055000")
    assert passed.reason_codes == ("source_authority_freshness_matrix_balanced",)


def test_watch_thresholds_are_statused_without_blocking() -> None:
    report = build_report(
        evidence(
            "agency.filing",
            observed_seconds_ago=5400,
            source_rank_score=d("0.850000"),
            independence_score=d("0.650000"),
            contradiction_risk_score=d("0.350000"),
        ),
    )

    assert report.status == "watch"
    assert report.watch_source_family_count == d("1.000000")
    assert report.block_source_family_count == d("0.000000")
    assert report.reason_codes == (
        "stale_high_source_rank_watch",
        "low_independence_watch",
        "contradiction_risk_watch",
    )
    assert report.rows[0].status == "watch"
    assert report.rows[0].freshness_band == "aging"
    assert report.rows[0].reason_codes == report.reason_codes


def test_payload_and_digest_are_deterministic_json_ready_and_public_safe() -> None:
    module = api()
    report_a = build_report(
        evidence("wire.confirmed"),
        evidence(
            "social.fast",
            observed_seconds_ago=300,
            source_rank_score=d("0.250000"),
            independence_score=d("0.400000"),
            contradiction_risk_score=d("0.750000"),
        ),
    )
    report_b = build_report(
        evidence(
            "social.fast",
            observed_seconds_ago=300,
            source_rank_score=d("0.250000"),
            independence_score=d("0.400000"),
            contradiction_risk_score=d("0.750000"),
        ),
        evidence("wire.confirmed"),
    )

    payload_a = module.research_source_authority_freshness_matrix_report_payload(report_a)
    payload_b = module.research_source_authority_freshness_matrix_report_payload(report_b)
    digest_a = module.research_source_authority_freshness_matrix_report_digest(report_a)
    digest_b = module.research_source_authority_freshness_matrix_report_digest(report_b)

    assert payload_a == payload_b
    assert digest_a == digest_b
    assert payload_a["derived_validation_digest"] == digest_a
    assert len(digest_a) == 64
    int(digest_a, 16)
    assert payload_a["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload_a["source_family_count"] == "2.000000"
    assert payload_a["rows"][0]["matrix_risk_score"] >= payload_a["rows"][1][
        "matrix_risk_score"
    ]
    json.dumps(payload_a, sort_keys=True)
    assert_no_float_values(payload_a)

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
    assert_payload_has_no_leaked_values(payload_a)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)


def test_validation_rejects_public_numeric_non_decimals_dates_flags_and_statuses() -> None:
    module = api()

    with pytest.raises(ValueError, match="fresh_age_seconds must be a Decimal"):
        config(fresh_age_seconds=_DecimalSubclass("3600.000000"))
    with pytest.raises(ValueError, match="source_rank_score must be a Decimal"):
        evidence("wire.confirmed", source_rank_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="contradiction_risk_score must be a Decimal"):
        evidence("wire.confirmed", contradiction_risk_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fresh_update_age_seconds must be positive"):
        config(fresh_update_age_seconds=d("0.000000"))
    with pytest.raises(ValueError, match="source_family contains unsafe text"):
        evidence("http://source.example/path")
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_authority_freshness_matrix_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="evidence_observed_at must be timezone-aware"):
        module.ResearchSourceAuthorityFreshnessMatrixInput(
            source_family="wire.confirmed",
            evidence_observed_at=datetime(2026, 7, 8, 11, 0),
            source_rank_score=d("0.750000"),
            independence_score=d("0.850000"),
            contradiction_risk_score=d("0.100000"),
        )
    with pytest.raises(ValueError, match="evidence_observed_at must not be in the future"):
        build_report(evidence("wire.confirmed", observed_seconds_ago=-1))
    with pytest.raises(ValueError, match="paper_only"):
        evidence("wire.confirmed", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        evidence("wire.confirmed", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        evidence("wire.confirmed", readonly=False)

    report = build_report(evidence("wire.confirmed"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="clear")
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="ready")


def test_exports_frozen_dataclasses_and_status_vocabulary() -> None:
    module = api()
    report = build_report(evidence("wire.confirmed"))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_AUTHORITY_FRESHNESS_MATRIX_REPORT_CONFIG_VERSION",
        "RESEARCH_SOURCE_AUTHORITY_FRESHNESS_MATRIX_STATUSES",
        "ResearchSourceAuthorityFreshnessMatrixConfig",
        "ResearchSourceAuthorityFreshnessMatrixInput",
        "ResearchSourceAuthorityFreshnessMatrixReport",
        "ResearchSourceAuthorityFreshnessMatrixRow",
        "build_research_source_authority_freshness_matrix_report",
        "research_source_authority_freshness_matrix_report_digest",
        "research_source_authority_freshness_matrix_report_payload",
        "validate_research_source_authority_freshness_matrix_report_digest",
    )
    assert module.RESEARCH_SOURCE_AUTHORITY_FRESHNESS_MATRIX_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert is_dataclass(config())
    assert is_dataclass(evidence("wire.confirmed"))
    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().fresh_age_seconds = d("1.000000")


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
