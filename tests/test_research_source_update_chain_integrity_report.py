from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_source_update_chain_integrity_report"
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(**overrides: object) -> Any:
    module = api()
    values = {
        "candidate_id": "cand-private-alpha",
        "market_id": "mkt-private-alpha",
        "market_slug": "will-private-market-update",
        "market_question": "Will this private question stay out of the payload?",
        "update_chain_id": "chain-public-alpha",
        "authority_family": "official_primary",
        "authority_sequence_position": d("1"),
        "expected_previous_update_count": d("0"),
        "observed_previous_update_count": d("0"),
        "expected_next_update_count": d("1"),
        "observed_next_update_count": d("1"),
        "previous_authority_family": None,
        "source_observed_at": GENERATED_AT - timedelta(hours=2),
        "contradiction_pressure": d("0.050000"),
        "extraction_confidence": d("0.950000"),
        "manual_verification_count": d("2"),
        "required_manual_verification_count": d("2"),
        "raw_source_url": "https://private.example/source?token=secret",
        "raw_source_text": "Private source text that must not be serialized.",
        "source_dsn": "postgres://token@private/db",
        "source_table_name": "private_source_updates",
    }
    values.update(overrides)
    return module.ResearchSourceUpdateChainObservation(**values)


def report(*items: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_update_chain_integrity_report(
        items,
        config=cfg or module.ResearchSourceUpdateChainIntegrityConfig(),
        generated_at=GENERATED_AT,
    )


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def assert_numeric_fields_are_decimal(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if type(item) is bool:
            continue
        assert type(item) is not float
        assert type(item) is not int
        if isinstance(item, tuple):
            for nested in item:
                if is_dataclass(nested):
                    assert_numeric_fields_are_decimal(nested)


def walk_payload(value: object) -> list[object]:
    items = [value]
    if isinstance(value, dict):
        for key, item in value.items():
            items.append(key)
            items.extend(walk_payload(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            items.extend(walk_payload(item))
    return items


def test_source_update_chain_integrity_scores_rows_deterministically() -> None:
    inputs = (
        observation(
            candidate_id="cand-pass",
            market_id="mkt-pass",
            market_slug="market-pass",
            update_chain_id="chain-pass",
            authority_family="official_primary",
            authority_sequence_position=d("1"),
            expected_previous_update_count=d("0"),
            observed_previous_update_count=d("0"),
            expected_next_update_count=d("1"),
            observed_next_update_count=d("1"),
            previous_authority_family=None,
            source_observed_at=GENERATED_AT - timedelta(hours=2),
            contradiction_pressure=d("0.050000"),
            extraction_confidence=d("0.950000"),
            manual_verification_count=d("2"),
            required_manual_verification_count=d("2"),
        ),
        observation(
            candidate_id="cand-watch",
            market_id="mkt-watch",
            market_slug="market-watch",
            update_chain_id="chain-watch",
            authority_family="official_primary",
            authority_sequence_position=d("2"),
            expected_previous_update_count=d("1"),
            observed_previous_update_count=d("0"),
            expected_next_update_count=d("1"),
            observed_next_update_count=d("1"),
            previous_authority_family="wire_secondary",
            source_observed_at=GENERATED_AT - timedelta(hours=30),
            contradiction_pressure=d("0.300000"),
            extraction_confidence=d("0.720000"),
            manual_verification_count=d("1"),
            required_manual_verification_count=d("2"),
        ),
        observation(
            candidate_id="cand-block",
            market_id="mkt-block",
            market_slug="market-block",
            update_chain_id="chain-block",
            authority_family="official_primary",
            authority_sequence_position=d("3"),
            expected_previous_update_count=d("2"),
            observed_previous_update_count=d("0"),
            expected_next_update_count=d("1"),
            observed_next_update_count=d("0"),
            previous_authority_family="community_summary",
            source_observed_at=GENERATED_AT - timedelta(hours=80),
            contradiction_pressure=d("0.850000"),
            extraction_confidence=d("0.450000"),
            manual_verification_count=d("0"),
            required_manual_verification_count=d("2"),
        ),
    )

    result = report(*inputs)

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "research-source-update-chain-integrity-report-v1"
    assert result.row_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.status == "block"
    assert result.incomplete_sequence_count == d("2")
    assert result.authority_break_count == d("2")
    assert result.stale_update_count == d("2")
    assert result.contradiction_pressure_count == d("2")
    assert result.low_extraction_confidence_count == d("2")
    assert result.manual_verification_gap_count == d("2")
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.validation_digest)
    assert_numeric_fields_are_decimal(result)

    assert tuple(row.update_chain_id for row in result.rows) == (
        "chain-block",
        "chain-watch",
        "chain-pass",
    )

    blocked = result.rows[0]
    assert blocked.sequence_completeness_ratio == d("0.333333")
    assert blocked.freshness_age_seconds == d("288000.000000")
    assert blocked.manual_verification_coverage_ratio == d("0.000000")
    assert blocked.integrity_score == d("0.353333")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "source_update_chain_block",
        "update_sequence_incomplete_block",
        "authority_continuity_broken_block",
        "source_update_stale_block",
        "contradiction_pressure_block",
        "extraction_confidence_block",
        "manual_verification_gap_block",
    )
    assert_digest(blocked.validation_digest)

    watched = result.rows[1]
    assert watched.sequence_completeness_ratio == d("0.500000")
    assert watched.authority_continuity_ratio == d("0.000000")
    assert watched.freshness_age_seconds == d("108000.000000")
    assert watched.manual_verification_coverage_ratio == d("0.500000")
    assert watched.integrity_score == d("0.634000")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "source_update_chain_watch",
        "update_sequence_incomplete_watch",
        "authority_continuity_broken_watch",
        "source_update_stale_watch",
        "contradiction_pressure_watch",
        "extraction_confidence_watch",
        "manual_verification_gap_watch",
    )

    passed = result.rows[2]
    assert passed.integrity_score == d("0.980000")
    assert passed.status == "pass"
    assert passed.reason_codes == ("source_update_chain_pass",)

    same_result = report(*reversed(inputs))
    assert same_result.validation_digest == result.validation_digest


def test_payload_redacts_private_surfaces_and_is_frozen_json() -> None:
    module = api()
    result = report(observation())
    payload = module.research_source_update_chain_integrity_report_payload(result)

    assert payload["status"] == "pass"
    assert payload["validation_digest"] == result.validation_digest
    with pytest.raises(TypeError, match="immutable"):
        payload["status"] = "block"
    with pytest.raises(TypeError, match="immutable"):
        payload["rows"].append({})

    serialized = json.dumps(payload, sort_keys=True)
    forbidden_names = (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "raw_source_url",
        "raw_source_text",
        "source_dsn",
        "source_table_name",
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
    for forbidden in forbidden_names:
        assert forbidden not in serialized
    for value in walk_payload(payload):
        if type(value) is str:
            assert value not in {
                "cand-private-alpha",
                "mkt-private-alpha",
                "will-private-market-update",
                "Will this private question stay out of the payload?",
                "https://private.example/source?token=secret",
                "Private source text that must not be serialized.",
                "postgres://token@private/db",
                "private_source_updates",
            }


def test_empty_report_is_report_only_blocked_and_digest_validated() -> None:
    result = report()

    assert result.row_count == d("0")
    assert result.status == "block"
    assert result.reason_codes == ("source_update_chain_empty_block",)
    assert result.rows == ()
    assert result.reason_code_counts[0].reason_code == "source_update_chain_empty_block"
    assert result.reason_code_counts[0].row_count == d("0")
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.validation_digest)

    with pytest.raises(ValueError, match="validation_digest does not match payload"):
        replace(result, validation_digest="0" * 64)


def test_dataclasses_are_frozen_decimal_only_and_validate_inputs() -> None:
    module = api()
    item = observation()
    with pytest.raises(FrozenInstanceError):
        item.update_chain_id = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="contradiction_pressure must be a Decimal"):
        observation(contradiction_pressure=0.1)
    with pytest.raises(ValueError, match="status must be one of: pass, watch, block"):
        replace(report(observation()).rows[0], status="empty")
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.ResearchSourceUpdateChainObservation(
            **{
                **item.__dict__,
                "paper_only": False,
            },
        )


def test_module_has_no_db_network_or_scraping_surfaces() -> None:
    module = api()
    source_path = Path(module.__file__)
    tree = ast.parse(source_path.read_text())
    forbidden_import_roots = {
        "asyncpg",
        "bs4",
        "httpx",
        "psycopg",
        "requests",
        "selenium",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "supabase",
        "urllib",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
