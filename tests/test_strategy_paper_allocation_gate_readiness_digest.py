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
    / "strategy_paper_allocation_gate_readiness_digest.py"
)
GENERATED_AT = datetime(2026, 7, 4, 14, 0, tzinfo=UTC)
EVALUATED_AT = datetime(2026, 7, 4, 13, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _MissingOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_paper_allocation_gate_readiness_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_PAPER_ALLOCATION_GATE_READINESS_DIGEST_CONFIG_VERSION
        ),
        "max_ready_allocation_fraction": d("0.050000"),
        "max_watch_allocation_fraction": d("0.020000"),
        "min_ready_team_memory_weight": d("0.700000"),
        "min_watch_team_memory_weight": d("0.500000"),
        "min_ready_expected_value_buffer": d("0.030000"),
        "min_watch_expected_value_buffer": d("0.010000"),
        "min_ready_available_paper_budget": d("100.000000"),
        "min_watch_available_paper_budget": d("25.000000"),
    }
    values.update(overrides)
    return module.StrategyPaperAllocationGateReadinessDigestConfig(**values)


def candidate(**overrides: object) -> Any:
    module = api()
    values = {
        "candidate_reference": "public-alpha",
        "market_slug": "alpha-market",
        "category": "macro",
        "evaluated_at": EVALUATED_AT,
        "recommendation_gate_status": "pass",
        "portfolio_correlation_status": "pass",
        "category_rotation_status": "hold",
        "team_memory_weight": d("0.900000"),
        "expected_value_buffer": d("0.060000"),
        "available_paper_budget": d("200.000000"),
        "reason_codes": ("candidate_input",),
    }
    values.update(overrides)
    return module.StrategyPaperAllocationGateReadinessCandidate(**values)


