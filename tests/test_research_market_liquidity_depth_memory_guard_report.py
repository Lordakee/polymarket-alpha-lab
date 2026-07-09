from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 11, 45, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_liquidity_depth_memory_guard_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def term(*parts: str) -> str:
    return "".join(parts)


def expected_ref(prefix: str, *parts: str) -> str:
    digest = sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def raw_values(label: str) -> dict[str, str]:
    return {
        "raw_candidate_ref": f"candidate-private-{label}",
        "raw_market_ref": f"market-private-{label}",
        "evidence_locator": term("https", "://", "research.example.invalid/", label),
        "evidence_excerpt": f"internal note {label}",
        "evidence_store_ref": term("post", "gresql", "://user:pass@host/", label),
        "evidence_collection_ref": f"internal_collection_{label}",
        "evidence_secret_ref": f"secret-{label}",
    }


def observation(**overrides: object):
    mod = api()
    values: dict[str, object] = {
        **raw_values("alpha"),
        "cost_rate": d("0.020000"),
        "liquidity_score": d("0.900000"),
        "depth_score": d("0.900000"),
        "memory_score": d("0.900000"),
        "observed_at": OBSERVED_AT,
        "reason_codes": ("manual_review_ready",),
    }
    values.update(overrides)
    return mod.ResearchMarketLiquidityDepthMemoryGuardObservation(**values)


def config(**overrides: object):
    mod = api()
    values: dict[str, object] = {
        "config_version": (
            "research-market-liquidity-depth-memory-guard-report-v0"
        ),
        "max_pass_cost_rate": d("0.025000"),
        "max_watch_cost_rate": d("0.060000"),
        "min_pass_liquidity_score": d("0.700000"),
        "min_watch_liquidity_score": d("0.450000"),
        "min_pass_depth_score": d("0.700000"),
        "min_watch_depth_score": d("0.450000"),
        "min_pass_memory_score": d("0.750000"),
        "min_watch_memory_score": d("0.500000"),
    }
    values.update(overrides)
    return mod.ResearchMarketLiquidityDepthMemoryGuardConfig(**values)


