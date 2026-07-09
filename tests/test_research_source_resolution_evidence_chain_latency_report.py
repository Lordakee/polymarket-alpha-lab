from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_resolution_evidence_chain_latency_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "chain_latency_watch_seconds": d("3600.000000"),
        "chain_latency_block_seconds": d("7200.000000"),
        "authority_ack_watch_seconds": d("1800.000000"),
        "authority_ack_block_seconds": d("3600.000000"),
        "resolution_sync_watch_seconds": d("1800.000000"),
        "resolution_sync_block_seconds": d("5400.000000"),
        "min_chain_step_count": d("3.000000"),
        "block_chain_step_count": d("1.000000"),
        "manual_handoff_watch_count": d("1.000000"),
        "manual_handoff_block_count": d("2.000000"),
    }
    values.update(overrides)
    return module.ResearchSourceResolutionEvidenceChainLatencyConfig(**values)


def evidence(
    resolution_cluster: str,
    evidence_chain_family: str,
    *,
    first_seconds_ago: int = 1800,
    latest_seconds_ago: int = 1200,
    authority_ack_seconds_ago: int = 600,
    ready_seconds_ago: int = 300,
    chain_step_count: Decimal = d("3.000000"),
    pending_manual_handoff_count: Decimal = d("0.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceResolutionEvidenceChainLatencyInput(
        resolution_cluster=resolution_cluster,
        evidence_chain_family=evidence_chain_family,
        first_evidence_observed_at=GENERATED_AT - timedelta(seconds=first_seconds_ago),
        latest_evidence_observed_at=GENERATED_AT - timedelta(seconds=latest_seconds_ago),
        authority_acknowledged_at=GENERATED_AT - timedelta(seconds=authority_ack_seconds_ago),
        resolution_ready_at=GENERATED_AT - timedelta(seconds=ready_seconds_ago),
        chain_step_count=chain_step_count,
        pending_manual_handoff_count=pending_manual_handoff_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_resolution_evidence_chain_latency_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def test_latency_report_blocks_slow_evidence_resolution_chains() -> None:
    report = build_report(
        evidence(
            "settlement.criteria",
            "official.feed",
            first_seconds_ago=10800,
            latest_seconds_ago=7200,
            authority_ack_seconds_ago=3000,
            ready_seconds_ago=600,
            chain_step_count=d("1.000000"),
            pending_manual_handoff_count=d("2.000000"),
        ),
        evidence(
            "settlement.criteria",
            "archive.feed",
            first_seconds_ago=9000,
            latest_seconds_ago=6000,
            authority_ack_seconds_ago=2400,
            ready_seconds_ago=600,
            chain_step_count=d("2.000000"),
            pending_manual_handoff_count=d("0.000000"),
        ),
        evidence("verification.criteria", "official.feed"),
    )

    assert report.status == "block"
    assert report.resolution_cluster_count == d("2.000000")
    assert report.evidence_chain_count == d("3.000000")
    assert report.pass_resolution_cluster_count == d("1.000000")
    assert report.watch_resolution_cluster_count == d("0.000000")
    assert report.block_resolution_cluster_count == d("1.000000")
    assert report.chain_latency_breach_count == d("1.000000")
    assert report.authority_ack_latency_breach_count == d("1.000000")
    assert report.resolution_sync_latency_breach_count == d("1.000000")
    assert report.low_chain_depth_count == d("1.000000")
    assert report.manual_handoff_latency_count == d("1.000000")
    assert report.highest_latency_pressure_score == d("0.822222")
    assert report.slowest_chain_latency_seconds == d("10200.000000")
    assert report.reason_codes == (
        "evidence_chain_latency_block",
        "authority_ack_latency_block",
        "resolution_sync_latency_watch",
        "low_evidence_chain_depth_block",
        "manual_handoff_latency_block",
    )

    assert tuple(row.resolution_cluster for row in report.rows) == (
        "settlement.criteria",
        "verification.criteria",
    )

    blocked = report.rows[0]
    assert blocked.status == "block"
    assert blocked.evidence_chain_count == d("2.000000")
    assert blocked.evidence_chain_family_count == d("2.000000")
    assert blocked.maximum_chain_latency_seconds == d("10200.000000")
    assert blocked.average_chain_latency_seconds == d("9300.000000")
    assert blocked.maximum_authority_ack_latency_seconds == d("4200.000000")
    assert blocked.maximum_resolution_sync_latency_seconds == d("2400.000000")
    assert blocked.minimum_chain_step_count == d("1.000000")
    assert blocked.pending_manual_handoff_count == d("2.000000")
    assert blocked.latency_pressure_score == d("0.822222")
    assert blocked.reason_codes == report.reason_codes

    passed = report.rows[1]
    assert passed.status == "pass"
    assert passed.reason_codes == ("evidence_chain_latency_clear",)
    assert passed.latency_pressure_score == d("0.086111")
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True


def test_watch_thresholds_report_latency_pressure_without_blocking() -> None:
    report = build_report(
        evidence(
            "weather.criteria",
            "official.bulletin",
            first_seconds_ago=5400,
            latest_seconds_ago=3900,
            authority_ack_seconds_ago=1800,
            ready_seconds_ago=300,
            chain_step_count=d("2.000000"),
            pending_manual_handoff_count=d("1.000000"),
        ),
    )

    assert report.status == "watch"
    assert report.watch_resolution_cluster_count == d("1.000000")
    assert report.block_resolution_cluster_count == d("0.000000")
    assert report.reason_codes == (
        "evidence_chain_latency_watch",
        "authority_ack_latency_watch",
        "low_evidence_chain_depth_watch",
        "manual_handoff_latency_watch",
    )
    assert report.rows[0].status == "watch"
    assert report.rows[0].reason_codes == report.reason_codes
    assert report.rows[0].latency_pressure_score == d("0.480555")


def test_empty_input_returns_block_report_only_digest() -> None:
    module = api()
    report = build_report()
    payload = module.research_source_resolution_evidence_chain_latency_report_payload(
        report,
    )

    assert report.status == "block"
    assert report.reason_codes == (
        "research_source_resolution_evidence_chain_latency_empty",
    )
    assert report.resolution_cluster_count == d("0.000000")
    assert report.evidence_chain_count == d("0.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert_no_float_values(payload)


def test_payload_digest_is_deterministic_decimal_string_only_and_public_safe() -> None:
    module = api()
    report_a = build_report(
        evidence("verification.criteria", "official.feed"),
        evidence(
            "settlement.criteria",
            "official.feed",
            first_seconds_ago=10800,
            latest_seconds_ago=7200,
            authority_ack_seconds_ago=3000,
            ready_seconds_ago=600,
            chain_step_count=d("1.000000"),
            pending_manual_handoff_count=d("2.000000"),
        ),
    )
    report_b = build_report(
        evidence(
            "settlement.criteria",
            "official.feed",
            first_seconds_ago=10800,
            latest_seconds_ago=7200,
            authority_ack_seconds_ago=3000,
            ready_seconds_ago=600,
            chain_step_count=d("1.000000"),
            pending_manual_handoff_count=d("2.000000"),
        ),
        evidence("verification.criteria", "official.feed"),
    )

    payload_a = module.research_source_resolution_evidence_chain_latency_report_payload(
        report_a,
    )
    payload_b = module.research_source_resolution_evidence_chain_latency_report_payload(
        report_b,
    )
    digest_a = module.research_source_resolution_evidence_chain_latency_report_digest(
        report_a,
    )
    digest_b = module.research_source_resolution_evidence_chain_latency_report_digest(
        report_b,
    )

    assert payload_a == payload_b
    assert digest_a == digest_b
    assert payload_a["derived_validation_digest"] == digest_a
    assert payload_a["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload_a["resolution_cluster_count"] == "2.000000"
    assert payload_a["rows"][0]["latency_pressure_score"] >= payload_a["rows"][1][
        "latency_pressure_score"
    ]
    assert len(digest_a) == 64
    int(digest_a, 16)
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
        "live_url",
    }
    keys = {field.name for cls in (type(report_a), type(report_a.rows[0])) for field in fields(cls)}
    assert unsafe_keys.isdisjoint(keys)
    assert_payload_has_no_leaked_values(payload_a)
    module.validate_research_source_resolution_evidence_chain_latency_report_digest(
        report_a,
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)


def test_public_payload_uses_exact_schema_and_canonical_sha256_digest() -> None:
    module = api()
    report = build_report(evidence("settlement.criteria", "official.feed"))
    payload = module.research_source_resolution_evidence_chain_latency_report_payload(
        report,
    )

    assert tuple(payload) == (
        "generated_at",
        "config_version",
        "resolution_cluster_count",
        "evidence_chain_count",
        "pass_resolution_cluster_count",
        "watch_resolution_cluster_count",
        "block_resolution_cluster_count",
        "chain_latency_breach_count",
        "authority_ack_latency_breach_count",
        "resolution_sync_latency_breach_count",
        "low_chain_depth_count",
        "manual_handoff_latency_count",
        "highest_latency_pressure_score",
        "slowest_chain_latency_seconds",
        "status",
        "reason_codes",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(payload["rows"][0]) == (
        "resolution_cluster",
        "evidence_chain_count",
        "evidence_chain_family_count",
        "maximum_chain_latency_seconds",
        "average_chain_latency_seconds",
        "maximum_authority_ack_latency_seconds",
        "maximum_resolution_sync_latency_seconds",
        "minimum_chain_step_count",
        "pending_manual_handoff_count",
        "latency_pressure_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    )

    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    expected_digest = hashlib.sha256(
        json.dumps(
            digest_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8"),
    ).hexdigest()
    assert report.derived_validation_digest == expected_digest


def test_public_payload_rejects_serializer_schema_and_numeric_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = api()
    original = module.json_ready_no_floats

    def with_extra_report_field(value: object) -> object:
        payload = original(value)
        if type(payload) is dict and "generated_at" in payload and "rows" in payload:
            payload = dict(payload)
            payload["unexpected_field"] = "unexpected"
        return payload

    monkeypatch.setattr(module, "json_ready_no_floats", with_extra_report_field)
    with pytest.raises(ValueError, match="public payload schema"):
        build_report(evidence("settlement.criteria", "official.feed"))

    def with_missing_digest_field(value: object) -> object:
        payload = original(value)
        if type(payload) is dict and "derived_validation_digest" in payload:
            payload = dict(payload)
            payload.pop("derived_validation_digest")
        return payload

    monkeypatch.setattr(module, "json_ready_no_floats", with_missing_digest_field)
    with pytest.raises(ValueError, match="public payload schema"):
        build_report(evidence("settlement.criteria", "official.feed"))

    def with_missing_row_field(value: object) -> object:
        payload = original(value)
        if type(payload) is dict and payload.get("rows"):
            payload = dict(payload)
            rows = [dict(row) for row in payload["rows"]]
            rows[0].pop("status")
            payload["rows"] = rows
        return payload

    monkeypatch.setattr(module, "json_ready_no_floats", with_missing_row_field)
    with pytest.raises(ValueError, match="public payload schema"):
        build_report(evidence("settlement.criteria", "official.feed"))

    def with_numeric_count(value: object) -> object:
        payload = original(value)
        if type(payload) is dict and "resolution_cluster_count" in payload:
            payload = dict(payload)
            payload["resolution_cluster_count"] = 1
        return payload

    monkeypatch.setattr(module, "json_ready_no_floats", with_numeric_count)
    with pytest.raises(ValueError, match="public payload schema"):
        build_report(evidence("settlement.criteria", "official.feed"))


def test_count_fields_are_whole_scores_are_bounded_and_zero_is_canonical() -> None:
    report = build_report(evidence("settlement.criteria", "official.feed"))

    with pytest.raises(ValueError, match="chain_step_count must be a whole Decimal"):
        evidence(
            "settlement.criteria",
            "official.feed",
            chain_step_count=d("1.500000"),
        )
    with pytest.raises(
        ValueError,
        match="pending_manual_handoff_count must be a whole Decimal",
    ):
        evidence(
            "settlement.criteria",
            "official.feed",
            pending_manual_handoff_count=d("0.500000"),
        )
    with pytest.raises(
        ValueError,
        match="evidence_chain_count must be a whole Decimal",
    ):
        replace(report.rows[0], evidence_chain_count=d("1.500000"))
    with pytest.raises(
        ValueError,
        match="evidence_chain_family_count must not exceed evidence_chain_count",
    ):
        replace(report.rows[0], evidence_chain_family_count=d("2.000000"))
    with pytest.raises(ValueError, match="latency_pressure_score must not exceed 1"):
        replace(report.rows[0], latency_pressure_score=d("1.000001"))

    normalized = replace(
        report.rows[0],
        pending_manual_handoff_count=d("-0.000000"),
    )
    assert normalized.pending_manual_handoff_count == d("0.000000")
    assert str(normalized.pending_manual_handoff_count) == "0.000000"


def test_validation_flags_statuses_decimal_only_and_safe_scope() -> None:
    module = api()

    with pytest.raises(ValueError, match="chain_latency_watch_seconds must be a Decimal"):
        config(chain_latency_watch_seconds=_DecimalSubclass("3600.000000"))
    with pytest.raises(ValueError, match="chain_step_count must be a Decimal"):
        evidence("settlement.criteria", "official.feed", chain_step_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="pending_manual_handoff_count must be a Decimal"):
        evidence("settlement.criteria", "official.feed", pending_manual_handoff_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="resolution_cluster contains unsafe text"):
        evidence("market-question", "official.feed")
    with pytest.raises(ValueError, match="evidence_chain_family contains unsafe text"):
        evidence("settlement.criteria", "https://example.test/source")
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_resolution_evidence_chain_latency_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )
    with pytest.raises(ValueError, match="first_evidence_observed_at must not be in the future"):
        build_report(
            evidence(
                "settlement.criteria",
                "official.feed",
                first_seconds_ago=-100,
                latest_seconds_ago=-200,
                authority_ack_seconds_ago=-300,
                ready_seconds_ago=-400,
            ),
        )
    with pytest.raises(ValueError, match="latency timestamps must be monotonic"):
        evidence(
            "settlement.criteria",
            "official.feed",
            first_seconds_ago=600,
            latest_seconds_ago=1200,
        )
    with pytest.raises(ValueError, match="paper_only"):
        evidence("settlement.criteria", "official.feed", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        evidence("settlement.criteria", "official.feed", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        evidence("settlement.criteria", "official.feed", readonly=False)

    report = build_report(evidence("settlement.criteria", "official.feed"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="ready")
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="blocked")


def test_exports_frozen_dataclasses_status_vocabulary_and_pure_report_scope() -> None:
    module = api()
    report = build_report(evidence("settlement.criteria", "official.feed"))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_RESOLUTION_EVIDENCE_CHAIN_LATENCY_REPORT_CONFIG_VERSION",
        "RESEARCH_SOURCE_RESOLUTION_EVIDENCE_CHAIN_LATENCY_REPORT_STATUSES",
        "ResearchSourceResolutionEvidenceChainLatencyConfig",
        "ResearchSourceResolutionEvidenceChainLatencyInput",
        "ResearchSourceResolutionEvidenceChainLatencyReport",
        "ResearchSourceResolutionEvidenceChainLatencyRow",
        "build_research_source_resolution_evidence_chain_latency_report",
        "research_source_resolution_evidence_chain_latency_report_digest",
        "research_source_resolution_evidence_chain_latency_report_payload",
        "validate_research_source_resolution_evidence_chain_latency_report_digest",
    )
    assert module.RESEARCH_SOURCE_RESOLUTION_EVIDENCE_CHAIN_LATENCY_REPORT_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert is_dataclass(config())
    assert is_dataclass(evidence("settlement.criteria", "official.feed"))
    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().chain_latency_watch_seconds = d("3000.000000")

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
                "commit",
                "connect",
                "cursor",
                "execute",
                "executemany",
                "mkdir",
                "open",
                "request",
                "post",
                "put",
                "patch",
                "save",
                "touch",
                "unlink",
                "write",
                "write_bytes",
                "write_text",
            }

    forbidden_import_fragments = (
        "boto",
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "redis",
        "requests",
        "scrap",
        "sqlalchemy",
        "sqlite",
        "socket",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    forbidden_surface_fragments = (
        "allocation",
        "execution",
        "notional",
        "order",
        "position_size",
        "recommend",
        "sizing",
        "trade",
        "wallet",
    )
    public_names = set(module.__all__)
    for value in (
        config(),
        evidence("settlement.criteria", "official.feed"),
        report,
        report.rows[0],
    ):
        public_names.update(field.name for field in fields(type(value)))
    assert not any(
        fragment in public_name.lower()
        for public_name in public_names
        for fragment in forbidden_surface_fragments
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
        "candidate_",
        "market-",
        "market_",
        "token",
        "wallet",
        "order",
        "trade",
        "question",
        "slug",
        "live",
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
