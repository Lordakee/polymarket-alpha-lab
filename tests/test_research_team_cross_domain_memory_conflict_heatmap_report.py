from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_cross_domain_memory_conflict_heatmap_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 11, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _MissingOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_cross_domain_memory_conflict_heatmap_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "watch_conflict_pressure_score": d("0.250000"),
        "block_conflict_pressure_score": d("0.700000"),
        "block_unresolved_review_age_hours": d("72.000000"),
    }
    values.update(overrides)
    return module.ResearchTeamCrossDomainMemoryConflictHeatmapConfig(**values)


def observation(**overrides: object) -> Any:
    module = api()
    values = {
        "domain_a": "macro_rates",
        "domain_b": "crypto_research",
        "memory_freshness_score": d("0.900000"),
        "contradiction_score": d("0.050000"),
        "calibration_feedback_score": d("0.100000"),
        "unresolved_review_age_hours": d("2.000000"),
        "observed_at": OBSERVED_AT,
    }
    values.update(overrides)
    return module.ResearchTeamCrossDomainMemoryConflictObservation(**values)


def build_report(
    *items: object,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_team_cross_domain_memory_conflict_heatmap_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_public_float_or_int(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_float_or_int(item)


def assert_no_decimal_or_datetime(value: Any) -> None:
    if isinstance(value, (Decimal, datetime)):
        raise AssertionError(f"unexpected raw public value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_decimal_or_datetime(item)
    if isinstance(value, list):
        for item in value:
            assert_no_decimal_or_datetime(item)


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


def test_builds_cross_domain_memory_conflict_heatmap_from_sanitized_pairs() -> None:
    module = api()
    result = build_report(
        observation(
            domain_a="macro_rates",
            domain_b="crypto_research",
            memory_freshness_score=d("0.200000"),
            contradiction_score=d("0.900000"),
            calibration_feedback_score=d("0.800000"),
            unresolved_review_age_hours=d("80.000000"),
        ),
        observation(
            domain_a="crypto_research",
            domain_b="macro_rates",
            memory_freshness_score=d("0.400000"),
            contradiction_score=d("0.700000"),
            calibration_feedback_score=d("0.600000"),
            unresolved_review_age_hours=d("40.000000"),
        ),
        observation(
            domain_a="macro_rates",
            domain_b="sports_research",
            memory_freshness_score=d("0.800000"),
            contradiction_score=d("0.400000"),
            calibration_feedback_score=d("0.300000"),
            unresolved_review_age_hours=d("24.000000"),
        ),
        observation(
            domain_a="sports_research",
            domain_b="weather_research",
            memory_freshness_score=d("0.950000"),
            contradiction_score=d("0.050000"),
            calibration_feedback_score=d("0.050000"),
            unresolved_review_age_hours=d("1.000000"),
        ),
    )

    assert is_dataclass(result)
    assert module.PUBLIC_STATUSES == ("pass", "watch", "block")
    assert result.generated_at == GENERATED_AT
    assert result.config_version == (
        "research-team-cross-domain-memory-conflict-heatmap-report-v0"
    )
    assert result.status == "block"
    assert result.domain_pair_count == d("3")
    assert result.observation_count == d("4")
    assert result.domain_count == d("4")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.freshness_pressure_count == d("1")
    assert result.contradiction_pressure_count == d("2")
    assert result.calibration_feedback_pressure_count == d("2")
    assert result.unresolved_review_age_pressure_count == d("2")
    assert result.max_conflict_pressure_score == d("0.800000")
    assert result.average_conflict_pressure_score == d("0.383102")
    assert result.reason_codes == (
        "cross_domain_memory_conflict_heatmap_block",
        "memory_freshness_pressure_block",
        "memory_contradiction_pressure_block",
        "calibration_feedback_pressure_block",
        "unresolved_review_age_pressure_block",
        "memory_contradiction_pressure_watch",
        "calibration_feedback_pressure_watch",
        "unresolved_review_age_pressure_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64

    block_cell, watch_cell, pass_cell = result.cells
    assert (block_cell.domain_a, block_cell.domain_b) == (
        "crypto_research",
        "macro_rates",
    )
    assert block_cell.status == "block"
    assert block_cell.observation_count == d("2")
    assert block_cell.average_memory_freshness_score == d("0.300000")
    assert block_cell.freshness_pressure_score == d("0.700000")
    assert block_cell.average_contradiction_score == d("0.800000")
    assert block_cell.average_calibration_feedback_score == d("0.700000")
    assert block_cell.max_unresolved_review_age_hours == d("80.000000")
    assert block_cell.unresolved_review_age_pressure_score == d("1.000000")
    assert block_cell.conflict_pressure_score == d("0.800000")
    assert block_cell.reason_codes == (
        "cross_domain_memory_conflict_heatmap_block",
        "memory_freshness_pressure_block",
        "memory_contradiction_pressure_block",
        "calibration_feedback_pressure_block",
        "unresolved_review_age_pressure_block",
    )

    assert (watch_cell.domain_a, watch_cell.domain_b) == (
        "macro_rates",
        "sports_research",
    )
    assert watch_cell.status == "watch"
    assert watch_cell.conflict_pressure_score == d("0.308333")
    assert pass_cell.status == "pass"
    assert pass_cell.reason_codes == ("cross_domain_memory_conflict_clear",)


def test_watch_only_heatmap_accepts_watch_rollup_reason_code() -> None:
    result = build_report(
        observation(
            domain_a="macro_rates",
            domain_b="sports_research",
            memory_freshness_score=d("0.800000"),
            contradiction_score=d("0.400000"),
            calibration_feedback_score=d("0.300000"),
            unresolved_review_age_hours=d("24.000000"),
        ),
    )

    assert result.status == "watch"
    assert result.domain_pair_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("0")
    assert result.reason_codes == (
        "cross_domain_memory_conflict_heatmap_watch",
        "memory_contradiction_pressure_watch",
        "calibration_feedback_pressure_watch",
        "unresolved_review_age_pressure_watch",
    )


def test_empty_heatmap_is_pass_report_only_and_decimal_counted() -> None:
    result = build_report()

    assert result.domain_pair_count == d("0")
    assert result.observation_count == d("0")
    assert result.domain_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.freshness_pressure_count == d("0")
    assert result.contradiction_pressure_count == d("0")
    assert result.calibration_feedback_pressure_count == d("0")
    assert result.unresolved_review_age_pressure_count == d("0")
    assert result.max_conflict_pressure_score == d("0.000000")
    assert result.average_conflict_pressure_score == d("0.000000")
    assert result.status == "pass"
    assert result.reason_codes == ("cross_domain_memory_conflict_heatmap_empty",)
    assert result.reason_code_counts == ()
    assert result.cells == ()

    populated = build_report(observation())
    for value in (result, populated, *populated.cells, *populated.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item.name.endswith(("_count", "_score", "_hours", "_ratio")):
                assert type(item_value) is Decimal


def test_public_payload_is_stable_decimal_only_and_digest_checked() -> None:
    module = api()
    first = build_report(
        observation(
            domain_a="crypto_research",
            domain_b="macro_rates",
            memory_freshness_score=d("0.400000"),
            contradiction_score=d("0.700000"),
            calibration_feedback_score=d("0.600000"),
            unresolved_review_age_hours=d("40.000000"),
            observed_at=datetime(2026, 7, 8, 4, 30, tzinfo=timezone(timedelta(hours=-7))),
        ),
        observation(
            domain_a="macro_rates",
            domain_b="crypto_research",
            memory_freshness_score=d("0.200000"),
            contradiction_score=d("0.900000"),
            calibration_feedback_score=d("0.800000"),
            unresolved_review_age_hours=d("80.000000"),
        ),
        generated_at=datetime(2026, 7, 8, 5, tzinfo=timezone(timedelta(hours=-7))),
    )
    second = build_report(
        observation(
            domain_a="macro_rates",
            domain_b="crypto_research",
            memory_freshness_score=d("0.200000"),
            contradiction_score=d("0.900000"),
            calibration_feedback_score=d("0.800000"),
            unresolved_review_age_hours=d("80.000000"),
        ),
        observation(
            domain_a="crypto_research",
            domain_b="macro_rates",
            memory_freshness_score=d("0.400000"),
            contradiction_score=d("0.700000"),
            calibration_feedback_score=d("0.600000"),
            unresolved_review_age_hours=d("40.000000"),
            observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=UTC),
        ),
    )

    payload = module.research_team_cross_domain_memory_conflict_heatmap_report_payload(first)
    repeat_payload = module.research_team_cross_domain_memory_conflict_heatmap_report_payload(
        second,
    )

    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload == repeat_payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["domain_pair_count"] == "1"
    assert payload["cells"][0]["conflict_pressure_score"] == "0.800000"
    assert payload["cells"][0]["latest_observed_at"] == "2026-07-08T11:30:00+00:00"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert_no_public_float_or_int(payload)
    assert_no_decimal_or_datetime(payload)
    json.dumps(payload, sort_keys=True)

    encoded = json.dumps(payload, sort_keys=True).lower()
    forbidden_fragments = (
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
        "sizing",
        "recommendation",
    )
    assert not any(
        fragment in key.lower()
        for key in payload_keys(payload)
        for fragment in forbidden_fragments
    )
    assert not any(fragment in encoded for fragment in forbidden_fragments)

    tampered = dict(payload)
    tampered["pass_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_cross_domain_memory_conflict_heatmap_report_payload(tampered)

    with pytest.raises(ValueError, match="pass_count|derived_validation_digest"):
        replace(first, pass_count=d("2"))


def test_rejects_bad_types_unsafe_labels_times_statuses_flags_and_tampering() -> None:
    module = api()
    result = build_report(observation())
    cell = result.cells[0]
    payload = module.research_team_cross_domain_memory_conflict_heatmap_report_payload(result)

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        cell.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="Decimal"):
        observation(memory_freshness_score=1)
    with pytest.raises(ValueError, match="Decimal"):
        observation(contradiction_score=0.5)
    with pytest.raises(ValueError, match="Decimal"):
        observation(unresolved_review_age_hours=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(observation(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 8, 11, 0))
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 8, 11, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 8, 11, 0, tzinfo=_MissingOffsetTz()))
    with pytest.raises(ValueError, match="future"):
        build_report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="domain_a"):
        observation(domain_a="market_slug")
    with pytest.raises(ValueError, match="domain_b"):
        observation(domain_b="source_text")
    with pytest.raises(ValueError, match="domain"):
        observation(domain_a="macro_rates", domain_b="macro_rates")
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_report(observation(), cfg=object())
    with pytest.raises(ValueError, match="status"):
        replace(cell, status="blocked")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)

    unsafe = dict(payload)
    unsafe["source_text"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_team_cross_domain_memory_conflict_heatmap_report_payload(unsafe)

    numeric = dict(payload)
    numeric["domain_pair_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        module.research_team_cross_domain_memory_conflict_heatmap_report_payload(numeric)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.research_team_cross_domain_memory_conflict_heatmap_report_payload(downgraded)


def test_module_is_report_only_without_external_write_or_execution_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    banned_import_roots = {
        "http",
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
