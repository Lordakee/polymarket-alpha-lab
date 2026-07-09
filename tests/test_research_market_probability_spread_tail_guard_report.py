from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 15, 55, tzinfo=UTC)
ZERO = Decimal("0.000000")
FORBIDDEN_SURFACE_TERMS = (
    "auth",
    "database",
    "db",
    "dsn",
    "http",
    "key",
    "live",
    "market_id",
    "market_slug",
    "network",
    "order",
    "position",
    "private",
    "question",
    "recommend",
    "request",
    "secret",
    "sizing",
    "slug",
    "socket",
    "source_text",
    "source_url",
    "table",
    "token",
    "trade",
    "url",
    "wallet",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_probability_spread_tail_guard_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": module.DEFAULT_RESEARCH_MARKET_PROBABILITY_SPREAD_TAIL_GUARD_CONFIG_VERSION,
        "watch_spread_threshold": d("0.080000"),
        "block_spread_threshold": d("0.150000"),
        "watch_tail_probability_threshold": d("0.100000"),
        "block_tail_probability_threshold": d("0.300000"),
        "watch_source_age_seconds": d("1800.000000"),
        "block_source_age_seconds": d("3600.000000"),
        "spread_weight": d("0.450000"),
        "tail_weight": d("0.350000"),
        "source_age_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchMarketProbabilitySpreadTailGuardConfig(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_id": "candidate-secret-alpha",
        "probability_midpoint": d("0.540000"),
        "probability_spread": d("0.050000"),
        "left_tail_probability": d("0.040000"),
        "right_tail_probability": d("0.060000"),
        "source_observed_at": OBSERVED_AT,
        "reason_codes": ("candidate_probability_input",),
    }
    values.update(overrides)
    return module.ResearchMarketProbabilitySpreadTailGuardCandidate(**values)


