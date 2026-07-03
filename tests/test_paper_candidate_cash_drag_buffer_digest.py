from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 18, 0, tzinfo=UTC)
EVALUATED_AT = datetime(2026, 7, 2, 17, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.paper_candidate_cash_drag_buffer_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "paper-candidate-cash-drag-buffer-digest-v0",
        "watch_cash_drag_ratio": d("0.100000"),
        "blocked_cash_drag_ratio": d("0.200000"),
        "minimum_buffer_ratio": d("0.050000"),
    }
    values.update(overrides)
    return module.PaperCandidateCashDragBufferDigestConfig(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_reference": "public-alpha",
        "market_reference": "market-secret-alpha",
        "side": "yes",
        "evaluated_at": EVALUATED_AT,
        "proposed_notional": d("100.000000"),
        "available_cash": d("1000.000000"),
        "pending_cash_drag": d("25.000000"),
        "cash_buffer": d("100.000000"),
        "reason_codes": ("candidate_screened",),
    }
    values.update(overrides)
    return module.PaperCandidateCashDragBufferDigestCandidate(**values)


def report(*, candidates=(), cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_paper_candidate_cash_drag_buffer_digest(
        candidates,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_or_decimal_payload_values(value: Any) -> None:
    if isinstance(value, (float, Decimal)):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_decimal_payload_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_decimal_payload_values(item)


def test_digest_calculates_cash_drag_buffer_metrics_reason_codes_and_sorting() -> None:
    result = report(
        candidates=(
            candidate(
                candidate_reference="pass-alpha",
                proposed_notional=d("100.000000"),
                pending_cash_drag=d("25.000000"),
                cash_buffer=d("100.000000"),
            ),
            candidate(
                candidate_reference="watch-alpha",
                proposed_notional=d("100.000000"),
                pending_cash_drag=d("125.000000"),
                cash_buffer=d("100.000000"),
            ),
            candidate(
                candidate_reference="secret-market-token-alpha",
                proposed_notional=d("100.000000"),
                pending_cash_drag=d("250.000000"),
                cash_buffer=d("25.000000"),
            ),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "paper-candidate-cash-drag-buffer-digest-v0"
    assert result.candidate_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.total_proposed_notional == d("300.000000")
    assert result.total_pending_cash_drag == d("400.000000")
    assert result.total_cash_buffer == d("225.000000")
    assert result.max_cash_drag_ratio == d("0.250000")
    assert result.min_buffer_coverage_ratio == d("0.100000")
    assert result.max_buffer_shortfall == d("225.000000")
    assert result.status == "blocked"
    assert result.reason_codes == (
        "cash_drag_ratio_blocked",
        "cash_drag_ratio_watch",
        "cash_drag_buffer_passed",
        "pending_cash_drag_present",
        "cash_buffer_shortfall_present",
        "minimum_buffer_coverage_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    blocked, watched, passed = result.rows
    assert tuple(row.cash_drag_buffer_status for row in result.rows) == (
        "blocked",
        "watch",
        "pass",
    )
    assert blocked.redacted_candidate_reference.startswith("candidate_ref_")
    assert blocked.redacted_market_reference.startswith("market_ref_")
    assert "secret" not in blocked.redacted_candidate_reference
    assert "token" not in blocked.redacted_candidate_reference
    assert blocked.proposed_notional == d("100.000000")
    assert blocked.available_cash == d("1000.000000")
    assert blocked.pending_cash_drag == d("250.000000")
    assert blocked.cash_buffer == d("25.000000")
    assert blocked.required_cash_buffer == d("250.000000")
    assert blocked.buffer_shortfall == d("225.000000")
    assert blocked.cash_drag_ratio == d("0.250000")
    assert blocked.buffer_coverage_ratio == d("0.100000")
    assert blocked.cash_drag_buffer_status == "blocked"
    assert blocked.reason_codes == (
        "candidate_screened",
        "cash_drag_ratio_blocked",
        "pending_cash_drag_present",
        "cash_buffer_shortfall_present",
        "minimum_buffer_coverage_watch",
    )

    assert watched.cash_drag_ratio == d("0.125000")
    assert watched.required_cash_buffer == d("125.000000")
    assert watched.buffer_shortfall == d("25.000000")
    assert watched.buffer_coverage_ratio == d("0.800000")
    assert watched.cash_drag_buffer_status == "watch"
    assert watched.reason_codes == (
        "candidate_screened",
        "cash_drag_ratio_watch",
        "pending_cash_drag_present",
        "cash_buffer_shortfall_present",
    )

    assert passed.cash_drag_ratio == d("0.025000")
    assert passed.required_cash_buffer == d("25.000000")
    assert passed.buffer_shortfall == ZERO
    assert passed.buffer_coverage_ratio == d("4.000000")
    assert passed.cash_drag_buffer_status == "pass"
    assert passed.reason_codes == (
        "candidate_screened",
        "cash_drag_buffer_passed",
        "pending_cash_drag_present",
    )


def test_candidate_and_row_reason_codes_are_deduplicated() -> None:
    result = report(
        candidates=(
            candidate(
                reason_codes=(
                    "candidate_screened",
                    "candidate_screened",
                    "pending_cash_drag_present",
                ),
            ),
        ),
    )

    assert result.rows[0].reason_codes == (
        "candidate_screened",
        "cash_drag_buffer_passed",
        "pending_cash_drag_present",
    )


def test_empty_report_is_watch_zeroed_decimal_and_readonly() -> None:
    empty = report()

    assert empty.candidate_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.blocked_count == d("0")
    assert empty.total_proposed_notional == ZERO
    assert empty.total_pending_cash_drag == ZERO
    assert empty.total_cash_buffer == ZERO
    assert empty.max_cash_drag_ratio == ZERO
    assert empty.min_buffer_coverage_ratio == ZERO
    assert empty.max_buffer_shortfall == ZERO
    assert empty.status == "watch"
    assert empty.reason_codes == ("cash_drag_buffer_digest_empty",)
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    populated = report(candidates=(candidate(),))
    for value in (empty, *populated.rows, populated):
        for item in fields(value):
            if item.name in {
                "paper_only",
                "report_only",
                "readonly",
                "reason_codes",
                "rows",
                "generated_at",
                "evaluated_at",
                "config_version",
                "candidate_reference",
                "market_reference",
                "redacted_candidate_reference",
                "redacted_market_reference",
                "side",
                "status",
                "cash_drag_buffer_status",
            }:
                continue
            assert type(getattr(value, item.name)) is Decimal


def test_payload_redacts_references_uses_decimal_strings_and_no_floats() -> None:
    module = api()
    result = report(
        candidates=(
            candidate(
                candidate_reference="secret-market-token-alpha",
                market_reference="private-market-key-alpha",
                pending_cash_drag=d("250.000000"),
                cash_buffer=d("25.000000"),
            ),
        ),
        generated_at=datetime(2026, 7, 2, 11, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.paper_candidate_cash_drag_buffer_digest_payload(result)
    rendered = repr(payload).lower()
    assert payload["generated_at"] == "2026-07-02T18:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["total_cash_buffer"] == "25.000000"
    assert payload["max_buffer_shortfall"] == "225.000000"
    assert payload["rows"][0]["redacted_candidate_reference"].startswith(
        "candidate_ref_",
    )
    assert payload["rows"][0]["redacted_market_reference"].startswith("market_ref_")
    assert payload["rows"][0]["buffer_coverage_ratio"] == "0.100000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["rows"][0]["report_only"] is True
    assert payload["rows"][0]["readonly"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "secret-market" not in rendered
    assert "private-market" not in rendered
    assert "token" not in rendered
    assert "key" not in rendered
    assert_no_float_or_decimal_payload_values(payload)
    json.dumps(payload, sort_keys=True)


def test_validation_rejects_bad_types_nonfinite_values_duplicates_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_paper_candidate_cash_drag_buffer_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        module.PaperCandidateCashDragBufferDigestReport(
            generated_at=_DatetimeSubclass(2026, 7, 2, 18, 0, tzinfo=UTC),
            config_version="paper-candidate-cash-drag-buffer-digest-v0",
            candidate_count=ZERO,
            pass_count=ZERO,
            watch_count=ZERO,
            blocked_count=ZERO,
            total_proposed_notional=ZERO,
            total_pending_cash_drag=ZERO,
            total_cash_buffer=ZERO,
            max_cash_drag_ratio=ZERO,
            min_buffer_coverage_ratio=ZERO,
            max_buffer_shortfall=ZERO,
            status="watch",
            reason_codes=("cash_drag_buffer_digest_empty",),
            rows=(),
        )
    with pytest.raises(ValueError, match="proposed_notional"):
        candidate(proposed_notional=100.0)
    with pytest.raises(ValueError, match="available_cash"):
        candidate(available_cash=_DecimalSubclass("1000.000000"))
    with pytest.raises(ValueError, match="pending_cash_drag"):
        candidate(pending_cash_drag=Decimal("Infinity"))
    with pytest.raises(ValueError, match="proposed_notional must be positive"):
        candidate(proposed_notional=ZERO)
    with pytest.raises(ValueError, match="available_cash must be positive"):
        candidate(available_cash=ZERO)
    with pytest.raises(ValueError, match="cash_buffer must be nonnegative"):
        candidate(cash_buffer=d("-0.000001"))
    with pytest.raises(ValueError, match="candidate_reference"):
        candidate(candidate_reference=" public-alpha")
    with pytest.raises(ValueError, match="evaluated_at must not be after generated_at"):
        report(candidates=(candidate(evaluated_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="duplicate candidate_reference"):
        report(candidates=(candidate(), candidate()))
    with pytest.raises(ValueError, match="report_only"):
        replace(config(), report_only=False)

    frozen = candidate()
    with pytest.raises(FrozenInstanceError):
        frozen.side = "no"  # type: ignore[misc]


def test_report_rejects_nonintegral_count_fields() -> None:
    module = api()

    with pytest.raises(ValueError, match="candidate_count"):
        module.PaperCandidateCashDragBufferDigestReport(
            generated_at=GENERATED_AT,
            config_version="paper-candidate-cash-drag-buffer-digest-v0",
            candidate_count=d("1.5"),
            pass_count=d("0"),
            watch_count=d("0"),
            blocked_count=d("0"),
            total_proposed_notional=ZERO,
            total_pending_cash_drag=ZERO,
            total_cash_buffer=ZERO,
            max_cash_drag_ratio=ZERO,
            min_buffer_coverage_ratio=ZERO,
            max_buffer_shortfall=ZERO,
            status="watch",
            reason_codes=("cash_drag_buffer_digest_empty",),
            rows=(),
        )


def test_datetimes_are_normalized_to_utc() -> None:
    result = report(
        candidates=(
            candidate(
                evaluated_at=datetime(
                    2026,
                    7,
                    2,
                    13,
                    45,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
            ),
        ),
    )

    assert result.rows[0].evaluated_at == datetime(2026, 7, 2, 17, 45, tzinfo=UTC)
    assert result.rows[0].evaluated_at.tzinfo is UTC


def test_rows_sort_deterministically_by_severity_shortfall_and_reference() -> None:
    result = report(
        candidates=(
            candidate(
                candidate_reference="zulu-blocked",
                pending_cash_drag=d("250.000000"),
                cash_buffer=d("50.000000"),
            ),
            candidate(
                candidate_reference="alpha-blocked",
                pending_cash_drag=d("250.000000"),
                cash_buffer=d("25.000000"),
            ),
            candidate(
                candidate_reference="bravo-watch",
                pending_cash_drag=d("125.000000"),
            ),
            candidate(
                candidate_reference="charlie-pass",
                pending_cash_drag=d("25.000000"),
                cash_buffer=d("100.000000"),
            ),
        ),
    )

    assert tuple(row.cash_drag_buffer_status for row in result.rows) == (
        "blocked",
        "blocked",
        "watch",
        "pass",
    )
    assert tuple(row.buffer_shortfall for row in result.rows) == (
        d("225.000000"),
        d("200.000000"),
        d("25.000000"),
        ZERO,
    )


def test_report_rejects_misordered_rows_and_mismatched_aggregates() -> None:
    result = report(
        candidates=(
            candidate(
                candidate_reference="blocked-alpha",
                pending_cash_drag=d("250.000000"),
                cash_buffer=d("25.000000"),
            ),
            candidate(
                candidate_reference="watch-alpha",
                pending_cash_drag=d("125.000000"),
            ),
        ),
    )

    with pytest.raises(ValueError, match="deterministically sorted"):
        replace(result, rows=tuple(reversed(result.rows)))

    with pytest.raises(ValueError, match="total_proposed_notional"):
        replace(result, total_proposed_notional=d("999.000000"))
    with pytest.raises(ValueError, match="total_pending_cash_drag"):
        replace(result, total_pending_cash_drag=d("999.000000"))
    with pytest.raises(ValueError, match="total_cash_buffer"):
        replace(result, total_cash_buffer=d("999.000000"))
    with pytest.raises(ValueError, match="max_cash_drag_ratio"):
        replace(result, max_cash_drag_ratio=d("0.999999"))
    with pytest.raises(ValueError, match="min_buffer_coverage_ratio"):
        replace(result, min_buffer_coverage_ratio=d("0.999999"))
    with pytest.raises(ValueError, match="max_buffer_shortfall"):
        replace(result, max_buffer_shortfall=d("999.000000"))


def test_payload_requires_report_type_and_hard_flags() -> None:
    module = api()
    result = report(candidates=(candidate(),))

    with pytest.raises(ValueError, match="report must be"):
        module.paper_candidate_cash_drag_buffer_digest_payload(object())

    with pytest.raises(ValueError, match="report_only must be True"):
        module.paper_candidate_cash_drag_buffer_digest_payload(
            replace(result, report_only=False),
        )


def test_module_has_no_external_io_or_unsafe_surface_terms() -> None:
    source_path = Path(
        "src/polymarket_alpha_lab/paper_candidate_cash_drag_buffer_digest.py",
    )
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "pathlib",
    }
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert imports.isdisjoint(forbidden_import_roots)

    forbidden_calls = {"open", "connect", "execute", "urlopen"}
    call_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert call_names.isdisjoint(forbidden_calls)

    lowered_source = source.lower()
    for forbidden in (
        "live",
        "trading",
        "auth",
        "wallet",
        "order",
        "account",
        "advice",
    ):
        assert forbidden not in lowered_source
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