def report(
    *candidates: object,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_strategy_paper_allocation_gate_readiness_digest(
        candidates,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_public_numeric_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_public_numeric_values(item)


def test_digest_combines_gate_inputs_into_sorted_allocation_readiness_rows() -> None:
    result = report(
        candidate(
            candidate_reference="ready-alpha",
            market_slug="gamma-ready",
            category="macro",
            team_memory_weight=d("0.900000"),
            expected_value_buffer=d("0.060000"),
            available_paper_budget=d("200.000000"),
        ),
        candidate(
            candidate_reference="watch-alpha",
            market_slug="beta-watch",
            category="sports",
            portfolio_correlation_status="watch",
            team_memory_weight=d("0.600000"),
            expected_value_buffer=d("0.020000"),
            available_paper_budget=d("60.000000"),
        ),
        candidate(
            candidate_reference="secret-wallet-token-alpha",
            market_slug="alpha-blocked",
            category="crypto",
            recommendation_gate_status="blocked",
            team_memory_weight=d("0.400000"),
            expected_value_buffer=d("-0.010000"),
            available_paper_budget=d("0.000000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == (
        "strategy-paper-allocation-gate-readiness-digest-v0"
    )
    assert result.candidate_count == d("3")
    assert result.ready_count == d("1")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.total_available_paper_budget == d("260.000000")
    assert result.max_suggested_paper_allocation_fraction == d("0.045000")
    assert result.min_team_memory_weight == d("0.400000")
    assert result.min_expected_value_buffer == d("-0.010000")
    assert result.status == "blocked"
    assert result.reason_codes == (
        "allocation_gate_blocked",
        "allocation_gate_watch",
        "allocation_gate_ready",
        "recommendation_gate_blocked",
        "recommendation_gate_passed",
        "portfolio_correlation_watch",
        "portfolio_correlation_passed",
        "category_rotation_hold",
        "team_memory_weight_blocked",
        "team_memory_weight_watch",
        "team_memory_weight_ready",
        "expected_value_buffer_blocked",
        "expected_value_buffer_watch",
        "expected_value_buffer_ready",
        "paper_budget_blocked",
        "paper_budget_watch",
        "paper_budget_ready",
        "candidate_input",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.market_slug for row in result.rows) == (
        "alpha-blocked",
        "beta-watch",
        "gamma-ready",
    )
    blocked, watched, ready = result.rows

    assert blocked.allocation_readiness_status == "blocked"
    assert blocked.suggested_paper_allocation_fraction == ZERO
    assert blocked.redacted_candidate_reference.startswith("candidate_ref_")
    assert "secret" not in repr(blocked).lower()
    assert "wallet" not in repr(blocked).lower()
    assert "token" not in repr(blocked).lower()
    assert blocked.reason_codes == (
        "candidate_input",
        "allocation_gate_blocked",
        "recommendation_gate_blocked",
        "portfolio_correlation_passed",
        "category_rotation_hold",
        "team_memory_weight_blocked",
        "expected_value_buffer_blocked",
        "paper_budget_blocked",
    )

    assert watched.allocation_readiness_status == "watch"
    assert watched.suggested_paper_allocation_fraction == d("0.012000")
    assert watched.readiness_score == d("0.727778")
    assert watched.reason_codes == (
        "candidate_input",
        "allocation_gate_watch",
        "recommendation_gate_passed",
        "portfolio_correlation_watch",
        "category_rotation_hold",
        "team_memory_weight_watch",
        "expected_value_buffer_watch",
        "paper_budget_watch",
    )

    assert ready.allocation_readiness_status == "ready"
    assert ready.suggested_paper_allocation_fraction == d("0.045000")
    assert ready.readiness_score == d("0.983333")
    assert ready.reason_codes == (
        "candidate_input",
        "allocation_gate_ready",
        "recommendation_gate_passed",
        "portfolio_correlation_passed",
        "category_rotation_hold",
        "team_memory_weight_ready",
        "expected_value_buffer_ready",
        "paper_budget_ready",
    )


def test_empty_report_is_watch_zeroed_decimal_and_readonly() -> None:
    empty = report()

    assert empty.candidate_count == d("0")
    assert empty.ready_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.blocked_count == d("0")
    assert empty.total_available_paper_budget == ZERO
    assert empty.max_suggested_paper_allocation_fraction == ZERO
    assert empty.min_team_memory_weight == ZERO
    assert empty.min_expected_value_buffer == ZERO
    assert empty.status == "watch"
    assert empty.reason_codes == (
        "strategy_paper_allocation_gate_readiness_digest_empty",
    )
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    populated = report(candidate())
    for value in (empty, populated, *populated.rows):
        for item in fields(value):
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(
                (
                    "_count",
                    "_budget",
                    "_fraction",
                    "_weight",
                    "_buffer",
                    "_score",
                ),
            ):
                assert type(item_value) is Decimal


def test_payload_redacts_references_uses_decimal_strings_and_rejects_public_numbers() -> None:
    module = api()
    result = report(
        candidate(
            candidate_reference="secret-wallet-token-alpha",
            market_slug="payload-market",
            category="crypto",
            recommendation_gate_status="watch",
            team_memory_weight=d("0.600000"),
            expected_value_buffer=d("0.020000"),
            available_paper_budget=d("60.000000"),
            evaluated_at=datetime(2026, 7, 4, 6, 45, tzinfo=timezone(timedelta(hours=-7))),
        ),
        generated_at=datetime(2026, 7, 4, 7, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.strategy_paper_allocation_gate_readiness_digest_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True)
    assert payload["generated_at"] == "2026-07-04T14:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["total_available_paper_budget"] == "60.000000"
    assert payload["max_suggested_paper_allocation_fraction"] == "0.012000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["evaluated_at"] == "2026-07-04T13:45:00+00:00"
    assert payload["rows"][0]["redacted_candidate_reference"].startswith(
        "candidate_ref_",
    )
    assert payload["rows"][0]["suggested_paper_allocation_fraction"] == "0.012000"
    assert "secret-wallet-token-alpha" not in rendered
    assert "wallet" not in rendered.lower()
    assert "token" not in rendered.lower()
    assert_no_public_numeric_values(payload)

    unsafe_report = replace(result)
    object.__setattr__(unsafe_report, "extra_public_count", 1)
    with pytest.raises(ValueError, match="public payload numeric"):
        module.strategy_paper_allocation_gate_readiness_digest_payload(unsafe_report)


def test_validation_rejects_bad_types_datetimes_duplicates_flags_and_consistency() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_strategy_paper_allocation_gate_readiness_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="team_memory_weight must be a Decimal"):
        candidate(team_memory_weight=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="available_paper_budget must be a Decimal"):
        candidate(available_paper_budget=200)
    with pytest.raises(ValueError, match="expected_value_buffer must be a Decimal"):
        candidate(expected_value_buffer=_DecimalSubclass("0.060000"))
    with pytest.raises(ValueError, match="team_memory_weight"):
        candidate(team_memory_weight=d("1.000001"))
    with pytest.raises(ValueError, match="available_paper_budget must be nonnegative"):
        candidate(available_paper_budget=d("-0.000001"))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(candidate(), generated_at=datetime(2026, 7, 4, 14, 0))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            candidate(),
            generated_at=datetime(2026, 7, 4, 14, 0, tzinfo=_MissingOffsetTz()),
        )
    with pytest.raises(ValueError, match="evaluated_at must be exactly datetime"):
        candidate(evaluated_at=_DatetimeSubclass(2026, 7, 4, 13, 45, tzinfo=UTC))
    with pytest.raises(ValueError, match="evaluated_at must not be after generated_at"):
        report(candidate(evaluated_at=datetime(2026, 7, 4, 14, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="duplicate candidate_reference"):
        report(candidate(), candidate())
    with pytest.raises(ValueError, match="max_watch_allocation_fraction"):
        config(max_watch_allocation_fraction=d("0.060000"))
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)

    result = report(
        candidate(candidate_reference="ready-alpha", market_slug="alpha"),
        candidate(
            candidate_reference="blocked-beta",
            market_slug="beta",
            category_rotation_status="rotate_out",
        ),
    )
    with pytest.raises(FrozenInstanceError):
        result.ready_count = d("9")  # type: ignore[misc]
    with pytest.raises(ValueError, match="ready_count"):
        replace(result, ready_count=d("0"))
    with pytest.raises(ValueError, match="rows must be sorted"):
        replace(result, rows=tuple(reversed(result.rows)))
    with pytest.raises(ValueError, match="suggested_paper_allocation_fraction"):
        replace(result.rows[0], suggested_paper_allocation_fraction=d("0.010000"))
    with pytest.raises(ValueError, match="redacted_candidate_reference"):
        replace(result.rows[0], redacted_candidate_reference="public-alpha")


def test_payload_requires_report_type_hard_flags_and_safe_public_text() -> None:
    module = api()
    result = report(candidate())

    with pytest.raises(ValueError, match="report must be"):
        module.strategy_paper_allocation_gate_readiness_digest_payload(object())
    with pytest.raises(ValueError, match="report_only must be True"):
        module.strategy_paper_allocation_gate_readiness_digest_payload(
            replace(result, report_only=False),
        )

    unsafe_report = replace(result)
    object.__setattr__(unsafe_report.rows[0], "redacted_candidate_reference", "secret-token")
    with pytest.raises(ValueError, match="unsafe public text"):
        module.strategy_paper_allocation_gate_readiness_digest_payload(unsafe_report)


def test_module_scope_has_no_persistence_network_file_io_or_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_terms = (
        "psycopg",
        "supabase",
        "sqlite",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "read_text",
        "write_text",
    )
    for forbidden in forbidden_terms:
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imported_names = [alias.name for alias in node.names]
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_names.append(node.module)
            for imported in imported_names:
                assert not any(term in imported.lower() for term in forbidden_terms)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {
                "open",
                "connect",
                "execute",
                "fetch",
                "request",
                "submit",
            }
