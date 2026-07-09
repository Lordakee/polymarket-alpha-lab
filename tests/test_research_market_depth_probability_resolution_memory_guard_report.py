from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_market_depth_probability_resolution_memory_guard_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate_ref(value: str) -> str:
    return f"candidate_ref_{sha256(value.encode('utf-8')).hexdigest()[:16]}"


def market_ref(*parts: str) -> str:
    digest = sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"market_ref_{digest}"


def evidence_ref(*parts: str) -> str:
    digest = sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"evidence_ref_{digest}"


def expected_payload_digest(payload: dict[str, object]) -> str:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest")
    encoded = json.dumps(
        unsigned_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def config(**overrides: object):
    mod = api()
    values = {
        "config_version": (
            "research-market-depth-probability-resolution-memory-guard-v0"
        ),
        "watch_depth_coverage_ratio": d("0.750000"),
        "block_depth_coverage_ratio": d("0.500000"),
        "watch_probability_gap": d("0.080000"),
        "block_probability_gap": d("0.150000"),
        "watch_resolution_memory_age_hours": d("24.000000"),
        "block_resolution_memory_age_hours": d("72.000000"),
    }
    values.update(overrides)
    return mod.ResearchMarketDepthProbabilityResolutionMemoryGuardConfig(**values)


def observation(**overrides: object):
    mod = api()
    values = {
        "raw_candidate_id": "candidate-secret-alpha",
        "raw_market_id": "market-private-alpha",
        "raw_market_slug": "will-event-alpha-resolve",
        "raw_market_question": "Will the private alpha event resolve?",
        "raw_source_url": "https://research.example.invalid/private?token=alpha",
        "raw_source_text": "internal resolution note alpha",
        "raw_source_dsn": "postgresql://user:pass@host/alpha",
        "raw_source_table": "internal_resolution_table_alpha",
        "raw_source_token": "token-alpha",
        "market_probability": d("0.600000"),
        "resolution_memory_probability": d("0.610000"),
        "available_depth": d("120.000000"),
        "required_depth_floor": d("100.000000"),
        "resolution_memory_age_hours": d("2.000000"),
    }
    values.update(overrides)
    return mod.ResearchMarketDepthProbabilityResolutionMemoryGuardObservation(**values)


def report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    return api().build_research_market_depth_probability_resolution_memory_guard_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


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
    assert type(value) is not float
    assert type(value) is not int


def test_report_builds_depth_probability_resolution_memory_guard_and_digest() -> None:
    built = report(
        observation(
            raw_candidate_id="candidate-secret-pass",
            raw_market_id="market-private-pass",
            raw_market_slug="will-pass-resolve",
            raw_market_question="Will pass resolve?",
            market_probability=d("0.600000"),
            resolution_memory_probability=d("0.610000"),
            available_depth=d("120.000000"),
            resolution_memory_age_hours=d("2.000000"),
        ),
        observation(
            raw_candidate_id="candidate-secret-watch",
            raw_market_id="market-private-watch",
            raw_market_slug="will-watch-resolve",
            raw_market_question="Will watch resolve?",
            market_probability=d("0.610000"),
            resolution_memory_probability=d("0.510000"),
            available_depth=d("70.000000"),
            resolution_memory_age_hours=d("30.000000"),
        ),
        observation(
            raw_candidate_id="candidate-secret-block",
            raw_market_id="market-private-block",
            raw_market_slug="will-block-resolve",
            raw_market_question="Will block resolve?",
            market_probability=d("0.800000"),
            resolution_memory_probability=d("0.600000"),
            available_depth=d("40.000000"),
            resolution_memory_age_hours=d("80.000000"),
        ),
    )

    assert is_dataclass(built)
    assert built.generated_at == GENERATED_AT
    assert (
        built.config_version
        == "research-market-depth-probability-resolution-memory-guard-v0"
    )
    assert built.observation_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.min_depth_coverage_ratio == d("0.400000")
    assert built.max_probability_gap == d("0.200000")
    assert built.max_resolution_memory_age_hours == d("80.000000")
    assert built.status == "block"
    assert built.reason_codes == (
        "depth_coverage_block",
        "probability_gap_block",
        "resolution_memory_block",
        "depth_coverage_watch",
        "probability_gap_watch",
        "resolution_memory_stale",
    )
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True

    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    first = built.rows[0]
    assert first.candidate_ref == candidate_ref("candidate-secret-block")
    assert first.market_ref == market_ref(
        "market-private-block",
        "will-block-resolve",
        "Will block resolve?",
    )
    assert first.probability_gap == d("0.200000")
    assert first.depth_coverage_ratio == d("0.400000")
    assert first.reason_codes == (
        "depth_coverage_block",
        "probability_gap_block",
        "resolution_memory_block",
    )

    payload = api().research_market_depth_probability_resolution_memory_guard_report_payload(
        built,
    )
    assert payload["derived_validation_digest"] == expected_payload_digest(payload)
    assert built.derived_validation_digest == payload["derived_validation_digest"]
    assert api().validate_research_market_depth_probability_resolution_memory_guard_report_payload(
        payload,
    )

    tampered = dict(payload)
    tampered["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api().validate_research_market_depth_probability_resolution_memory_guard_report_payload(
            tampered,
        )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)


