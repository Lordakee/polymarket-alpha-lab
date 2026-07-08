from __future__ import annotations

import ast
import hashlib
import importlib
import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
SIX_DECIMAL_RE = re.compile(r"^-?\d+\.\d{6}$")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _MissingOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_recheck_frequency_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "source_age_watch_seconds": d("3600.000000"),
        "source_age_block_seconds": d("10800.000000"),
        "reliability_memory_watch_floor": d("0.800000"),
        "reliability_memory_block_floor": d("0.600000"),
        "catalyst_pressure_watch_ratio": d("0.500000"),
        "catalyst_pressure_block_ratio": d("0.850000"),
        "contradiction_watch_count": d("2.000000"),
        "contradiction_block_count": d("5.000000"),
        "capacity_watch_ratio": d("0.750000"),
        "capacity_block_ratio": d("0.400000"),
        "pass_recheck_frequency_seconds": d("86400.000000"),
        "watch_recheck_frequency_seconds": d("21600.000000"),
        "block_recheck_frequency_seconds": d("3600.000000"),
    }
    values.update(overrides)
    return module.ResearchSourceRecheckFrequencyConfig(**values)


def recheck_input(
    team_id: str = "macro_rates",
    category_id: str = "finance.macro.rates",
    *,
    aggregate_source_age_seconds: Decimal = d("900.000000"),
    reliability_memory_score: Decimal = d("0.950000"),
    catalyst_pressure_ratio: Decimal = d("0.100000"),
    contradiction_count: Decimal = ZERO,
    available_team_capacity_units: Decimal = d("5.000000"),
    required_team_capacity_units: Decimal = d("5.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceRecheckFrequencyInput(
        team_id=team_id,
        category_id=category_id,
        aggregate_source_age_seconds=aggregate_source_age_seconds,
        reliability_memory_score=reliability_memory_score,
        catalyst_pressure_ratio=catalyst_pressure_ratio,
        contradiction_count=contradiction_count,
        available_team_capacity_units=available_team_capacity_units,
        required_team_capacity_units=required_team_capacity_units,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_source_recheck_frequency_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_builds_recheck_frequency_report_with_statuses_bands_and_sorted_rows() -> None:
    module = api()
    summary = report(
        (
            recheck_input("sports_soccer", "sports.soccer"),
            recheck_input(
                "politics",
                "politics",
                aggregate_source_age_seconds=d("12000.000000"),
                reliability_memory_score=d("0.500000"),
                catalyst_pressure_ratio=d("0.900000"),
                contradiction_count=d("5.000000"),
                available_team_capacity_units=d("3.000000"),
                required_team_capacity_units=d("10.000000"),
            ),
            recheck_input(
                "macro_rates",
                "finance.macro.rates",
                aggregate_source_age_seconds=d("4500.000000"),
                reliability_memory_score=d("0.750000"),
                catalyst_pressure_ratio=d("0.400000"),
                contradiction_count=d("1.000000"),
                available_team_capacity_units=d("6.000000"),
                required_team_capacity_units=d("10.000000"),
            ),
            recheck_input(
                "crypto_btc",
                "finance.crypto.btc",
                aggregate_source_age_seconds=d("4500.000000"),
                reliability_memory_score=d("0.750000"),
                catalyst_pressure_ratio=d("0.400000"),
                contradiction_count=d("1.000000"),
                available_team_capacity_units=d("6.000000"),
                required_team_capacity_units=d("10.000000"),
            ),
        ),
    )

    assert type(summary) is module.ResearchSourceRecheckFrequencyReport
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert module.STATUSES == ("pass", "watch", "block")
    assert summary.status == "block"
    assert summary.team_category_count == d("4.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("2.000000")
    assert summary.block_count == d("1.000000")
    assert summary.max_aggregate_source_age_seconds == d("12000.000000")
    assert summary.min_reliability_memory_score == d("0.500000")
    assert summary.max_catalyst_pressure_ratio == d("0.900000")
    assert summary.max_contradiction_count == d("5.000000")
    assert summary.min_team_capacity_ratio == d("0.300000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.derived_validation_digest) == 64

    assert tuple((row.status, row.category_id, row.team_id) for row in summary.rows) == (
        ("block", "politics", "politics"),
        ("watch", "finance.crypto.btc", "crypto_btc"),
        ("watch", "finance.macro.rates", "macro_rates"),
        ("pass", "sports.soccer", "sports_soccer"),
    )
    assert tuple(row.recheck_frequency_band for row in summary.rows) == (
        "block_1h",
        "watch_6h",
        "watch_6h",
        "pass_24h",
    )
    assert tuple(row.recheck_frequency_seconds for row in summary.rows) == (
        d("3600.000000"),
        d("21600.000000"),
        d("21600.000000"),
        d("86400.000000"),
    )
    assert tuple(row.team_capacity_ratio for row in summary.rows) == (
        d("0.300000"),
        d("0.600000"),
        d("0.600000"),
        d("1.000000"),
    )
    assert summary.rows[0].reason_codes == (
        "research_source_recheck_frequency_stale_source_age",
        "research_source_recheck_frequency_reliability_memory_low",
        "research_source_recheck_frequency_catalyst_pressure",
        "research_source_recheck_frequency_contradiction_count",
        "research_source_recheck_frequency_capacity_limited",
    )
    assert summary.reason_codes == summary.rows[0].reason_codes


def test_empty_report_blocks_as_readonly_report_only_missing_public_aggregates() -> None:
    summary = report(())

    assert summary.status == "block"
    assert summary.team_category_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.rows == ()
    assert summary.reason_codes == (
        "research_source_recheck_frequency_no_public_aggregate_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_statuses_are_exactly_pass_watch_block_and_frequency_bands_follow_status() -> None:
    module = api()
    pass_report = report((recheck_input("sports_soccer", "sports.soccer"),))
    watch_report = report(
        (
            recheck_input(
                "macro_rates",
                "finance.macro.rates",
                aggregate_source_age_seconds=d("3600.000000"),
            ),
        ),
    )
    block_report = report(
        (
            recheck_input(
                "politics",
                "politics",
                reliability_memory_score=d("0.500000"),
            ),
        ),
    )

    assert module.STATUSES == ("pass", "watch", "block")
    assert tuple(row.status for row in pass_report.rows) == ("pass",)
    assert tuple(row.recheck_frequency_band for row in pass_report.rows) == ("pass_24h",)
    assert tuple(row.status for row in watch_report.rows) == ("watch",)
    assert tuple(row.recheck_frequency_band for row in watch_report.rows) == ("watch_6h",)
    assert tuple(row.status for row in block_report.rows) == ("block",)
    assert tuple(row.recheck_frequency_band for row in block_report.rows) == ("block_1h",)


def test_payload_is_public_safe_deterministic_json_ready_and_digest_bound() -> None:
    module = api()
    rows = (
        recheck_input(
            "politics",
            "politics",
            aggregate_source_age_seconds=d("12000.000000"),
            reliability_memory_score=d("0.500000"),
            catalyst_pressure_ratio=d("0.900000"),
            contradiction_count=d("5.000000"),
            available_team_capacity_units=d("3.000000"),
            required_team_capacity_units=d("10.000000"),
        ),
        recheck_input("sports_soccer", "sports.soccer"),
    )
    first_report = report(rows)
    second_report = report(tuple(reversed(rows)))
    first_payload = module.research_source_recheck_frequency_report_payload(first_report)
    second_payload = module.research_source_recheck_frequency_report_payload(second_report)

    assert first_payload == second_payload
    json.dumps(first_payload, sort_keys=True)
    assert first_payload["derived_validation_digest"] == first_report.derived_validation_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert first_payload["generated_at"] == GENERATED_AT.isoformat()
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert first_payload["team_category_count"] == "2.000000"
    assert first_payload["rows"][0]["team_id"] == "politics"
    assert first_payload["rows"][0]["aggregate_source_age_seconds"] == "12000.000000"
    assert first_payload["rows"][0]["recheck_frequency_band"] == "block_1h"
    assert_payload_is_plain_json(first_payload)
    assert_six_decimal_strings(first_payload)
    assert_no_raw_source_material(first_payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first_report, derived_validation_digest="0" * 64)


def test_public_contracts_are_frozen_decimal_only_and_reject_false_flags() -> None:
    summary = report((recheck_input(),))
    instances = (config(), recheck_input(), summary.rows[0], summary)
    for instance in instances:
        assert is_dataclass(instance)
        assert instance.__dataclass_params__.frozen
        assert_public_numeric_fields_are_exact_decimals(instance)

    with pytest.raises(FrozenInstanceError):
        summary.rows[0].status = "block"  # type: ignore[misc]

    with pytest.raises(ValueError, match="source_age_watch_seconds must be a Decimal"):
        config(source_age_watch_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reliability_memory_score must be a Decimal"):
        recheck_input(reliability_memory_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="contradiction_count must be a Decimal"):
        recheck_input(contradiction_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report((recheck_input(),), generated_at=datetime(2026, 7, 8, 12, 0))

    false_flag_cases = (
        lambda: config(paper_only=False),
        lambda: config(report_only=False),
        lambda: config(readonly=False),
        lambda: recheck_input(paper_only=False),
        lambda: recheck_input(report_only=False),
        lambda: recheck_input(readonly=False),
        lambda: replace(summary.rows[0], paper_only=False),
        lambda: replace(summary.rows[0], report_only=False),
        lambda: replace(summary.rows[0], readonly=False),
        lambda: replace(summary, paper_only=False),
        lambda: replace(summary, report_only=False),
        lambda: replace(summary, readonly=False),
    )
    for make_value in false_flag_cases:
        with pytest.raises(ValueError, match="must be True"):
            make_value()


def test_validation_rejects_bad_thresholds_inputs_sequences_and_identifiers() -> None:
    with pytest.raises(ValueError, match="source_age_block_seconds"):
        config(source_age_block_seconds=d("3600.000000"))
    with pytest.raises(ValueError, match="reliability_memory_block_floor"):
        config(reliability_memory_block_floor=d("0.800001"))
    with pytest.raises(ValueError, match="contradiction_watch_count"):
        config(contradiction_watch_count=d("1.500000"))
    with pytest.raises(ValueError, match="watch_recheck_frequency_seconds"):
        config(watch_recheck_frequency_seconds=d("86400.000000"))

    with pytest.raises(ValueError, match="category_id"):
        recheck_input("politics", "finance.macro.rates")
    with pytest.raises(ValueError, match="aggregate_source_age_seconds"):
        recheck_input(aggregate_source_age_seconds=d("-1.000000"))
    with pytest.raises(ValueError, match="catalyst_pressure_ratio"):
        recheck_input(catalyst_pressure_ratio=d("1.000001"))
    with pytest.raises(ValueError, match="contradiction_count"):
        recheck_input(contradiction_count=d("1.500000"))
    with pytest.raises(ValueError, match="required_team_capacity_units"):
        recheck_input(required_team_capacity_units=ZERO)
    with pytest.raises(ValueError, match="generated_at"):
        report((recheck_input(),), generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        report((recheck_input(),), generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=_MissingOffsetTimezone()))
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unique"):
        report((recheck_input(), recheck_input()))

    ready = report((recheck_input(),))
    with pytest.raises(ValueError, match="status"):
        replace(ready.rows[0], status="blocked")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready.rows[0],
            reason_codes=(
                "research_source_recheck_frequency_clear",
                "research_source_recheck_frequency_stale_source_age",
            ),
        )
    with pytest.raises(ValueError, match="rows"):
        replace(
            report(
                (
                    recheck_input("sports_soccer", "sports.soccer"),
                    recheck_input("macro_rates", "finance.macro.rates"),
                ),
            ),
            rows=tuple(
                reversed(
                    report(
                        (
                            recheck_input("sports_soccer", "sports.soccer"),
                            recheck_input("macro_rates", "finance.macro.rates"),
                        ),
                    ).rows,
                ),
            ),
        )


def test_module_has_no_io_execution_surface_or_advice_language() -> None:
    module = api()
    module_source = module.__loader__.get_source(module.__name__)
    assert module_source is not None
    tree = ast.parse(module_source)
    lowered_source = module_source.lower()
    lowered_payload = repr(
        module.research_source_recheck_frequency_report_payload(
            report((recheck_input(),)),
        ),
    ).lower()

    forbidden_fragments = (
        "api_key",
        "auth",
        "buy",
        "cancel_order",
        "database",
        "exchange",
        "live_execution",
        "live_trading",
        "place_order",
        "private_key",
        "recommend",
        "sell",
        "sizing",
        "submit_order",
        "token",
        "trade",
        "wallet",
    )
    assert not any(fragment in lowered_source for fragment in forbidden_fragments)
    assert not any(fragment in lowered_payload for fragment in forbidden_fragments)

    imported_roots: set[str] = set()
    call_names: list[str] = []
    attribute_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            leaf = call_leaf_name(node.func)
            if leaf is not None:
                call_names.append(leaf)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    assert imported_roots.isdisjoint(
        {
            "aiohttp",
            "ccxt",
            "eth_account",
            "httpx",
            "psycopg",
            "requests",
            "socket",
            "sqlalchemy",
            "sqlite3",
            "subprocess",
            "supabase",
            "urllib",
            "web3",
        },
    )
    assert not (
        set(call_names)
        & {
            "close",
            "commit",
            "connect",
            "cursor",
            "environ",
            "execute",
            "executemany",
            "getenv",
            "open",
            "rollback",
            "send",
            "urlopen",
            "write",
        }
    )
    assert not (
        set(attribute_names)
        & {
            "close",
            "commit",
            "connect",
            "cursor",
            "environ",
            "execute",
            "executemany",
            "getenv",
            "rollback",
            "send",
            "write",
        }
    )

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_recheck_frequency_report.py"
    )
    assert module_path.name == "research_source_recheck_frequency_report.py"


def assert_payload_is_plain_json(value: object) -> None:
    if isinstance(value, dict):
        for child in value.values():
            assert_payload_is_plain_json(child)
    elif isinstance(value, list):
        for child in value:
            assert_payload_is_plain_json(child)
    else:
        assert not isinstance(value, (Decimal, datetime, float))
        assert type(value) is not int


def assert_six_decimal_strings(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if is_public_numeric_field(str(key)):
                assert type(child) is str, key
                assert SIX_DECIMAL_RE.fullmatch(child), (key, child)
            assert_six_decimal_strings(child)
    elif isinstance(value, list):
        for child in value:
            assert_six_decimal_strings(child)


def assert_public_numeric_fields_are_exact_decimals(value: object) -> None:
    for field in fields(value):
        field_value = getattr(value, field.name)
        if is_public_numeric_field(field.name):
            assert type(field_value) is Decimal, (field.name, field_value, type(field_value))
            assert field_value.as_tuple().exponent == -6, field.name


def assert_no_raw_source_material(value: object) -> None:
    lowered = json.dumps(value, sort_keys=True).lower()
    forbidden_identifier_fragments = (
        "condition_id",
        "event_id",
        "market_slug",
        "question",
        "raw_source",
        "source_id",
        "source_name",
        "source_text",
        "source_url",
        "source_reference",
        "source_ref",
        "url",
    )
    assert not any(fragment in lowered for fragment in forbidden_identifier_fragments)


def is_public_numeric_field(field_name: str) -> bool:
    return field_name.endswith(
        (
            "_seconds",
            "_count",
            "_ratio",
            "_score",
        ),
    )


def call_leaf_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None
