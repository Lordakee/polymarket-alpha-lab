from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
HANDOFF_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_domain_crypto_signal_memory_quality_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_domain_crypto_signal_memory_quality_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_DOMAIN_CRYPTO_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION
        ),
        "watch_missing_memory_input_count": d("1"),
        "block_missing_memory_input_count": d("2"),
        "watch_stale_memory_input_count": d("1"),
        "block_stale_memory_input_count": d("2"),
        "watch_conflicting_memory_input_count": d("1"),
        "block_conflicting_memory_input_count": d("2"),
        "watch_memory_age_seconds": d("21600.000000"),
        "block_memory_age_seconds": d("86400.000000"),
        "watch_min_quality_score": d("0.850000"),
        "block_min_quality_score": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchDomainCryptoSignalMemoryQualityConfig(**values)


def memory_input(**overrides: object):
    module = api()
    values = {
        "domain_label": "btc_research",
        "catalyst_family": "macro_liquidity",
        "memory_bucket": "handoff_memory",
        "latest_refresh_at": HANDOFF_AT - timedelta(hours=1),
        "expected_memory_input_count": d("4"),
        "available_memory_input_count": d("4"),
        "stale_memory_input_count": d("0"),
        "conflicting_memory_input_count": d("0"),
    }
    values.update(overrides)
    return module.ResearchDomainCryptoSignalMemoryQualityInput(**values)