def test_payload_is_deterministic_decimal_only_and_redacts_sensitive_inputs() -> None:
    source_parts = (
        "https://research.example.invalid/private?token=bravo",
        "internal resolution note bravo",
        "postgresql://user:pass@host/bravo",
        "internal_resolution_table_bravo",
        "token-bravo",
    )
    built = report(
        observation(
            raw_candidate_id="candidate-secret-bravo",
            raw_market_id="market-private-bravo",
            raw_market_slug="will-bravo-resolve",
            raw_market_question="Will bravo resolve?",
            raw_source_url=source_parts[0],
            raw_source_text=source_parts[1],
            raw_source_dsn=source_parts[2],
            raw_source_table=source_parts[3],
            raw_source_token=source_parts[4],
        ),
        generated_at=datetime(2026, 7, 9, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload_one = api().research_market_depth_probability_resolution_memory_guard_report_payload(
        built,
    )
    payload_two = api().research_market_depth_probability_resolution_memory_guard_report_payload(
        built,
    )
    payload_text = json.dumps(payload_one, ensure_ascii=True, sort_keys=True).lower()

    assert payload_one == payload_two
    assert built.generated_at == GENERATED_AT
    assert payload_one["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload_one["observation_count"] == "1.000000"
    assert payload_one["rows"][0]["candidate_ref"] == candidate_ref(
        "candidate-secret-bravo",
    )
    assert payload_one["rows"][0]["market_ref"] == market_ref(
        "market-private-bravo",
        "will-bravo-resolve",
        "Will bravo resolve?",
    )
    assert payload_one["rows"][0]["evidence_ref"] == evidence_ref(*source_parts)
    assert payload_one["rows"][0]["available_depth"] == "120.000000"
    assert_no_native_numbers(payload_one)
    assert "Decimal(" not in repr(payload_one)
    assert "datetime" not in payload_text

    for raw_fragment in (
        "candidate-secret-bravo",
        "market-private-bravo",
        "will-bravo-resolve",
        "will bravo resolve",
        "research.example.invalid",
        "internal resolution note bravo",
        "postgresql://",
        "internal_resolution_table_bravo",
        "token-bravo",
        "raw_candidate_id",
        "raw_market_id",
        "raw_market_slug",
        "raw_market_question",
        "raw_source_url",
        "raw_source_text",
        "raw_source_dsn",
        "raw_source_table",
        "raw_source_token",
    ):
        assert raw_fragment.lower() not in payload_text


def test_statuses_are_limited_and_public_payloads_reject_unsafe_surfaces() -> None:
    mod = api()

    assert mod.STATUSES == ("pass", "watch", "block")

    with pytest.raises(ValueError, match="status"):
        mod.ResearchMarketDepthProbabilityResolutionMemoryGuardRow(
            candidate_ref=candidate_ref("candidate-secret"),
            market_ref=market_ref("market-secret", "slug", "question"),
            evidence_ref=evidence_ref("url", "text", "dsn", "table", "token"),
            market_probability=d("0.600000"),
            resolution_memory_probability=d("0.610000"),
            probability_gap=d("0.010000"),
            available_depth=d("120.000000"),
            required_depth_floor=d("100.000000"),
            depth_coverage_ratio=d("1.200000"),
            resolution_memory_age_hours=d("1.000000"),
            status="review",
            reason_codes=(
                "depth_coverage_clear",
                "probability_gap_clear",
                "resolution_memory_fresh",
            ),
        )

    with pytest.raises(ValueError, match="unsafe public field"):
        mod.research_market_depth_probability_resolution_memory_guard_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "derived_validation_digest": "0" * 64,
                "raw_market_question": "Will this leak?",
            },
        )

    with pytest.raises(ValueError, match="readonly"):
        mod.research_market_depth_probability_resolution_memory_guard_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": False,
                "derived_validation_digest": "0" * 64,
            },
        )

    with pytest.raises(ValueError, match="Decimal-derived strings"):
        mod.research_market_depth_probability_resolution_memory_guard_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "observation_count": 1,
                "derived_validation_digest": "0" * 64,
            },
        )

    with pytest.raises(ValueError, match="unsafe public value"):
        mod.research_market_depth_probability_resolution_memory_guard_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "mode": "https://example.invalid/path",
                "derived_validation_digest": "0" * 64,
            },
        )


def test_decimal_only_flags_frozen_dataclasses_and_exact_types() -> None:
    built = report(observation())

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].market_probability = d("0")  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadReport(
            api().ResearchMarketDepthProbabilityResolutionMemoryGuardReport,
        ):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(observation(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(built.rows[0], readonly=False)
    with pytest.raises(ValueError, match="Decimal"):
        observation(market_probability=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        observation(resolution_memory_probability=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="between zero and one"):
        observation(market_probability=d("1.000001"))
    with pytest.raises(ValueError, match="watch_depth_coverage_ratio"):
        config(
            watch_depth_coverage_ratio=d("0.400000"),
            block_depth_coverage_ratio=d("0.500000"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(observation(), generated_at=_DatetimeSubclass(2026, 7, 9, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        report(observation(), generated_at=datetime(2026, 7, 9))


def test_owned_module_has_no_forbidden_operational_imports_or_calls() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_depth_probability_resolution_memory_guard_report.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    forbidden_import_roots = {
        "aiohttp",
        "ccxt",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "subprocess",
        "urllib",
        "web3",
    }
    forbidden_call_names = {"connect", "execute", "open", "request"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            if isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names
