from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import ast
import inspect
import json
from typing import Any

import pytest

import polymarket_alpha_lab.team_specialist_source_diversity_score as api
from polymarket_alpha_lab.team_specialist_source_diversity_score import (
    TeamSpecialistSourceDiversityScoreConfig,
    TeamSpecialistSourceDiversityScoreInput,
    TeamSpecialistSourceDiversityScoreReasonCodeCount,
    TeamSpecialistSourceDiversityScoreReport,
    TeamSpecialistSourceDiversityScoreRow,
    build_team_specialist_source_diversity_score_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def source_input(
    team_id: str = "team_alpha",
    specialist_id: str = "specialist_a",
    topic_id: str = "topic_macro",
    *,
    required_source_type_count: Decimal = d("4.000000"),
    observed_source_type_count: Decimal = d("4.000000"),
    primary_source_type_share: Decimal = d("0.350000"),
    independent_source_type_ratio: Decimal = d("0.900000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> TeamSpecialistSourceDiversityScoreInput:
    return TeamSpecialistSourceDiversityScoreInput(
        team_id=team_id,
        specialist_id=specialist_id,
        topic_id=topic_id,
        required_source_type_count=required_source_type_count,
        observed_source_type_count=observed_source_type_count,
        primary_source_type_share=primary_source_type_share,
        independent_source_type_ratio=independent_source_type_ratio,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: TeamSpecialistSourceDiversityScoreInput,
    generated_at: datetime = NOW,
    config: TeamSpecialistSourceDiversityScoreConfig | None = None,
) -> TeamSpecialistSourceDiversityScoreReport:
    return build_team_specialist_source_diversity_score_report(
        rows,
        generated_at=generated_at,
        config=config,
    )


def test_diverse_source_types_pass_with_decimal_rollups() -> None:
    result = report(source_input())

    assert result.report_status == "pass"
    assert result.item_count == d("1.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("0.000000")
    assert result.block_count == d("0.000000")
    assert result.average_diversity_score == d("0.875000")
    assert result.minimum_diversity_score == d("0.875000")
    assert result.reason_code_counts == (
        TeamSpecialistSourceDiversityScoreReasonCodeCount(
            reason_code="team_specialist_source_diversity_pass",
            count=d("1.000000"),
        ),
    )

    row = result.rows[0]
    assert row.rank == d("1.000000")
    assert row.team_id == "team_alpha"
    assert row.specialist_id == "specialist_a"
    assert row.topic_id == "topic_macro"
    assert row.source_type_coverage_ratio == d("1.000000")
    assert row.concentration_spread_score == d("0.650000")
    assert row.diversity_score == d("0.875000")
    assert row.status == "pass"
    assert row.reason_codes == ("team_specialist_source_diversity_pass",)
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_partial_type_coverage_and_concentration_watch() -> None:
    result = report(
        source_input(
            observed_source_type_count=d("3.000000"),
            primary_source_type_share=d("0.650000"),
            independent_source_type_ratio=d("0.800000"),
        ),
    )

    row = result.rows[0]
    assert row.source_type_coverage_ratio == d("0.750000")
    assert row.concentration_spread_score == d("0.350000")
    assert row.diversity_score == d("0.640000")
    assert row.status == "watch"
    assert row.reason_codes == (
        "insufficient_source_type_coverage",
        "high_primary_source_type_concentration",
    )
    assert result.report_status == "watch"
    assert result.watch_count == d("1.000000")


def test_single_source_type_overfit_blocks() -> None:
    result = report(
        source_input(
            observed_source_type_count=d("1.000000"),
            primary_source_type_share=d("1.000000"),
            independent_source_type_ratio=d("0.000000"),
        ),
    )

    row = result.rows[0]
    assert row.source_type_coverage_ratio == d("0.250000")
    assert row.concentration_spread_score == d("0.000000")
    assert row.diversity_score == d("0.125000")
    assert row.status == "block"
    assert row.reason_codes == (
        "single_source_type_block",
        "insufficient_source_type_coverage",
        "high_primary_source_type_concentration",
        "low_source_type_independence",
        "source_diversity_score_block",
    )
    assert result.report_status == "block"
    assert result.block_count == d("1.000000")


def test_decimal_exact_type_rejection() -> None:
    with pytest.raises(ValueError, match="required_source_type_count must be a Decimal"):
        source_input(required_source_type_count=4)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_source_type_count must be a Decimal"):
        source_input(observed_source_type_count=DecimalSubclass("4.000000"))
    with pytest.raises(ValueError, match="primary_source_type_share must be a Decimal"):
        source_input(primary_source_type_share=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="independent_source_type_ratio"):
        source_input(independent_source_type_ratio=d("0.3333333"))
    with pytest.raises(ValueError, match="primary_source_type_share"):
        source_input(primary_source_type_share=d("1.000001"))


def test_public_payload_rejects_leaks_and_unsafe_public_terms() -> None:
    forbidden_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        for fragment in forbidden_fragments:
            assert fragment not in lowered

    for cls in (
        TeamSpecialistSourceDiversityScoreConfig,
        TeamSpecialistSourceDiversityScoreInput,
        TeamSpecialistSourceDiversityScoreReasonCodeCount,
        TeamSpecialistSourceDiversityScoreRow,
        TeamSpecialistSourceDiversityScoreReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            for fragment in forbidden_fragments:
                assert fragment not in lowered

    payload = report(source_input()).payload
    payload_text = json.dumps(payload, sort_keys=True).lower()
    for fragment in forbidden_fragments:
        assert fragment not in payload_text

    unsafe_values = (
        "candidate_alpha",
        "market_alpha",
        "market_slug_alpha",
        "will_rate_cut_question",
        "https://example.invalid/source",
        "source_ref_alpha",
        "source_text_alpha",
        "postgres_dsn_alpha",
        "table_name_alpha",
        "token_alpha",
        "wallet_auth_alpha",
        "order_trade_alpha",
        "position_sizing_alpha",
        "buy_signal_alpha",
        "sell_signal_alpha",
        "recommendation_alpha",
    )
    for unsafe_value in unsafe_values:
        with pytest.raises(ValueError, match="unsafe public"):
            source_input(team_id=unsafe_value)


def test_hard_flags_and_frozen_dataclasses_are_enforced() -> None:
    result = report(source_input())
    values = (
        TeamSpecialistSourceDiversityScoreConfig(),
        source_input(),
        result.reason_code_counts[0],
        result.rows[0],
        result,
    )

    for value in values:
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        TeamSpecialistSourceDiversityScoreConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        source_input(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result.rows[0], readonly=False)


def test_payload_is_deterministic_and_json_safe() -> None:
    first = report(
        source_input("team_b", "specialist_b", "topic_b"),
        source_input("team_a", "specialist_a", "topic_a"),
    )
    second = report(
        source_input("team_a", "specialist_a", "topic_a"),
        source_input("team_b", "specialist_b", "topic_b"),
    )

    assert tuple((row.team_id, row.specialist_id, row.topic_id) for row in first.rows) == (
        ("team_a", "specialist_a", "topic_a"),
        ("team_b", "specialist_b", "topic_b"),
    )
    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert api.team_specialist_source_diversity_score_payload(first) == first.payload
    json.dumps(first.payload, sort_keys=True)
    _assert_no_decimal_objects(first.payload)
    _assert_no_non_decimal_public_numbers(first)


def test_report_and_digest_consistency_rejects_tampering() -> None:
    result = report(
        source_input("team_pass", "specialist_a", "topic_a"),
        source_input(
            "team_watch",
            "specialist_b",
            "topic_b",
            observed_source_type_count=d("3.000000"),
            primary_source_type_share=d("0.650000"),
            independent_source_type_ratio=d("0.800000"),
        ),
        source_input(
            "team_block",
            "specialist_c",
            "topic_c",
            observed_source_type_count=d("1.000000"),
            primary_source_type_share=d("1.000000"),
            independent_source_type_ratio=d("0.000000"),
        ),
    )

    assert result.report_status == "block"
    assert result.item_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.payload["derived_validation_digest"] == result.derived_validation_digest

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_count"):
        replace(
            result,
            pass_count=d("2.000000"),
            derived_validation_digest=result.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="rows"):
        replace(result, rows=tuple(reversed(result.rows)))


def test_module_has_no_io_network_persistence_or_trading_surface() -> None:
    source = inspect.getsource(api)
    tree = ast.parse(source)
    forbidden_import_roots = {
        "boto3",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "commit",
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "urlopen",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls

    lowered = source.lower()
    for token in (
        "account",
        "balance",
        "cancel",
        "clob",
        "database",
        "db_write",
        "live trading",
        "private_key",
        "submit",
        "wallet",
    ):
        assert token not in lowered


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public dataclass contains non-Decimal number: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
