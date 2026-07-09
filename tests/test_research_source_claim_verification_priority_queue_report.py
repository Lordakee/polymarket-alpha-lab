from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_source_claim_verification_priority_queue_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_claim_verification_priority_queue_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            "research-source-claim-verification-priority-queue-report-v0"
        ),
        "max_source_age_seconds": d("86400.000000"),
        "deadline_priority_window_seconds": d("172800.000000"),
        "component_watch_threshold": d("0.500000"),
        "component_block_threshold": d("0.800000"),
        "priority_watch_threshold": d("0.350000"),
        "priority_block_threshold": d("0.700000"),
        "authority_weight": d("0.180000"),
        "freshness_weight": d("0.160000"),
        "contradiction_weight": d("0.240000"),
        "extraction_confidence_weight": d("0.120000"),
        "corroboration_gap_weight": d("0.160000"),
        "deadline_proximity_weight": d("0.140000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchSourceClaimVerificationPriorityQueueConfig(**values)


def observation(
    claim_label: str,
    *,
    source_family_label: str = "official_reporting",
    resolution_bucket: str = "macro_policy",
    source_observed_at: datetime = GENERATED_AT - timedelta(hours=2),
    resolution_deadline_at: datetime = GENERATED_AT + timedelta(hours=1),
    source_authority_score: Decimal = d("0.950000"),
    extraction_confidence_score: Decimal = d("0.300000"),
    contradiction_severity: Decimal = d("0.900000"),
    corroborating_source_count: Decimal = d("0.000000"),
    required_corroborating_source_count: Decimal = d("3.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceClaimVerificationPriorityQueueObservation(
        claim_label=claim_label,
        source_family_label=source_family_label,
        resolution_bucket=resolution_bucket,
        source_observed_at=source_observed_at,
        resolution_deadline_at=resolution_deadline_at,
        source_authority_score=source_authority_score,
        extraction_confidence_score=extraction_confidence_score,
        contradiction_severity=contradiction_severity,
        corroborating_source_count=corroborating_source_count,
        required_corroborating_source_count=required_corroborating_source_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def sample_observations() -> tuple[Any, ...]:
    return (
        observation("verify-watch",
            source_family_label="specialist_notes",
            resolution_bucket="sports_roster",
            source_observed_at=GENERATED_AT - timedelta(hours=12),
            resolution_deadline_at=GENERATED_AT + timedelta(hours=24),
            source_authority_score=d("0.600000"),
            extraction_confidence_score=d("0.600000"),
            contradiction_severity=d("0.400000"),
            corroborating_source_count=d("1.000000"),
            required_corroborating_source_count=d("3.000000"),
        ),
        observation("verify-pass",
            source_family_label="summary_digest",
            resolution_bucket="general_context",
            source_observed_at=GENERATED_AT - timedelta(hours=1),
            resolution_deadline_at=GENERATED_AT + timedelta(hours=96),
            source_authority_score=d("0.200000"),
            extraction_confidence_score=d("0.950000"),
            contradiction_severity=d("0.100000"),
            corroborating_source_count=d("2.000000"),
            required_corroborating_source_count=d("2.000000"),
        ),
        observation("verify-block"),
    )


def report(
    observations: tuple[Any, ...] | None = None,
    *,
    generated_at: datetime = GENERATED_AT,
    config: object | None = None,
) -> Any:
    module = api()
    return module.build_research_source_claim_verification_priority_queue_report(
        sample_observations() if observations is None else observations,
        generated_at=generated_at,
        config=config or cfg(),
    )


def assert_public_payload_is_json_scalar_only(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_public_payload_is_json_scalar_only(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_public_payload_is_json_scalar_only(item)
        return
    assert type(value) not in (Decimal, float, int, datetime)


def assert_no_raw_surface(value: object) -> None:
    forbidden_key_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
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
        "live",
    )
    forbidden_value_fragments = (
        "://",
        "www.",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            for fragment in forbidden_key_fragments:
                assert fragment not in lowered_key, key
            assert_no_raw_surface(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_raw_surface(item)
        return
    if isinstance(value, str):
        lowered_value = value.lower()
        for fragment in forbidden_value_fragments:
            assert fragment not in lowered_value, value


def test_prioritizes_claim_verification_queue() -> None:
    built = report()

    assert is_dataclass(built)
    assert built.status == "block"
    assert built.claim_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.average_verification_priority_score == d("0.454250")
    assert built.max_verification_priority_score == d("0.781417")
    assert built.average_source_authority_score == d("0.583333")
    assert built.average_freshness_score == d("0.208333")
    assert built.average_contradiction_severity == d("0.466667")
    assert built.average_extraction_confidence_score == d("0.616667")
    assert built.average_corroboration_gap_score == d("0.555556")
    assert built.average_deadline_proximity_score == d("0.493056")

    assert tuple(row.claim_label for row in built.rows) == (
        "verify-block",
        "verify-watch",
        "verify-pass",
    )
    assert tuple(row.priority_rank for row in built.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.verification_status for row in built.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert built.rows[0].source_age_seconds == d("7200.000000")
    assert built.rows[0].freshness_score == d("0.083333")
    assert built.rows[0].extraction_uncertainty_score == d("0.700000")
    assert built.rows[0].corroboration_gap_score == d("1.000000")
    assert built.rows[0].deadline_proximity_score == d("0.979167")
    assert built.rows[0].verification_priority_score == d("0.781417")
    assert "claim_verification_priority_block" in built.rows[0].reason_codes
    assert built.rows[-1].reason_codes == (
        "source_claim_verification_priority_pass",
    )
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True


def test_public_payload_is_deterministic_validated_and_redacted() -> None:
    module = api()
    built = report()

    payload = module.research_source_claim_verification_priority_queue_report_payload(
        built,
    )
    assert tuple(payload) == module.PUBLIC_REPORT_PAYLOAD_FIELDS
    assert_public_payload_is_json_scalar_only(payload)
    assert_no_raw_surface(payload)
    assert payload["derived_validation_digest"] == built.derived_validation_digest
    assert (
        module.research_source_claim_verification_priority_queue_report_digest(built)
        == built.derived_validation_digest
    )

    encoded_once = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    encoded_twice = json.dumps(
        module.research_source_claim_verification_priority_queue_report_payload(built),
        sort_keys=True,
        separators=(",", ":"),
    )
    assert encoded_once == encoded_twice

    tampered = dict(payload)
    tampered["status"] = "pass"
    assert (
        module.validate_research_source_claim_verification_priority_queue_public_payload(
            tampered,
        )
        is False
    )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_source_claim_verification_priority_queue_report_payload(
            tampered,
        )


def test_empty_report_passes_with_decimal_zero_summaries() -> None:
    built = report(())

    assert built.status == "pass"
    assert built.claim_count == d("0.000000")
    assert built.pass_count == d("0.000000")
    assert built.watch_count == d("0.000000")
    assert built.block_count == d("0.000000")
    assert built.average_verification_priority_score == d("0.000000")
    assert built.max_verification_priority_score == d("0.000000")
    assert built.rows == ()
    assert built.reason_codes == ("source_claim_verification_priority_pass",)


def test_dataclasses_are_frozen_and_validate_exact_decimal_inputs() -> None:
    module = api()
    built = report()

    with pytest.raises(FrozenInstanceError):
        built.status = "pass"

    for item in (cfg(), sample_observations()[0], built.rows[0], built):
        assert is_dataclass(item)
        assert all(field.init for field in fields(item))

    with pytest.raises(ValueError, match="Decimal"):
        observation("bad-decimal", source_authority_score=0)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="subclassing"):
        type(
            "DerivedConfig",
            (module.ResearchSourceClaimVerificationPriorityQueueConfig,),
            {},
        )


def test_rejects_unsafe_public_surfaces_and_non_report_inputs() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public"):
        observation("https://example.com/raw-claim")
    with pytest.raises(ValueError, match="unsafe public"):
        observation("market_slug")
    with pytest.raises(ValueError, match="unsafe public"):
        observation("123456789012345678901234567890")
    with pytest.raises(ValueError, match="unsafe public"):
        observation("will-team-win-title-2026")
    with pytest.raises(ValueError, match="paper_only"):
        observation("unsafe-flags", paper_only=False)
    with pytest.raises(ValueError, match="iterable"):
        module.build_research_source_claim_verification_priority_queue_report(
            "not-observations",
            generated_at=GENERATED_AT,
            config=cfg(),
        )
    with pytest.raises(ValueError, match="Observation"):
        module.build_research_source_claim_verification_priority_queue_report(
            [object()],
            generated_at=GENERATED_AT,
            config=cfg(),
        )


def test_module_imports_no_db_network_scraping_or_live_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_import_roots = {
        "asyncpg",
        "boto3",
        "bs4",
        "httpx",
        "os",
        "psycopg",
        "psycopg2",
        "requests",
        "scrapy",
        "selenium",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    forbidden_name_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
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
        "live",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_import_roots
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            lowered = node.name.lower()
            for fragment in forbidden_name_fragments:
                assert fragment not in lowered, node.name
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float