def build_report(*items: object, cfg=None, generated_at=GENERATED_AT, handoff_at=HANDOFF_AT):
    module = api()
    return module.build_research_domain_crypto_signal_memory_quality_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
        handoff_at=handoff_at,
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
            keys.append(str(key))
            keys.extend(payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(payload_keys(item))
        return tuple(keys)
    return ()


def test_crypto_signal_memory_quality_scores_pass_watch_and_block() -> None:
    result = build_report(
        memory_input(
            catalyst_family="macro_liquidity",
            memory_bucket="cycle_memory",
            latest_refresh_at=HANDOFF_AT - timedelta(hours=30),
            expected_memory_input_count=d("5"),
            available_memory_input_count=d("2"),
            stale_memory_input_count=d("3"),
            conflicting_memory_input_count=d("2"),
        ),
        memory_input(
            catalyst_family="etf_flow",
            memory_bucket="flow_memory",
            latest_refresh_at=HANDOFF_AT - timedelta(hours=8),
            expected_memory_input_count=d("4"),
            available_memory_input_count=d("3"),
            stale_memory_input_count=d("1"),
            conflicting_memory_input_count=d("1"),
        ),
        memory_input(
            catalyst_family="miner_balance",
            memory_bucket="miner_memory",
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.handoff_at == HANDOFF_AT
    assert result.config_version == "research-domain-crypto-signal-memory-quality-report-v0"
    assert result.memory_set_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.missing_memory_input_total == d("4")
    assert result.stale_memory_input_total == d("4")
    assert result.conflicting_memory_input_total == d("3")
    assert result.max_memory_age_seconds == d("108000.000000")
    assert result.min_quality_score == d("0.000000")
    assert result.status == "block"
    assert result.paper_handoff_action == "paper_crypto_memory_handoff_block"
    assert result.reason_codes == (
        "crypto_memory_quality_report_block",
        "missing_memory_inputs_block",
        "stale_memory_inputs_block",
        "conflicting_memory_inputs_block",
        "memory_age_block",
        "memory_quality_block",
        "missing_memory_inputs_watch",
        "stale_memory_inputs_watch",
        "conflicting_memory_inputs_watch",
        "memory_age_watch",
        "memory_quality_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64

    blocked, watched, passed = result.rows
    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    assert blocked.catalyst_family == "macro_liquidity"
    assert blocked.missing_memory_input_count == d("3")
    assert blocked.memory_age_seconds == d("108000.000000")
    assert blocked.quality_score == d("0.000000")
    assert blocked.reason_codes == (
        "missing_memory_inputs_block",
        "stale_memory_inputs_block",
        "conflicting_memory_inputs_block",
        "memory_age_block",
        "memory_quality_block",
    )
    assert watched.catalyst_family == "etf_flow"
    assert watched.completeness_ratio == d("0.750000")
    assert watched.quality_score == d("0.666667")
    assert watched.reason_codes == (
        "missing_memory_inputs_watch",
        "stale_memory_inputs_watch",
        "conflicting_memory_inputs_watch",
        "memory_age_watch",
        "memory_quality_watch",
    )
    assert passed.catalyst_family == "miner_balance"
    assert passed.quality_score == d("0.958333")
    assert passed.reason_codes == ("crypto_memory_quality_clear",)
    assert result.reason_code_counts[0].reason_code == "conflicting_memory_inputs_block"
    assert result.reason_code_counts[0].count == d("1")


def test_empty_crypto_memory_report_blocks_forecast_handoff() -> None:
    result = build_report()

    assert result.memory_set_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.missing_memory_input_total == d("0")
    assert result.stale_memory_input_total == d("0")
    assert result.conflicting_memory_input_total == d("0")
    assert result.max_memory_age_seconds == d("0.000000")
    assert result.min_quality_score == d("0.000000")
    assert result.status == "block"
    assert result.paper_handoff_action == "paper_crypto_memory_handoff_block"
    assert result.reason_codes == ("crypto_memory_quality_no_memory_sets",)
    assert result.reason_code_counts[0].reason_code == "crypto_memory_quality_no_memory_sets"
    assert result.reason_code_counts[0].count == d("1")
    assert result.rows == ()

    populated = build_report(memory_input())
    for value in (result, populated, *populated.rows, *populated.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item.name.endswith(("_count", "_total", "_score", "_seconds", "_ratio")):
                assert type(item_value) is Decimal


def test_payload_is_deterministic_public_safe_and_digest_validated() -> None:
    module = api()
    first = build_report(
        memory_input(
            catalyst_family="etf_flow",
            memory_bucket="flow_memory",
            latest_refresh_at=datetime(
                2026,
                7,
                7,
                21,
                0,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
            expected_memory_input_count=d("4"),
            available_memory_input_count=d("3"),
            stale_memory_input_count=d("1"),
            conflicting_memory_input_count=d("1"),
        ),
        memory_input(catalyst_family="miner_balance", memory_bucket="miner_memory"),
        generated_at=datetime(
            2026,
            7,
            8,
            5,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
        handoff_at=datetime(
            2026,
            7,
            8,
            5,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )
    second = build_report(
        memory_input(catalyst_family="miner_balance", memory_bucket="miner_memory"),
        memory_input(
            catalyst_family="etf_flow",
            memory_bucket="flow_memory",
            latest_refresh_at=datetime(2026, 7, 8, 4, 0, tzinfo=UTC),
            expected_memory_input_count=d("4"),
            available_memory_input_count=d("3"),
            stale_memory_input_count=d("1"),
            conflicting_memory_input_count=d("1"),
        ),
    )

    payload = module.research_domain_crypto_signal_memory_quality_report_payload(first)
    repeat_payload = module.research_domain_crypto_signal_memory_quality_report_payload(second)
    unsigned_payload = dict(payload)
    digest = unsigned_payload.pop("derived_validation_digest")
    expected_digest = sha256(
        json.dumps(unsigned_payload, sort_keys=True, separators=(",", ":")).encode(),
    ).hexdigest()

    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload == repeat_payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["handoff_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["memory_set_count"] == "2"
    assert payload["rows"][0]["quality_score"] == "0.666667"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert digest == expected_digest
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
        "database",
        "network",
        "auth",
        "live",
        "sizing",
        "recommendation",
    )
    assert not any(
        fragment in key.lower()
        for key in payload_keys(payload)
        for fragment in unsafe_fragments
    )
    payload_text = repr(payload).lower()
    assert not any(fragment in payload_text for fragment in unsafe_fragments)

    tampered = dict(payload)
    tampered["pass_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_domain_crypto_signal_memory_quality_report_payload(tampered)

    unsafe = dict(payload)
    unsafe["market_slug"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_domain_crypto_signal_memory_quality_report_payload(unsafe)

    numeric = dict(payload)
    numeric["memory_set_count"] = 2
    with pytest.raises(ValueError, match="numeric"):
        module.research_domain_crypto_signal_memory_quality_report_payload(numeric)


def test_rejects_bad_types_flags_times_labels_and_manual_tampering() -> None:
    module = api()
    safe_input = memory_input()
    result = build_report(safe_input)
    row = result.rows[0]

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="Decimal"):
        memory_input(expected_memory_input_count=4)
    with pytest.raises(ValueError, match="Decimal"):
        memory_input(stale_memory_input_count=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="whole"):
        memory_input(available_memory_input_count=d("1.500000"))
    with pytest.raises(ValueError, match="available_memory_input_count"):
        memory_input(expected_memory_input_count=d("2"), available_memory_input_count=d("3"))
    with pytest.raises(ValueError, match="latest_refresh_at"):
        memory_input(latest_refresh_at=datetime(2026, 7, 8, 11, 0))
    with pytest.raises(ValueError, match="latest_refresh_at"):
        memory_input(
            latest_refresh_at=_DatetimeSubclass(2026, 7, 8, 11, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="handoff_at"):
        build_report(safe_input, handoff_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="future"):
        build_report(memory_input(latest_refresh_at=HANDOFF_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique"):
        build_report(memory_input(), memory_input())
    with pytest.raises(ValueError, match="catalyst_family"):
        memory_input(catalyst_family="market_slug")
    with pytest.raises(ValueError, match="memory_bucket"):
        memory_input(memory_bucket="source_text")
    with pytest.raises(ValueError, match="paper_only"):
        memory_input(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_report(memory_input(), cfg=object())
    with pytest.raises(ValueError, match="status"):
        replace(row, status="review")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, pass_count=d("2"))
    multi_row_result = build_report(
        safe_input,
        memory_input(catalyst_family="etf_flow", memory_bucket="flow_memory"),
    )
    with pytest.raises(ValueError, match="rows"):
        replace(multi_row_result, rows=tuple(reversed(multi_row_result.rows)))

    payload = module.research_domain_crypto_signal_memory_quality_report_payload(result)
    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.research_domain_crypto_signal_memory_quality_report_payload(downgraded)


def test_module_is_report_only_without_external_write_or_execution_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    banned_import_roots = {
        "aiohttp",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "urllib",
        "web3",
    }
    banned_call_names = {
        "buy",
        "connect",
        "delete",
        "execute",
        "executemany",
        "get",
        "open",
        "order",
        "patch",
        "post",
        "put",
        "request",
        "sell",
        "send",
        "submit",
        "trade",
        "write",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in banned_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in banned_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in banned_call_names
