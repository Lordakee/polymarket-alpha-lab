from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(hours=2)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_domain_fx_signal_memory_quality_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_domain_fx_signal_memory_quality_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    report = api()
    values = {
        "config_version": "research-domain-fx-signal-memory-quality-report-v0",
        "watch_stale_after_hours": d("12.000000"),
        "block_stale_after_hours": d("48.000000"),
        "watch_conflict_count": d("1"),
        "block_conflict_count": d("3"),
        "watch_missing_count": d("1"),
        "block_missing_count": d("2"),
        "required_memory_inputs": (
            "central_bank",
            "rates",
            "macro_release",
            "intervention",
            "cross_asset",
        ),
    }
    values.update(overrides)
    return report.ResearchDomainFxSignalMemoryQualityConfig(**values)


def memory_input(**overrides: object):
    report = api()
    values = {
        "memory_input": "central_bank",
        "age_hours": d("2.000000"),
        "conflict_count": d("0"),
        "missing_count": d("0"),
        "observed_at": OBSERVED_AT,
    }
    values.update(overrides)
    return report.ResearchDomainFxSignalMemoryInput(**values)


def build_report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    report = api()
    return report.build_research_domain_fx_signal_memory_quality_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def payload_keys(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            keys.append(key)
            keys.extend(payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(payload_keys(item))
        return tuple(keys)
    return ()


def test_fx_memory_quality_scores_stale_conflicting_and_missing_inputs() -> None:
    report = build_report(
        memory_input(
            memory_input="central_bank",
            age_hours=d("80.000000"),
            conflict_count=d("3"),
            missing_count=d("2"),
        ),
        memory_input(
            memory_input="rates",
            age_hours=d("18.000000"),
            conflict_count=d("1"),
            missing_count=d("1"),
        ),
        memory_input(memory_input="macro_release"),
        memory_input(
            memory_input="intervention",
            age_hours=d("14.000000"),
            conflict_count=d("0"),
            missing_count=d("0"),
        ),
        memory_input(memory_input="cross_asset"),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "research-domain-fx-signal-memory-quality-report-v0"
    assert report.memory_input_count == d("5")
    assert report.required_memory_input_count == d("5")
    assert report.missing_required_memory_input_count == d("0")
    assert report.pass_count == d("2")
    assert report.watch_count == d("2")
    assert report.block_count == d("1")
    assert report.max_age_hours == d("80.000000")
    assert report.total_conflict_count == d("4")
    assert report.total_missing_count == d("3")
    assert report.status == "block"
    assert report.forecast_handoff_status == "block"
    assert report.missing_memory_inputs == ()
    assert report.reason_codes == (
        "fx_memory_quality_block",
        "fx_memory_stale_block",
        "fx_memory_conflict_block",
        "fx_memory_missing_block",
        "fx_memory_stale_watch",
        "fx_memory_conflict_watch",
        "fx_memory_missing_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    assert tuple(row.memory_status for row in report.rows) == (
        "block",
        "watch",
        "watch",
        "pass",
        "pass",
    )
    blocked, rates_watch, intervention_watch, macro_pass, cross_asset_pass = report.rows
    assert blocked.memory_input == "central_bank"
    assert blocked.reason_codes == (
        "fx_memory_stale_block",
        "fx_memory_conflict_block",
        "fx_memory_missing_block",
    )
    assert rates_watch.memory_input == "rates"
    assert rates_watch.reason_codes == (
        "fx_memory_stale_watch",
        "fx_memory_conflict_watch",
        "fx_memory_missing_watch",
    )
    assert intervention_watch.memory_input == "intervention"
    assert intervention_watch.reason_codes == ("fx_memory_stale_watch",)
    assert macro_pass.reason_codes == ("fx_memory_clear",)
    assert cross_asset_pass.reason_codes == ("fx_memory_clear",)
    assert report.reason_code_counts[0].reason_code == "fx_memory_clear"
    assert report.reason_code_counts[0].count == d("2")
    assert report.reason_code_counts[0].memory_input_ratio == d("0.400000")


def test_missing_required_fx_memory_inputs_block_forecast_handoff() -> None:
    partial = build_report(
        memory_input(memory_input="central_bank"),
        memory_input(memory_input="rates"),
        memory_input(memory_input="macro_release"),
        memory_input(memory_input="intervention"),
    )

    assert partial.status == "block"
    assert partial.forecast_handoff_status == "block"
    assert partial.missing_required_memory_input_count == d("1")
    assert partial.missing_memory_inputs == ("cross_asset",)
    assert partial.reason_codes == (
        "fx_memory_quality_block",
        "fx_memory_required_input_missing",
    )

    empty = build_report()
    assert empty.memory_input_count == d("0")
    assert empty.required_memory_input_count == d("5")
    assert empty.missing_required_memory_input_count == d("5")
    assert empty.missing_memory_inputs == (
        "central_bank",
        "rates",
        "macro_release",
        "intervention",
        "cross_asset",
    )
    assert empty.status == "block"
    assert empty.reason_code_counts == ()
    assert empty.rows == ()


def test_custom_config_changes_status_thresholds() -> None:
    custom = config(
        watch_stale_after_hours=d("1.000000"),
        block_stale_after_hours=d("100.000000"),
        watch_conflict_count=d("2"),
        block_conflict_count=d("5"),
        watch_missing_count=d("1"),
        block_missing_count=d("4"),
        required_memory_inputs=("central_bank",),
    )

    report = build_report(memory_input(), cfg=custom)

    assert report.status == "watch"
    assert report.forecast_handoff_status == "watch"
    assert report.reason_codes == (
        "fx_memory_quality_watch",
        "fx_memory_stale_watch",
    )
    assert report.rows[0].reason_codes == ("fx_memory_stale_watch",)


def test_payload_is_deterministic_decimal_only_public_safe_and_digest_checked() -> None:
    report = api()
    first = build_report(
        memory_input(
            memory_input="rates",
            age_hours=d("18.000000"),
            conflict_count=d("1"),
            missing_count=d("1"),
            observed_at=datetime(
                2026,
                7,
                8,
                4,
                30,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        memory_input(memory_input="central_bank"),
        memory_input(memory_input="macro_release"),
        memory_input(memory_input="intervention"),
        memory_input(memory_input="cross_asset"),
        generated_at=datetime(
            2026,
            7,
            8,
            5,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )
    second = build_report(
        memory_input(memory_input="cross_asset"),
        memory_input(memory_input="intervention"),
        memory_input(memory_input="macro_release"),
        memory_input(memory_input="central_bank"),
        memory_input(
            memory_input="rates",
            age_hours=d("18.000000"),
            conflict_count=d("1"),
            missing_count=d("1"),
            observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=UTC),
        ),
    )

    payload = report.research_domain_fx_signal_memory_quality_report_payload(first)
    repeat_payload = report.research_domain_fx_signal_memory_quality_report_payload(
        second,
    )

    assert first.generated_at == GENERATED_AT
    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload == repeat_payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["memory_input_count"] == "5"
    assert payload["rows"][0]["memory_input"] == "rates"
    assert payload["rows"][0]["observed_at"] == "2026-07-08T11:30:00+00:00"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert_no_int_or_float_values(payload)
    json.dumps(payload, sort_keys=True)

    unsafe_fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "source",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "auth",
        "recommendation",
        "sizing",
    )
    assert not any(
        fragment in key.lower()
        for key in payload_keys(payload)
        for fragment in unsafe_fragments
    )
    payload_text = repr(payload).lower()
    assert not any(fragment in payload_text for fragment in unsafe_fragments)

    tampered = dict(payload)
    tampered["pass_count"] = "5"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report.research_domain_fx_signal_memory_quality_report_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, pass_count=d("5"))


def test_public_payload_rejects_raw_identifiers_unsafe_flags_and_numbers() -> None:
    report = api()
    payload = report.research_domain_fx_signal_memory_quality_report_payload(
        build_report(memory_input(), cfg=config(required_memory_inputs=("central_bank",))),
    )

    for key in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet_address",
        "order_id",
        "trade_id",
        "live_url",
        "position_sizing",
        "recommendation_id",
        "auth_header",
    ):
        unsafe = dict(payload)
        unsafe[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            report.research_domain_fx_signal_memory_quality_report_payload(unsafe)

    for value in (
        "raw candidate id",
        "market slug",
        "event question",
        "source text",
        "dsn value",
        "table name",
        "wallet signer",
        "auth token",
        "order route",
        "trade route",
        "live execution",
        "recommendation",
        "sizing",
    ):
        unsafe = dict(payload)
        unsafe["reason_codes"] = (value,)
        with pytest.raises(ValueError, match="unsafe public"):
            report.research_domain_fx_signal_memory_quality_report_payload(unsafe)

    numeric = dict(payload)
    numeric["memory_input_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        report.research_domain_fx_signal_memory_quality_report_payload(numeric)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        report.research_domain_fx_signal_memory_quality_report_payload(downgraded)


def test_dataclasses_are_frozen_and_enforce_exact_decimal_inputs() -> None:
    signal = memory_input()

    with pytest.raises(FrozenInstanceError):
        signal.age_hours = d("4.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="Decimal"):
        memory_input(age_hours=2)
    with pytest.raises(ValueError, match="Decimal"):
        memory_input(conflict_count=1.0)
    with pytest.raises(ValueError, match="Decimal"):
        memory_input(missing_count=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="integral"):
        memory_input(conflict_count=d("1.500000"))
    with pytest.raises(ValueError, match="memory_input"):
        memory_input(memory_input="market_slug")
    with pytest.raises(ValueError, match="generated_at"):
        build_report(signal, generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        memory_input(observed_at=datetime(2026, 7, 8, 11, 45))
    with pytest.raises(ValueError, match="observed_at"):
        memory_input(observed_at=_DatetimeSubclass(2026, 7, 8, 11, 45, tzinfo=UTC))
    with pytest.raises(ValueError, match="future"):
        build_report(memory_input(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique"):
        build_report(memory_input(), memory_input())
    with pytest.raises(ValueError, match="paper_only"):
        memory_input(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_report(memory_input(), cfg=object())

    populated = build_report(
        memory_input(),
        cfg=config(required_memory_inputs=("central_bank",)),
    )
    for value in (populated, *populated.rows, *populated.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item_value is None:
                continue
            if item.name.endswith(("_count", "_hours", "_ratio")):
                assert type(item_value) is Decimal


def test_statuses_and_materialized_fields_are_tamper_evident() -> None:
    report = api()
    digest = build_report(
        memory_input(),
        cfg=config(required_memory_inputs=("central_bank",)),
    )
    row = digest.rows[0]

    assert report.STATUSES == ("pass", "watch", "block")
    assert "blocked" not in report.STATUSES

    with pytest.raises(ValueError, match="memory_status"):
        report.ResearchDomainFxSignalMemoryQualityRow(
            **{
                **row.__dict__,
                "memory_status": "blocked",
            },
        )

    with pytest.raises(ValueError, match="status"):
        report.ResearchDomainFxSignalMemoryQualityReport(
            **{
                **digest.__dict__,
                "status": "blocked",
            },
        )

    object.__setattr__(digest.rows[0], "age_hours", d("99.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report.research_domain_fx_signal_memory_quality_report_payload(digest)


def test_module_is_report_only_without_external_write_or_execution_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_import_roots = {
        "http",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "connect",
        "execute",
        "open",
        "request",
        "send",
        "urlopen",
        "write",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
