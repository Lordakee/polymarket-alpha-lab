from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_source_coverage_quorum_v9",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-source-coverage-quorum-v9",
        "max_source_age_hours": d("6.000000"),
        "required_source_families": (
            "primary",
            "official",
            "secondary",
            "market_data",
        ),
    }
    values.update(overrides)
    return module.StrategySourceCoverageQuorumV9Config(**values)


def source(
    candidate_id: str,
    source_id: str,
    source_family: str,
    *,
    observed_at: datetime = GENERATED_AT - timedelta(hours=1),
):
    module = api()
    return module.StrategySourceCoverageQuorumV9Source(
        candidate_id=candidate_id,
        source_id=source_id,
        source_family=source_family,
        observed_at=observed_at,
    )


def full_candidate(candidate_id: str = "candidate-alpha"):
    return (
        source(candidate_id, "primary-1", "primary"),
        source(candidate_id, "official-1", "official"),
        source(candidate_id, "secondary-1", "secondary"),
        source(candidate_id, "market-data-1", "market_data"),
    )


def report(*rows, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_strategy_source_coverage_quorum_v9(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def _walk(value: object):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)
    else:
        yield value


def test_full_playbook_source_coverage_passes_quorum() -> None:
    digest = report(*full_candidate())

    assert is_dataclass(digest)
    assert digest.generated_at == GENERATED_AT
    assert digest.config_version == "strategy-source-coverage-quorum-v9"
    assert digest.input_count == d("4")
    assert digest.candidate_count == d("1")
    assert digest.pass_candidate_count == d("1")
    assert digest.watch_candidate_count == d("0")
    assert digest.blocked_candidate_count == d("0")
    assert digest.stale_candidate_count == d("0")
    assert digest.quorum_status == "pass"
    assert digest.missing_source_families == ()
    assert digest.reason_codes == ("strategy_source_coverage_quorum_v9_passed",)
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True

    row = digest.rows[0]
    assert row.candidate_id == "candidate-alpha"
    assert row.source_count == d("4")
    assert row.fresh_source_count == d("4")
    assert row.stale_source_count == d("0")
    assert row.primary_source_count == d("1")
    assert row.official_source_count == d("1")
    assert row.secondary_source_count == d("1")
    assert row.market_data_source_count == d("1")
    assert row.quorum_status == "pass"
    assert row.missing_source_families == ()
    assert row.reason_codes == ("strategy_source_coverage_quorum_v9_passed",)


def test_missing_official_and_market_data_block_quorum() -> None:
    digest = report(
        source("candidate-missing", "primary-1", "primary"),
        source("candidate-missing", "secondary-1", "secondary"),
    )

    assert digest.quorum_status == "blocked"
    assert digest.blocked_candidate_count == d("1")
    assert digest.missing_source_families == ("official", "market_data")
    assert digest.reason_codes == (
        "strategy_source_coverage_quorum_v9_missing_official",
        "strategy_source_coverage_quorum_v9_missing_market_data",
    )
    assert digest.rows[0].quorum_status == "blocked"
    assert digest.rows[0].missing_source_families == ("official", "market_data")
    assert digest.rows[0].reason_codes == (
        "strategy_source_coverage_quorum_v9_missing_official",
        "strategy_source_coverage_quorum_v9_missing_market_data",
    )


def test_stale_required_family_counts_as_missing_fresh_coverage() -> None:
    digest = report(
        source("candidate-stale", "primary-1", "primary"),
        source(
            "candidate-stale",
            "official-old",
            "official",
            observed_at=GENERATED_AT - timedelta(hours=7),
        ),
        source("candidate-stale", "secondary-1", "secondary"),
        source("candidate-stale", "market-data-1", "market_data"),
    )

    assert digest.quorum_status == "blocked"
    assert digest.missing_source_families == ("official",)
    assert digest.stale_candidate_count == d("1")
    assert digest.reason_codes == (
        "strategy_source_coverage_quorum_v9_missing_official",
        "strategy_source_coverage_quorum_v9_stale_sources_present",
    )
    assert digest.rows[0].fresh_source_count == d("3")
    assert digest.rows[0].stale_source_count == d("1")
    assert digest.rows[0].official_source_count == d("0")
    assert digest.rows[0].missing_source_families == ("official",)
    assert digest.rows[0].reason_codes == (
        "strategy_source_coverage_quorum_v9_missing_official",
        "strategy_source_coverage_quorum_v9_stale_sources",
    )


def test_extra_stale_sources_watch_when_required_fresh_families_are_present() -> None:
    digest = report(
        *full_candidate("candidate-watch"),
        source(
            "candidate-watch",
            "secondary-old",
            "secondary",
            observed_at=GENERATED_AT - timedelta(hours=8),
        ),
    )

    assert digest.quorum_status == "watch"
    assert digest.watch_candidate_count == d("1")
    assert digest.stale_candidate_count == d("1")
    assert digest.missing_source_families == ()
    assert digest.reason_codes == (
        "strategy_source_coverage_quorum_v9_stale_sources_present",
    )
    assert digest.rows[0].quorum_status == "watch"
    assert digest.rows[0].missing_source_families == ()
    assert digest.rows[0].reason_codes == (
        "strategy_source_coverage_quorum_v9_stale_sources",
    )


def test_empty_input_returns_clear_report_only_digest() -> None:
    digest = report()

    assert digest.quorum_status == "pass"
    assert digest.input_count == d("0")
    assert digest.candidate_count == d("0")
    assert digest.missing_source_families == ()
    assert digest.rows == ()
    assert digest.reason_codes == ("strategy_source_coverage_quorum_v9_clear",)


def test_rows_and_missing_families_are_sorted_deterministically() -> None:
    digest = report(
        source("candidate-pass", "primary-1", "primary"),
        source("candidate-pass", "official-1", "official"),
        source("candidate-pass", "secondary-1", "secondary"),
        source("candidate-pass", "market-data-1", "market_data"),
        source("candidate-blocked", "primary-1", "primary"),
        source("candidate-watch", "primary-1", "primary"),
        source("candidate-watch", "official-1", "official"),
        source("candidate-watch", "secondary-1", "secondary"),
        source("candidate-watch", "market-data-1", "market_data"),
        source(
            "candidate-watch",
            "official-old",
            "official",
            observed_at=GENERATED_AT - timedelta(hours=8),
        ),
    )

    assert tuple(row.candidate_id for row in digest.rows) == (
        "candidate-blocked",
        "candidate-watch",
        "candidate-pass",
    )
    assert tuple(row.quorum_status for row in digest.rows) == (
        "blocked",
        "watch",
        "pass",
    )
    assert digest.missing_source_families == (
        "official",
        "secondary",
        "market_data",
    )
    assert digest.reason_codes == (
        "strategy_source_coverage_quorum_v9_missing_official",
        "strategy_source_coverage_quorum_v9_missing_secondary",
        "strategy_source_coverage_quorum_v9_missing_market_data",
        "strategy_source_coverage_quorum_v9_stale_sources_present",
    )


def test_payload_helper_uses_decimal_strings_iso_datetimes_and_no_floats() -> None:
    payload = api().strategy_source_coverage_quorum_v9_payload(
        report(*full_candidate()),
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["input_count"] == "4"
    assert payload["rows"][0]["source_count"] == "4"
    assert payload["rows"][0]["primary_source_count"] == "1"
    assert '"4"' in encoded
    assert all(type(value) is not float for value in _walk(payload))


def test_validation_rejects_non_decimal_numbers_bad_times_and_duplicates() -> None:
    module = api()

    with pytest.raises(ValueError, match="max_source_age_hours"):
        config(max_source_age_hours=6)
    with pytest.raises(ValueError, match="max_source_age_hours"):
        config(max_source_age_hours=_DecimalSubclass("6.000000"))
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("strategy-source-coverage-quorum-v9"))
    with pytest.raises(ValueError, match="required_source_families"):
        config(required_source_families=("primary", "primary"))
    with pytest.raises(ValueError, match="source_family"):
        source("candidate-alpha", "market-data-1", "market data")
    with pytest.raises(ValueError, match="candidate_id"):
        source("", "primary-1", "primary")
    with pytest.raises(ValueError, match="observed_at"):
        source(
            "candidate-alpha",
            "primary-1",
            "primary",
            observed_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="observed_at"):
        source(
            "candidate-alpha",
            "primary-1",
            "primary",
            observed_at=datetime(
                2026,
                7,
                2,
                8,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        )
    with pytest.raises(ValueError, match="observed_at"):
        source(
            "candidate-alpha",
            "primary-1",
            "primary",
            observed_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(*full_candidate(), generated_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="future"):
        report(
            source(
                "candidate-alpha",
                "primary-1",
                "primary",
                observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(
            source("candidate-alpha", "primary-1", "primary"),
            source("candidate-alpha", "primary-1", "official"),
        )
    with pytest.raises(ValueError, match="config"):
        module.build_strategy_source_coverage_quorum_v9(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    digest = report(*full_candidate())
    with pytest.raises(ValueError, match="candidate_count"):
        replace(digest, candidate_count=d("2"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(source("candidate-alpha", "primary-1", "primary"), paper_only=False)


def test_dataclasses_are_frozen_and_numeric_public_fields_are_decimal() -> None:
    module = api()
    digest = report(*full_candidate())
    cfg = config()
    row = digest.rows[0]
    input_row = source("candidate-alpha", "primary-1", "primary")

    for exported_name in module.__all__:
        exported_value = getattr(module, exported_name)
        if isinstance(exported_value, type):
            assert is_dataclass(exported_value)
            assert exported_value.__dataclass_params__.frozen is True

    for value in (cfg, digest, row):
        for field in fields(value):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_hours")
            ):
                assert field.type == "Decimal"
                assert type(getattr(value, field.name)) is Decimal

    with pytest.raises(FrozenInstanceError):
        cfg.max_source_age_hours = d("7.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        input_row.source_family = "official"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.quorum_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest.quorum_status = "blocked"  # type: ignore[misc]


def test_payload_helper_requires_report_hard_flags() -> None:
    module = api()
    digest = report(*full_candidate())

    with pytest.raises(ValueError, match="paper_only"):
        module.strategy_source_coverage_quorum_v9_payload(
            replace(digest, paper_only=False),
        )
    with pytest.raises(ValueError, match="report_only"):
        module.strategy_source_coverage_quorum_v9_payload(
            replace(digest, report_only=False),
        )
    with pytest.raises(ValueError, match="readonly"):
        module.strategy_source_coverage_quorum_v9_payload(
            replace(digest, readonly=False),
        )


def test_module_has_no_static_forbidden_surface_terms() -> None:
    source_text = Path(
        "src/polymarket_alpha_lab/strategy_source_coverage_quorum_v9.py",
    ).read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "auth",
        "wallet",
        "broker",
        "live trading",
        "order",
        "cancel",
        "replace",
        "signing",
        "api_key",
        "private_key",
        "payload_json",
        "sqlite",
        "psycopg",
        "supabase",
        "requests",
        "httpx",
        "socket",
        "subprocess",
        "open(",
        "read(",
        "write(",
        "float(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {"__import__", "open", "read", "write", "float"}
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {
                    "connect",
                    "execute",
                    "open",
                    "request",
                    "read",
                    "read_text",
                    "write",
                    "write_text",
                }
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in {
                    "httpx",
                    "os",
                    "pathlib",
                    "psycopg",
                    "requests",
                    "socket",
                    "sqlite3",
                    "subprocess",
                    "supabase",
                }
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in {
                "httpx",
                "os",
                "pathlib",
                "psycopg",
                "requests",
                "socket",
                "sqlite3",
                "subprocess",
                "supabase",
            }