def report(*items: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT):
    return api().build_research_market_liquidity_depth_memory_guard_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def expected_payload_digest(payload: dict[str, object]) -> str:
    public_payload = dict(payload)
    public_payload.pop("payload_sha256")
    encoded = json.dumps(
        public_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def assert_no_native_numbers(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_native_numbers(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_native_numbers(item)
        return
    if type(value) is bool:
        return
    assert type(value) is not int
    assert type(value) is not float
    assert type(value) is not Decimal


def test_report_builds_pass_watch_block_rows_and_digest() -> None:
    built = report(
        observation(**raw_values("pass")),
        observation(
            **raw_values("watch"),
            cost_rate=d("0.040000"),
            liquidity_score=d("0.600000"),
            depth_score=d("0.600000"),
            memory_score=d("0.600000"),
        ),
        observation(
            **raw_values("block"),
            cost_rate=d("0.080000"),
            liquidity_score=d("0.300000"),
            depth_score=d("0.300000"),
            memory_score=d("0.300000"),
        ),
    )

    assert is_dataclass(built)
    assert built.generated_at == GENERATED_AT
    assert built.config_version == "research-market-liquidity-depth-memory-guard-report-v0"
    assert built.observation_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.max_cost_rate == d("0.080000")
    assert built.min_liquidity_score == d("0.300000")
    assert built.min_depth_score == d("0.300000")
    assert built.min_memory_score == d("0.300000")
    assert built.min_guard_score == d("0.350000")
    assert built.status == "block"
    assert built.summary == (
        "block: liquidity/depth/memory guard inputs are not sufficient for paper review"
    )
    assert built.reason_codes == (
        "liquidity_depth_memory_guard_report_block",
        "liquidity_depth_memory_guard_cost_block",
        "liquidity_depth_memory_guard_liquidity_block",
        "liquidity_depth_memory_guard_depth_block",
        "liquidity_depth_memory_guard_memory_block",
        "liquidity_depth_memory_guard_cost_watch",
        "liquidity_depth_memory_guard_liquidity_watch",
        "liquidity_depth_memory_guard_depth_watch",
        "liquidity_depth_memory_guard_memory_watch",
    )
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True

    block_row, watch_row, pass_row = built.rows
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    assert block_row.row_index == d("1.000000")
    assert block_row.subject_ref == expected_ref("subject_ref", "candidate-private-block")
    assert block_row.venue_ref == expected_ref("venue_ref", "market-private-block")
    assert block_row.evidence_ref == expected_ref(
        "evidence_ref",
        *tuple(raw_values("block")[name] for name in (
            "evidence_locator",
            "evidence_excerpt",
            "evidence_store_ref",
            "evidence_collection_ref",
            "evidence_secret_ref",
        )),
    )
    assert block_row.guard_score == d("0.350000")
    assert block_row.reason_codes == (
        "manual_review_ready",
        "liquidity_depth_memory_guard_cost_block",
        "liquidity_depth_memory_guard_liquidity_block",
        "liquidity_depth_memory_guard_depth_block",
        "liquidity_depth_memory_guard_memory_block",
    )
    assert watch_row.guard_score == d("0.650000")
    assert pass_row.guard_score == d("0.900000")
    assert pass_row.reason_codes == (
        "manual_review_ready",
        "liquidity_depth_memory_guard_ready",
    )

    payload = api().research_market_liquidity_depth_memory_guard_report_payload(built)
    assert payload["payload_sha256"] == expected_payload_digest(payload)
    assert built.payload_sha256 == payload["payload_sha256"]
    assert api().validate_research_market_liquidity_depth_memory_guard_report_payload(
        payload,
    )

    tampered = dict(payload)
    tampered["status"] = "pass"
    with pytest.raises(ValueError, match="payload_sha256"):
        api().validate_research_market_liquidity_depth_memory_guard_report_payload(
            tampered,
        )


def test_payload_is_deterministic_decimal_only_and_redacts_raw_inputs() -> None:
    raw = raw_values("bravo")
    built = report(
        observation(**raw),
        generated_at=datetime(2026, 7, 9, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload_one = api().research_market_liquidity_depth_memory_guard_report_payload(built)
    payload_two = api().research_market_liquidity_depth_memory_guard_report_payload(built)
    encoded = json.dumps(payload_one, sort_keys=True)
    payload_text = encoded.lower()

    assert payload_one == payload_two
    assert built.generated_at == GENERATED_AT
    assert payload_one["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload_one["observation_count"] == "1.000000"
    assert payload_one["rows"][0]["cost_rate"] == "0.020000"
    assert payload_one["rows"][0]["observed_at"] == "2026-07-09T11:45:00+00:00"
    assert_no_native_numbers(payload_one)
    assert "Decimal(" not in repr(payload_one)
    assert "datetime" not in payload_text

    for raw_fragment in raw.values():
        assert raw_fragment.lower() not in payload_text
    for unsafe_key_part in (
        "raw",
        "locator",
        "excerpt",
        "store_ref",
        "collection_ref",
        "secret_ref",
        term("u", "r", "l"),
        term("d", "s", "n"),
        term("ta", "ble"),
        term("to", "ken"),
    ):
        assert unsafe_key_part not in payload_text


def test_decimal_only_flags_frozen_and_status_validation() -> None:
    mod = api()
    built = report(observation())

    assert mod.STATUSES == ("pass", "watch", "block")
    for value in (config(), observation(), built, *built.rows):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item.name.endswith(("_count", "_rate", "_score")) or item.name == "row_index":
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        built.status = "pass"  # type: ignore[misc]

    with pytest.raises(ValueError, match="cost_rate must be a Decimal"):
        observation(cost_rate=0.02)
    with pytest.raises(ValueError, match="cost_rate must be a Decimal"):
        observation(cost_rate=_DecimalSubclass("0.020000"))
    with pytest.raises(ValueError, match="cost_rate must be finite"):
        observation(cost_rate=Decimal("NaN"))
    with pytest.raises(ValueError, match="config must be paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="status is not supported"):
        mod.ResearchMarketLiquidityDepthMemoryGuardRow(
            row_index=d("1.000000"),
            subject_ref=expected_ref("subject_ref", "candidate-private"),
            venue_ref=expected_ref("venue_ref", "market-private"),
            evidence_ref=expected_ref("evidence_ref", "a", "b", "c", "d", "e"),
            cost_rate=d("0.020000"),
            liquidity_score=d("0.900000"),
            depth_score=d("0.900000"),
            memory_score=d("0.900000"),
            guard_score=d("0.900000"),
            observed_at=OBSERVED_AT,
            status="review",
            reason_codes=("liquidity_depth_memory_guard_ready",),
        )


def test_payload_validation_rejects_unsafe_surface_and_non_readonly_flags() -> None:
    mod = api()
    payload = mod.research_market_liquidity_depth_memory_guard_report_payload(
        report(observation()),
    )

    unsafe_payload = dict(payload)
    unsafe_payload["raw_candidate_ref"] = "candidate-private"
    unsafe_payload["payload_sha256"] = expected_payload_digest(unsafe_payload)
    with pytest.raises(ValueError, match="unsafe public field"):
        mod.validate_research_market_liquidity_depth_memory_guard_report_payload(
            unsafe_payload,
        )

    bad_flags = dict(payload)
    bad_flags["readonly"] = False
    bad_flags["payload_sha256"] = expected_payload_digest(bad_flags)
    with pytest.raises(ValueError, match="payload must be readonly"):
        mod.validate_research_market_liquidity_depth_memory_guard_report_payload(
            bad_flags,
        )


def test_module_static_surface_stays_report_only() -> None:
    module_path = Path(api().__file__)
    module_text = module_path.read_text(encoding="utf-8")
    lowered = module_text.lower()

    for blocked in (
        term("d", "b"),
        term("net", "work"),
        term("wal", "let"),
        term("au", "th"),
        term("or", "der"),
        term("li", "ve"),
        term("tra", "ding"),
        term("siz", "ing"),
        term("recomm", "endation"),
    ):
        assert blocked not in lowered

    tree = ast.parse(module_text)
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert "requests" not in imported_roots
    assert "socket" not in imported_roots
    assert "sqlite3" not in imported_roots
    assert "sqlalchemy" not in imported_roots