def report(*candidates: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_research_market_probability_spread_tail_guard_report(
        candidates,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_report_scores_spread_tail_and_source_age_with_pass_watch_block_statuses() -> None:
    result = report(
        candidate(
            candidate_id="pass-secret-alpha",
            probability_spread=d("0.050000"),
            left_tail_probability=d("0.040000"),
            right_tail_probability=d("0.060000"),
            source_observed_at=GENERATED_AT - timedelta(minutes=5),
        ),
        candidate(
            candidate_id="watch-wallet-alpha",
            probability_spread=d("0.100000"),
            left_tail_probability=d("0.120000"),
            right_tail_probability=d("0.080000"),
            source_observed_at=GENERATED_AT - timedelta(minutes=20),
        ),
        candidate(
            candidate_id="blocked-market-token-alpha",
            probability_spread=d("0.180000"),
            left_tail_probability=d("0.320000"),
            right_tail_probability=d("0.150000"),
            source_observed_at=GENERATED_AT - timedelta(minutes=70),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.candidate_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.max_probability_spread == d("0.180000")
    assert result.max_tail_probability == d("0.320000")
    assert result.max_source_age_seconds == d("4200.000000")
    assert result.max_tail_guard_score == d("0.426333")
    assert result.status == "block"
    assert result.reason_codes == (
        "spread_tail_guard_block",
        "spread_tail_guard_source_stale_block",
        "spread_tail_guard_spread_block",
        "spread_tail_guard_spread_watch",
        "spread_tail_guard_tail_block",
        "spread_tail_guard_tail_watch",
        "spread_tail_guard_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    blocked_row, watched, passed = result.rows
    assert blocked_row.public_candidate_ref.startswith("candidate_ref_")
    assert "token" not in blocked_row.public_candidate_ref
    assert "market" not in blocked_row.public_candidate_ref
    assert blocked_row.tail_probability == d("0.320000")
    assert blocked_row.source_age_seconds == d("4200.000000")
    assert blocked_row.tail_guard_score == d("0.426333")
    assert blocked_row.reason_codes == (
        "candidate_probability_input",
        "spread_tail_guard_block",
        "spread_tail_guard_source_stale_block",
        "spread_tail_guard_spread_block",
        "spread_tail_guard_tail_block",
    )

    assert watched.tail_probability == d("0.120000")
    assert watched.tail_guard_score == d("0.153667")
    assert watched.reason_codes == (
        "candidate_probability_input",
        "spread_tail_guard_spread_watch",
        "spread_tail_guard_tail_watch",
        "spread_tail_guard_watch",
    )

    assert passed.status == "pass"
    assert passed.reason_codes == (
        "candidate_probability_input",
        "spread_tail_guard_pass",
    )


def test_empty_report_is_watch_zeroed_decimal_readonly_and_digest_validated() -> None:
    module = api()
    empty = report()

    assert empty.candidate_count == ZERO
    assert empty.pass_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.block_count == ZERO
    assert empty.max_probability_spread == ZERO
    assert empty.max_tail_probability == ZERO
    assert empty.max_source_age_seconds == ZERO
    assert empty.max_tail_guard_score == ZERO
    assert empty.status == "watch"
    assert empty.reason_codes == ("spread_tail_guard_no_candidates",)
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True
    assert len(empty.derived_validation_digest) == 64
    int(empty.derived_validation_digest, 16)
    assert empty.payload["derived_validation_digest"] == empty.derived_validation_digest
    assert module.research_market_probability_spread_tail_guard_payload(empty) == empty.payload

    payload_without_digest = dict(empty.payload)
    payload_without_digest.pop("derived_validation_digest")
    canonical = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert hashlib.sha256(canonical.encode("utf-8")).hexdigest() == empty.derived_validation_digest

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(empty, derived_validation_digest="0" * 64)


def test_payload_uses_decimal_strings_redacts_candidate_ids_and_rejects_public_leaks() -> None:
    module = api()
    result = report(
        candidate(
            candidate_id="secret-wallet-order-token-candidate",
            probability_spread=d("0.180000"),
            right_tail_probability=d("0.320000"),
        ),
        generated_at=datetime(2026, 7, 8, 9, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.research_market_probability_spread_tail_guard_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload["generated_at"] == "2026-07-08T16:00:00+00:00"
    assert payload["candidate_count"] == "1.000000"
    assert payload["rows"][0]["source_observed_at"] == "2026-07-08T15:55:00+00:00"
    assert payload["rows"][0]["probability_spread"] == "0.180000"
    assert payload["rows"][0]["tail_probability"] == "0.320000"
    assert payload["rows"][0]["public_candidate_ref"].startswith("candidate_ref_")
    assert "secret-wallet" not in rendered
    assert "order" not in rendered
    assert "token" not in rendered
    assert "candidate_id" not in rendered
    assert "market_id" not in rendered
    assert "market_slug" not in rendered
    assert "question" not in rendered
    assert "source_url" not in rendered
    assert_no_float_values(payload)
    json.dumps(payload, sort_keys=True)


def test_validation_rejects_bad_types_flags_times_thresholds_and_consistency() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_research_market_probability_spread_tail_guard_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(candidate(), generated_at=datetime(2026, 7, 8, 16, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            candidate(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="probability_midpoint"):
        candidate(probability_midpoint=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="probability_spread"):
        candidate(probability_spread=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="right_tail_probability"):
        candidate(right_tail_probability=Decimal("NaN"))
    with pytest.raises(ValueError, match="source_observed_at"):
        candidate(source_observed_at=datetime(2026, 7, 8, 15, 55))
    with pytest.raises(ValueError, match="source_observed_at"):
        report(candidate(source_observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate candidate"):
        report(candidate(), candidate())
    with pytest.raises(ValueError, match="reason_codes"):
        candidate(reason_codes=("z_reason", "a_reason"))
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(config(), report_only=False)
    with pytest.raises(ValueError, match="block_spread_threshold"):
        config(block_spread_threshold=d("0.070000"))
    with pytest.raises(ValueError, match="weight"):
        config(spread_weight=d("0.500000"))
    with pytest.raises(ValueError, match="candidate_count"):
        replace(report(candidate(candidate_id="row")), candidate_count=d("2.000000"))

    frozen = candidate(candidate_id="frozen")
    with pytest.raises(FrozenInstanceError):
        frozen.probability_spread = d("0.200000")  # type: ignore[misc]


def test_public_api_and_static_no_io_no_live_or_identifier_leak_surface() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_RESEARCH_MARKET_PROBABILITY_SPREAD_TAIL_GUARD_CONFIG_VERSION",
        "ResearchMarketProbabilitySpreadTailGuardCandidate",
        "ResearchMarketProbabilitySpreadTailGuardConfig",
        "ResearchMarketProbabilitySpreadTailGuardReport",
        "ResearchMarketProbabilitySpreadTailGuardRow",
        "build_research_market_probability_spread_tail_guard_report",
        "research_market_probability_spread_tail_guard_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    source_path = (
        Path(__file__).resolve().parents[1]
        / "src/polymarket_alpha_lab/research_market_probability_spread_tail_guard_report.py"
    )
    source = source_path.read_text(encoding="utf-8")
    lowered_source = source.lower()
    for term in (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "connect(",
        "execute(",
        "executemany(",
        "open(",
        "read(",
        "write(",
    ):
        assert term not in lowered_source
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if hasattr(exported, "__dataclass_fields__"):
            assert not any(
                term in field.name.lower()
                for field in fields(exported)
                for term in FORBIDDEN_SURFACE_TERMS
            )

    tree = ast.parse(source)
    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "http",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    forbidden_call_names = {
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "post",
        "put",
        "patch",
        "read",
        "write",
    }
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in forbidden_call_names

    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
