from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_source_resolution_signal_quorum_drift_report"
GENERATED_AT = datetime(2026, 7, 8, 15, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "min_authoritative_source_count": d("1.000000"),
        "min_total_source_count": d("3.000000"),
        "min_corroborating_source_count": d("3.000000"),
        "freshness_watch_lag_seconds": d("3600.000000"),
        "freshness_block_lag_seconds": d("7200.000000"),
        "contradiction_watch_pressure": d("0.300000"),
        "contradiction_block_pressure": d("0.600000"),
        "extraction_confidence_watch_floor": d("0.700000"),
        "extraction_confidence_block_floor": d("0.400000"),
        "pass_quorum_signal_score": d("0.750000"),
        "watch_quorum_signal_score": d("0.450000"),
        "authority_mix_weight": d("0.250000"),
        "freshness_weight": d("0.200000"),
        "corroboration_breadth_weight": d("0.200000"),
        "contradiction_pressure_weight": d("0.200000"),
        "extraction_confidence_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchSourceResolutionSignalQuorumDriftConfig(**values)


def signal_item(
    analyst_bucket: str,
    *,
    authoritative_source_count: Decimal = d("1.000000"),
    supporting_source_count: Decimal = d("2.000000"),
    corroborating_source_count: Decimal = d("3.000000"),
    freshness_lag_seconds: Decimal = d("900.000000"),
    contradiction_pressure_score: Decimal = d("0.050000"),
    extraction_confidence_score: Decimal = d("0.950000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceResolutionSignalQuorumDriftInput(
        analyst_bucket=analyst_bucket,
        authoritative_source_count=authoritative_source_count,
        supporting_source_count=supporting_source_count,
        corroborating_source_count=corroborating_source_count,
        freshness_lag_seconds=freshness_lag_seconds,
        contradiction_pressure_score=contradiction_pressure_score,
        extraction_confidence_score=extraction_confidence_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_resolution_signal_quorum_drift_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_quorum_drift_scores_authority_freshness_breadth_contradiction_confidence() -> None:
    module = api()
    report = build_report(
        signal_item("official_consensus"),
        signal_item(
            "community_crosscheck",
            authoritative_source_count=d("1.000000"),
            supporting_source_count=d("1.000000"),
            corroborating_source_count=d("2.000000"),
            freshness_lag_seconds=d("4800.000000"),
            contradiction_pressure_score=d("0.350000"),
            extraction_confidence_score=d("0.650000"),
        ),
        signal_item(
            "contested_gap",
            authoritative_source_count=d("0.000000"),
            supporting_source_count=d("1.000000"),
            corroborating_source_count=d("0.000000"),
            freshness_lag_seconds=d("8000.000000"),
            contradiction_pressure_score=d("0.700000"),
            extraction_confidence_score=d("0.350000"),
        ),
    )

    assert type(report) is module.ResearchSourceResolutionSignalQuorumDriftReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.signal_count == d("3.000000")
    assert report.pass_signal_count == d("1.000000")
    assert report.watch_signal_count == d("1.000000")
    assert report.block_signal_count == d("1.000000")
    assert report.weak_authority_mix_count == d("2.000000")
    assert report.freshness_lag_count == d("2.000000")
    assert report.thin_corroboration_count == d("2.000000")
    assert report.contradiction_pressure_count == d("2.000000")
    assert report.low_extraction_confidence_count == d("2.000000")
    assert report.lowest_quorum_signal_score == d("0.154167")
    assert report.highest_quorum_drift_score == d("0.845833")
    assert report.highest_freshness_lag_seconds == d("8000.000000")
    assert report.highest_contradiction_pressure_score == d("0.700000")
    assert report.lowest_extraction_confidence_score == d("0.350000")
    assert tuple(row.analyst_bucket for row in report.rows) == (
        "contested_gap",
        "community_crosscheck",
        "official_consensus",
    )
    assert report.reason_codes == (
        "research_source_resolution_signal_quorum_drift_weak_authority_mix_block",
        "research_source_resolution_signal_quorum_drift_freshness_lag_block",
        "research_source_resolution_signal_quorum_drift_thin_corroboration_block",
        "research_source_resolution_signal_quorum_drift_contradiction_pressure_block",
        "research_source_resolution_signal_quorum_drift_low_extraction_confidence_block",
        "research_source_resolution_signal_quorum_drift_low_score_block",
        "research_source_resolution_signal_quorum_drift_weak_authority_mix_watch",
        "research_source_resolution_signal_quorum_drift_freshness_lag_watch",
        "research_source_resolution_signal_quorum_drift_thin_corroboration_watch",
        "research_source_resolution_signal_quorum_drift_contradiction_pressure_watch",
        "research_source_resolution_signal_quorum_drift_low_extraction_confidence_watch",
        "research_source_resolution_signal_quorum_drift_low_score_watch",
    )
    assert (
        "research_source_resolution_signal_quorum_drift_clear",
        d("1.000000"),
    ) in tuple((row.reason_code, row.count) for row in report.reason_code_counts)

    blocked = report.rows[0]
    assert blocked.status == "block"
    assert blocked.total_source_count == d("1.000000")
    assert blocked.source_authority_mix_score == d("0.166667")
    assert blocked.freshness_score == d("0.000000")
    assert blocked.corroboration_breadth_score == d("0.000000")
    assert blocked.contradiction_support_score == d("0.300000")
    assert blocked.extraction_confidence_support_score == d("0.350000")
    assert blocked.quorum_signal_score == d("0.154167")
    assert blocked.quorum_drift_score == d("0.845833")
    assert blocked.reason_codes == (
        "research_source_resolution_signal_quorum_drift_weak_authority_mix_block",
        "research_source_resolution_signal_quorum_drift_freshness_lag_block",
        "research_source_resolution_signal_quorum_drift_thin_corroboration_block",
        "research_source_resolution_signal_quorum_drift_contradiction_pressure_block",
        "research_source_resolution_signal_quorum_drift_low_extraction_confidence_block",
        "research_source_resolution_signal_quorum_drift_low_score_block",
    )

    watched = report.rows[1]
    assert watched.status == "watch"
    assert watched.source_authority_mix_score == d("0.833334")
    assert watched.freshness_score == d("0.666667")
    assert watched.corroboration_breadth_score == d("0.666667")
    assert watched.quorum_signal_score == d("0.702500")
    assert watched.quorum_drift_score == d("0.297500")

    passed = report.rows[2]
    assert passed.status == "pass"
    assert passed.quorum_signal_score == d("0.982500")
    assert passed.quorum_drift_score == d("0.017500")
    assert passed.reason_codes == ("research_source_resolution_signal_quorum_drift_clear",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_authority_freshness_and_extraction_thresholds_drive_statuses() -> None:
    exact_watch_boundary = build_report(
        signal_item("fresh_boundary", freshness_lag_seconds=d("3600.000000")),
    ).rows[0]
    exact_block_boundary = build_report(
        signal_item("stale_boundary", freshness_lag_seconds=d("7200.000000")),
    ).rows[0]
    missing_authority = build_report(
        signal_item("authority_gap", authoritative_source_count=d("0.000000")),
    ).rows[0]
    weak_extraction = build_report(
        signal_item("weak_extraction", extraction_confidence_score=d("0.650000")),
    ).rows[0]
    failed_extraction = build_report(
        signal_item("failed_extraction", extraction_confidence_score=d("0.350000")),
    ).rows[0]

    assert exact_watch_boundary.status == "pass"
    assert exact_block_boundary.status == "block"
    assert missing_authority.status == "block"
    assert weak_extraction.status == "watch"
    assert failed_extraction.status == "block"
    assert (
        "research_source_resolution_signal_quorum_drift_low_extraction_confidence_watch"
        in weak_extraction.reason_codes
    )
    assert (
        "research_source_resolution_signal_quorum_drift_low_extraction_confidence_block"
        in failed_extraction.reason_codes
    )


def test_public_payload_digest_is_deterministic_json_ready_and_tamper_checked() -> None:
    module = api()
    report_a = build_report(
        signal_item("official_consensus"),
        signal_item(
            "contested_gap",
            authoritative_source_count=d("0.000000"),
            supporting_source_count=d("1.000000"),
            corroborating_source_count=d("0.000000"),
            freshness_lag_seconds=d("8000.000000"),
            contradiction_pressure_score=d("0.700000"),
            extraction_confidence_score=d("0.350000"),
        ),
    )
    report_b = build_report(
        signal_item(
            "contested_gap",
            authoritative_source_count=d("0.000000"),
            supporting_source_count=d("1.000000"),
            corroborating_source_count=d("0.000000"),
            freshness_lag_seconds=d("8000.000000"),
            contradiction_pressure_score=d("0.700000"),
            extraction_confidence_score=d("0.350000"),
        ),
        signal_item("official_consensus"),
    )

    payload_a = module.research_source_resolution_signal_quorum_drift_report_payload(report_a)
    payload_b = module.research_source_resolution_signal_quorum_drift_report_payload(report_b)
    digest_a = module.research_source_resolution_signal_quorum_drift_report_digest(report_a)
    digest_b = module.research_source_resolution_signal_quorum_drift_report_digest(report_b)

    assert payload_a == payload_b
    assert digest_a == digest_b
    assert payload_a["derived_validation_digest"] == digest_a
    assert payload_a["derived_validation_digest"] == canonical_digest(payload_a)
    assert len(digest_a) == 64
    int(digest_a, 16)
    assert payload_a["generated_at"] == "2026-07-08T15:30:00+00:00"
    assert payload_a["signal_count"] == "2.000000"
    assert payload_a["rows"][0]["quorum_drift_score"] == "0.845833"
    json.dumps(payload_a, sort_keys=True, allow_nan=False)
    assert_no_public_numeric_values(payload_a)
    assert_payload_has_no_leaked_values(payload_a)
    module.validate_research_source_resolution_signal_quorum_drift_report_digest(report_a)
    module.validate_research_source_resolution_signal_quorum_drift_public_payload(payload_a)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)
    tampered = dict(payload_a)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_source_resolution_signal_quorum_drift_public_payload(tampered)


def test_public_payload_rejects_digest_consistent_semantic_and_flag_tampering() -> None:
    module = api()
    payload = module.research_source_resolution_signal_quorum_drift_report_payload(
        build_report(signal_item("official_consensus")),
    )

    aggregate_tampered = {**payload, "signal_count": "2.000000"}
    aggregate_tampered["derived_validation_digest"] = canonical_digest(
        aggregate_tampered,
    )
    with pytest.raises(ValueError, match="signal_count"):
        module.validate_research_source_resolution_signal_quorum_drift_public_payload(
            aggregate_tampered,
        )

    nested_flag_tampered = {
        **payload,
        "rows": [{**payload["rows"][0], "readonly": False}],
    }
    nested_flag_tampered["derived_validation_digest"] = canonical_digest(
        nested_flag_tampered,
    )
    with pytest.raises(ValueError, match="readonly"):
        module.validate_research_source_resolution_signal_quorum_drift_public_payload(
            nested_flag_tampered,
        )


def test_public_payload_prevents_identifier_source_secret_and_trading_leaks() -> None:
    module = api()
    report = build_report(signal_item("official_consensus"))
    payload = module.research_source_resolution_signal_quorum_drift_report_payload(report)
    unsafe_keys = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "live_surface",
        "recommendation",
    }
    keys = {
        field.name
        for cls in (type(signal_item("official_consensus")), type(report), type(report.rows[0]))
        for field in fields(cls)
    }

    assert unsafe_keys.isdisjoint(keys)
    assert_payload_has_no_leaked_values(payload)

    for unsafe_value in (
        "candidate-123",
        "market_slug",
        "https://example.invalid/source",
        "source_text",
        "wallet_token",
        "live_order_surface",
    ):
        with pytest.raises(ValueError, match="unsafe text"):
            signal_item(unsafe_value)

    for unsafe_payload in (
        {"candidate_id": "safe"},
        {"safe": "https://example.invalid/source"},
        {"safe": "wallet token"},
        {"safe": "live order trade recommendation"},
        {"table_name": "public_summary"},
    ):
        with pytest.raises(ValueError, match="public payload"):
            module.validate_research_source_resolution_signal_quorum_drift_public_payload(
                {
                    **payload,
                    **unsafe_payload,
                    "derived_validation_digest": payload["derived_validation_digest"],
                },
            )


def test_input_and_report_invariants_reject_invalid_or_duplicate_data() -> None:
    with pytest.raises(ValueError, match="authoritative_source_count"):
        signal_item(
            "fractional_count",
            authoritative_source_count=d("0.500000"),
        )
    with pytest.raises(ValueError, match="extraction_confidence_score"):
        signal_item(
            "non_finite_confidence",
            extraction_confidence_score=d("NaN"),
        )
    with pytest.raises(ValueError, match="analyst_bucket"):
        build_report(
            signal_item("duplicate_bucket"),
            signal_item("duplicate_bucket", supporting_source_count=d("1.000000")),
        )

    report = build_report(signal_item("official_consensus"))
    with pytest.raises(ValueError, match="signal_count"):
        replace(report, signal_count=d("2.000000"))


def test_custom_config_validation_flags_and_frozen_dataclasses() -> None:
    module = api()
    loose_config = config(
        min_total_source_count=d("2.000000"),
        min_corroborating_source_count=d("2.000000"),
        freshness_watch_lag_seconds=d("6000.000000"),
        freshness_block_lag_seconds=d("9000.000000"),
        contradiction_watch_pressure=d("0.500000"),
        contradiction_block_pressure=d("0.800000"),
        extraction_confidence_watch_floor=d("0.600000"),
        extraction_confidence_block_floor=d("0.300000"),
        pass_quorum_signal_score=d("0.650000"),
        watch_quorum_signal_score=d("0.300000"),
    )
    report = build_report(
        signal_item(
            "community_crosscheck",
            authoritative_source_count=d("1.000000"),
            supporting_source_count=d("1.000000"),
            corroborating_source_count=d("2.000000"),
            freshness_lag_seconds=d("4800.000000"),
            contradiction_pressure_score=d("0.350000"),
            extraction_confidence_score=d("0.650000"),
        ),
        cfg=loose_config,
    )

    assert report.status == "pass"
    assert report.rows[0].status == "pass"
    assert report.rows[0].reason_codes == (
        "research_source_resolution_signal_quorum_drift_clear",
    )

    with pytest.raises(ValueError, match="authority_mix_weight"):
        config(authority_mix_weight=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="min_total_source_count"):
        config(min_total_source_count=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="weights must sum"):
        config(extraction_confidence_weight=d("0.100000"))
    with pytest.raises(ValueError, match="pass_quorum_signal_score"):
        config(pass_quorum_signal_score=d("0.300000"))
    with pytest.raises(ValueError, match="freshness_watch_lag_seconds"):
        config(freshness_watch_lag_seconds=d("7200.000000"))
    with pytest.raises(ValueError, match="extraction_confidence_block_floor"):
        config(extraction_confidence_block_floor=d("0.800000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        signal_item("official_consensus", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        signal_item("official_consensus", readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_source_resolution_signal_quorum_drift_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 8, 15, 30),
        )

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_RESOLUTION_SIGNAL_QUORUM_DRIFT_REPORT_CONFIG_VERSION",
        "RESEARCH_SOURCE_RESOLUTION_SIGNAL_QUORUM_DRIFT_STATUSES",
        "ResearchSourceResolutionSignalQuorumDriftConfig",
        "ResearchSourceResolutionSignalQuorumDriftInput",
        "ResearchSourceResolutionSignalQuorumDriftReasonCodeCount",
        "ResearchSourceResolutionSignalQuorumDriftReport",
        "ResearchSourceResolutionSignalQuorumDriftRow",
        "build_research_source_resolution_signal_quorum_drift_report",
        "research_source_resolution_signal_quorum_drift_report_digest",
        "research_source_resolution_signal_quorum_drift_report_payload",
        "validate_research_source_resolution_signal_quorum_drift_public_payload",
        "validate_research_source_resolution_signal_quorum_drift_report_digest",
    )
    assert is_dataclass(config())
    assert is_dataclass(signal_item("official_consensus"))
    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().extraction_confidence_weight = d("0.100000")
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="block")


def test_module_scope_is_pure_report_only_without_external_surfaces() -> None:
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
                "submit_order",
                "place_order",
                "recommend",
                "size_position",
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


def assert_no_public_numeric_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric_values(item)
    else:
        assert type(value) is not float
        assert type(value) is not int


def assert_payload_has_no_leaked_values(value: object) -> None:
    forbidden_fragments = (
        "http://",
        "https://",
        "postgres://",
        "mysql://",
        "jdbc:",
        "candidate-",
        "candidate_id",
        "market-",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "token",
        "wallet",
        "order",
        "trade",
        "live_surface",
        "recommendation",
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
