from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_collection_sla_priority_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "source_age_watch_seconds": d("3600.000000"),
        "source_age_block_seconds": d("7200.000000"),
        "reliability_watch_floor": d("0.800000"),
        "reliability_block_floor": d("0.600000"),
        "coverage_gap_watch_ratio": d("0.250000"),
        "coverage_gap_block_ratio": d("0.500000"),
        "catalyst_pressure_watch_ratio": d("0.500000"),
        "catalyst_pressure_block_ratio": d("0.850000"),
        "capacity_watch_ratio": d("0.750000"),
        "capacity_block_ratio": d("0.400000"),
    }
    values.update(overrides)
    return module.ResearchSourceCollectionSlaPriorityConfig(**values)


def input_row(
    team_id: str,
    category_id: str,
    *,
    collection_task_count: Decimal = d("1.000000"),
    aggregate_source_age_seconds: Decimal = d("900.000000"),
    reliability_score: Decimal = d("0.950000"),
    expected_source_count: Decimal = d("4.000000"),
    collected_source_count: Decimal = d("4.000000"),
    catalyst_pressure_ratio: Decimal = d("0.100000"),
    available_team_capacity_units: Decimal = d("4.000000"),
    required_team_capacity_units: Decimal = d("4.000000"),
) -> Any:
    module = api()
    return module.ResearchSourceCollectionSlaPriorityInput(
        team_id=team_id,
        category_id=category_id,
        collection_task_count=collection_task_count,
        aggregate_source_age_seconds=aggregate_source_age_seconds,
        reliability_score=reliability_score,
        expected_source_count=expected_source_count,
        collected_source_count=collected_source_count,
        catalyst_pressure_ratio=catalyst_pressure_ratio,
        available_team_capacity_units=available_team_capacity_units,
        required_team_capacity_units=required_team_capacity_units,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_collection_sla_priority_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_priority_report_builds_empty_pass_readonly_report() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourceCollectionSlaPriorityReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.team_count == d("0.000000")
    assert report.collection_task_count == d("0.000000")
    assert report.priority_rows == ()
    assert report.reason_codes == (
        "research_source_collection_sla_priority_no_collection_tasks",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_priority_report_ranks_by_block_watch_score_and_stable_ties() -> None:
    report = build_report(
        input_row(
            "sports_soccer",
            "sports.soccer",
            aggregate_source_age_seconds=d("900.000000"),
        ),
        input_row(
            "politics",
            "politics",
            collection_task_count=d("5.000000"),
            aggregate_source_age_seconds=d("9000.000000"),
            reliability_score=d("0.700000"),
            expected_source_count=d("10.000000"),
            collected_source_count=d("4.000000"),
            catalyst_pressure_ratio=d("0.600000"),
            available_team_capacity_units=d("3.000000"),
            required_team_capacity_units=d("10.000000"),
        ),
        input_row(
            "macro_rates",
            "finance.macro.rates",
            aggregate_source_age_seconds=d("4500.000000"),
            reliability_score=d("0.750000"),
            expected_source_count=d("8.000000"),
            collected_source_count=d("6.000000"),
            catalyst_pressure_ratio=d("0.400000"),
            available_team_capacity_units=d("6.000000"),
            required_team_capacity_units=d("10.000000"),
        ),
        input_row(
            "crypto_btc",
            "finance.crypto.btc",
            aggregate_source_age_seconds=d("4500.000000"),
            reliability_score=d("0.750000"),
            expected_source_count=d("8.000000"),
            collected_source_count=d("6.000000"),
            catalyst_pressure_ratio=d("0.400000"),
            available_team_capacity_units=d("6.000000"),
            required_team_capacity_units=d("10.000000"),
        ),
    )

    assert tuple(row.status for row in report.priority_rows) == (
        "block",
        "watch",
        "watch",
        "pass",
    )
    assert tuple(row.team_id for row in report.priority_rows) == (
        "politics",
        "crypto_btc",
        "macro_rates",
        "sports_soccer",
    )
    assert tuple(row.coverage_gap_ratio for row in report.priority_rows) == (
        d("0.600000"),
        d("0.250000"),
        d("0.250000"),
        d("0.000000"),
    )
    assert tuple(row.team_capacity_ratio for row in report.priority_rows) == (
        d("0.300000"),
        d("0.600000"),
        d("0.600000"),
        d("1.000000"),
    )
    assert report.status == "block"
    assert report.team_count == d("4.000000")
    assert report.collection_task_count == d("8.000000")
    assert report.block_team_count == d("1.000000")
    assert report.watch_team_count == d("2.000000")
    assert report.reason_codes == (
        "research_source_collection_sla_priority_stale_source_age",
        "research_source_collection_sla_priority_low_reliability",
        "research_source_collection_sla_priority_coverage_gap",
        "research_source_collection_sla_priority_catalyst_pressure",
        "research_source_collection_sla_priority_capacity_limited",
    )


def test_priority_report_statuses_are_exactly_pass_watch_block() -> None:
    module = api()
    pass_report = build_report(input_row("sports_soccer", "sports.soccer"))
    watch_report = build_report(
        input_row(
            "macro_rates",
            "finance.macro.rates",
            aggregate_source_age_seconds=d("3600.000000"),
        ),
    )
    block_report = build_report(
        input_row(
            "politics",
            "politics",
            reliability_score=d("0.500000"),
        ),
    )

    assert module.STATUSES == ("pass", "watch", "block")
    assert pass_report.status == "pass"
    assert pass_report.priority_rows[0].status == "pass"
    assert watch_report.status == "watch"
    assert watch_report.priority_rows[0].status == "watch"
    assert block_report.status == "block"
    assert block_report.priority_rows[0].status == "block"


def test_priority_report_rejects_non_decimal_numeric_inputs() -> None:
    module = api()
    with pytest.raises(ValueError, match="source_age_watch_seconds must be a Decimal"):
        config(source_age_watch_seconds=3600)
    with pytest.raises(ValueError, match="reliability_watch_floor must be a Decimal"):
        config(reliability_watch_floor=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="collection_task_count must be a Decimal"):
        input_row(
            "politics",
            "politics",
            collection_task_count=1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="catalyst_pressure_ratio must be a Decimal"):
        input_row(
            "politics",
            "politics",
            catalyst_pressure_ratio=0.5,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_collection_sla_priority_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )


def test_priority_report_payload_is_public_safe_deterministic_and_digest_verified() -> None:
    module = api()
    rows = (
        input_row(
            "politics",
            "politics",
            aggregate_source_age_seconds=d("9000.000000"),
            reliability_score=d("0.700000"),
            expected_source_count=d("10.000000"),
            collected_source_count=d("4.000000"),
            catalyst_pressure_ratio=d("0.600000"),
            available_team_capacity_units=d("3.000000"),
            required_team_capacity_units=d("10.000000"),
        ),
        input_row(
            "sports_soccer",
            "sports.soccer",
            aggregate_source_age_seconds=d("900.000000"),
        ),
    )

    payload = module.research_source_collection_sla_priority_report_payload(
        build_report(*rows),
    )
    reversed_payload = module.research_source_collection_sla_priority_report_payload(
        build_report(*reversed(rows)),
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["priority_rows"][0]["priority_score"] == "0.690000"
    assert payload["priority_rows"][0]["coverage_gap_ratio"] == "0.600000"
    assert json.dumps(payload, sort_keys=True)

    def assert_public_safe(value: object) -> None:
        forbidden = ("url", "text", "name", "ref", "reference", "source_id")
        if isinstance(value, dict):
            for key, item in value.items():
                assert not any(fragment in key.lower() for fragment in forbidden)
                assert_public_safe(item)
        elif isinstance(value, list):
            for item in value:
                assert_public_safe(item)
        else:
            assert type(value) is not float
            assert type(value) is not int
            if isinstance(value, str):
                assert not value.startswith(("http://", "https://"))

    assert_public_safe(payload)


def test_priority_report_exports_frozen_public_dataclasses() -> None:
    module = api()
    report = build_report(input_row("politics", "politics"))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_COLLECTION_SLA_PRIORITY_CONFIG_VERSION",
        "STATUSES",
        "ResearchSourceCollectionSlaPriorityConfig",
        "ResearchSourceCollectionSlaPriorityInput",
        "ResearchSourceCollectionSlaPriorityReport",
        "ResearchSourceCollectionSlaPriorityRow",
        "build_research_source_collection_sla_priority_report",
        "research_source_collection_sla_priority_report_payload",
    )
    assert is_dataclass(config())
    assert is_dataclass(input_row("sports_soccer", "sports.soccer"))
    assert is_dataclass(report)
    assert is_dataclass(report.priority_rows[0])

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.priority_rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().capacity_watch_ratio = d("0.500000")


def test_priority_report_scope_is_pure_report_only_public_payload() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "source_url",
        "source_text",
        "source_name",
        "source_ref",
        "source_reference",
        "recommendation",
        "sizing",
        "live",
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "trade",
        "private_key",
        "credential",
    ):
        assert forbidden not in lowered

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
