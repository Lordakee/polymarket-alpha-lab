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


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.candidate_settlement_cash_drag_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "candidate-settlement-cash-drag-score-v0",
        "watch_score_threshold": d("0.250000"),
        "blocked_score_threshold": d("0.700000"),
        "notional_risk_cap": d("10000.000000"),
        "watch_paper_notional": d("5000.000000"),
        "resolution_days_cap": d("90.000000"),
        "watch_resolution_days": d("30.000000"),
        "blocked_resolution_days": d("90.000000"),
        "settlement_lag_days_cap": d("30.000000"),
        "watch_settlement_lag_days": d("7.000000"),
        "blocked_settlement_lag_days": d("14.000000"),
        "minimum_fee_cost_buffer_ratio": d("0.010000"),
    }
    values.update(overrides)
    return module.CandidateSettlementCashDragScoreConfig(**values)


def facts(**overrides: object):
    module = api()
    values = {
        "redacted_candidate_reference": "candidate_ref_aaaaaaaaaaaaaaaa",
        "redacted_market_reference": "market_ref_bbbbbbbbbbbbbbbb",
        "proposed_paper_notional": d("100.000000"),
        "days_to_expected_resolution": d("3.000000"),
        "settlement_lag_days": d("1.000000"),
        "dispute_revision_risk": d("0.000000"),
        "portfolio_cash_lockup_pressure": d("0.050000"),
        "fee_cost_buffer": d("2.000000"),
    }
    values.update(overrides)
    return module.CandidateSettlementCashDragFacts(**values)


def report(*, candidates=(), cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_candidate_settlement_cash_drag_score_report(
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


def assert_no_public_payload_terms(value: Any, forbidden_terms: tuple[str, ...]) -> None:
    if isinstance(value, str):
        lowered = value.lower()
        for term in forbidden_terms:
            assert term not in lowered
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            for term in forbidden_terms:
                assert term not in lowered_key
            assert_no_public_payload_terms(item, forbidden_terms)
    if isinstance(value, list):
        for item in value:
            assert_no_public_payload_terms(item, forbidden_terms)


def test_score_calculates_support_reason_codes_and_sorting() -> None:
    result = report(
        candidates=(
            facts(
                redacted_candidate_reference="candidate_ref_cccccccccccccccc",
                proposed_paper_notional=d("100.000000"),
                days_to_expected_resolution=d("3.000000"),
                settlement_lag_days=d("1.000000"),
                dispute_revision_risk=d("0.000000"),
                portfolio_cash_lockup_pressure=d("0.050000"),
                fee_cost_buffer=d("2.000000"),
            ),
            facts(
                redacted_candidate_reference="candidate_ref_bbbbbbbbbbbbbbbb",
                proposed_paper_notional=d("1000.000000"),
                days_to_expected_resolution=d("45.000000"),
                settlement_lag_days=d("8.000000"),
                dispute_revision_risk=d("0.200000"),
                portfolio_cash_lockup_pressure=d("0.350000"),
                fee_cost_buffer=d("5.000000"),
            ),
            facts(
                redacted_candidate_reference="candidate_ref_aaaaaaaaaaaaaaaa",
                proposed_paper_notional=d("8000.000000"),
                days_to_expected_resolution=d("110.000000"),
                settlement_lag_days=d("20.000000"),
                dispute_revision_risk=d("0.950000"),
                portfolio_cash_lockup_pressure=d("0.820000"),
                fee_cost_buffer=ZERO,
            ),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "candidate-settlement-cash-drag-score-v0"
    assert result.candidate_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.max_settlement_cash_drag_score == d("0.871500")
    assert result.risk_support == "block"
    assert result.reason_codes == (
        "settlement_cash_drag_blocked",
        "settlement_cash_drag_watch",
        "settlement_cash_drag_passed",
        "paper_cash_drag_risk_high",
        "resolution_lockup_watch",
        "resolution_lockup_long",
        "settlement_lag_watch",
        "settlement_lag_long",
        "dispute_revision_risk_high",
        "portfolio_cash_lockup_pressure_present",
        "portfolio_cash_lockup_pressure_high",
        "fee_cost_buffer_shortfall_present",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    blocked, watched, passed = result.rows
    assert tuple(row.risk_support for row in result.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert blocked.redacted_candidate_reference == "candidate_ref_aaaaaaaaaaaaaaaa"
    assert blocked.redacted_market_reference == "market_ref_bbbbbbbbbbbbbbbb"
    assert blocked.settlement_cash_drag_score == d("0.871500")
    assert blocked.risk_support == "block"
    assert blocked.reason_codes == (
        "settlement_cash_drag_blocked",
        "paper_cash_drag_risk_high",
        "resolution_lockup_long",
        "settlement_lag_long",
        "dispute_revision_risk_high",
        "portfolio_cash_lockup_pressure_high",
        "fee_cost_buffer_shortfall_present",
    )

    assert watched.settlement_cash_drag_score == d("0.300000")
    assert watched.risk_support == "watch"
    assert watched.reason_codes == (
        "settlement_cash_drag_watch",
        "resolution_lockup_watch",
        "settlement_lag_watch",
        "portfolio_cash_lockup_pressure_present",
        "fee_cost_buffer_shortfall_present",
    )

    assert passed.settlement_cash_drag_score == d("0.023167")
    assert passed.risk_support == "pass"
    assert passed.reason_codes == ("settlement_cash_drag_passed",)


def test_empty_report_is_watch_zeroed_decimal_and_readonly() -> None:
    empty = report()

    assert empty.candidate_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.blocked_count == d("0")
    assert empty.max_settlement_cash_drag_score == ZERO
    assert empty.risk_support == "watch"
    assert empty.reason_codes == ("settlement_cash_drag_score_empty",)
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    populated = report(candidates=(facts(),))
    for value in (empty, *populated.rows, populated):
        for item in fields(value):
            if item.name in {
                "paper_only",
                "report_only",
                "readonly",
                "reason_codes",
                "rows",
                "generated_at",
                "config_version",
                "redacted_candidate_reference",
                "redacted_market_reference",
                "risk_support",
            }:
                continue
            assert type(getattr(value, item.name)) is Decimal


def test_payload_uses_only_public_refs_decimal_strings_and_support_fields() -> None:
    module = api()
    result = report(
        candidates=(
            facts(
                redacted_candidate_reference="candidate_ref_0123456789abcdef",
                redacted_market_reference="market_ref_fedcba9876543210",
                proposed_paper_notional=d("8000.000000"),
                days_to_expected_resolution=d("110.000000"),
                settlement_lag_days=d("20.000000"),
                dispute_revision_risk=d("0.950000"),
                portfolio_cash_lockup_pressure=d("0.820000"),
                fee_cost_buffer=ZERO,
            ),
        ),
        generated_at=datetime(2026, 7, 7, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.candidate_settlement_cash_drag_score_payload(result)
    rendered = repr(payload).lower()
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["max_settlement_cash_drag_score"] == "0.871500"
    assert payload["risk_support"] == "block"
    assert payload["rows"][0] == {
        "redacted_candidate_reference": "candidate_ref_0123456789abcdef",
        "redacted_market_reference": "market_ref_fedcba9876543210",
        "settlement_cash_drag_score": "0.871500",
        "risk_support": "block",
        "reason_codes": [
            "settlement_cash_drag_blocked",
            "paper_cash_drag_risk_high",
            "resolution_lockup_long",
            "settlement_lag_long",
            "dispute_revision_risk_high",
            "portfolio_cash_lockup_pressure_high",
            "fee_cost_buffer_shortfall_present",
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "secret" not in rendered
    assert "token" not in rendered
    assert_no_float_or_decimal_payload_values(payload)
    assert_no_public_payload_terms(
        payload,
        (
            "account",
            "wallet",
            "auth",
            "recommendation",
            "order",
            "sizing",
            "notional",
            "trade",
            "trading",
        ),
    )
    json.dumps(payload, sort_keys=True)


def test_validation_rejects_bad_types_raw_refs_bad_thresholds_duplicates_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_candidate_settlement_cash_drag_score_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        module.CandidateSettlementCashDragScoreReport(
            generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
            config_version="candidate-settlement-cash-drag-score-v0",
            candidate_count=ZERO,
            pass_count=ZERO,
            watch_count=ZERO,
            blocked_count=ZERO,
            max_settlement_cash_drag_score=ZERO,
            risk_support="watch",
            reason_codes=("settlement_cash_drag_score_empty",),
            rows=(),
        )
    with pytest.raises(ValueError, match="candidates"):
        report(candidates=(object(),))
    with pytest.raises(ValueError, match="proposed_paper_notional"):
        facts(proposed_paper_notional=100.0)
    with pytest.raises(ValueError, match="fee_cost_buffer"):
        facts(fee_cost_buffer=_DecimalSubclass("2.000000"))
    with pytest.raises(ValueError, match="days_to_expected_resolution"):
        facts(days_to_expected_resolution=Decimal("Infinity"))
    with pytest.raises(ValueError, match="proposed_paper_notional must be positive"):
        facts(proposed_paper_notional=ZERO)
    with pytest.raises(ValueError, match="settlement_lag_days must be nonnegative"):
        facts(settlement_lag_days=d("-0.000001"))
    with pytest.raises(ValueError, match="dispute_revision_risk"):
        facts(dispute_revision_risk=d("1.000001"))
    with pytest.raises(ValueError, match="redacted_candidate_reference"):
        facts(redacted_candidate_reference="candidate_ref_secret_token")
    with pytest.raises(ValueError, match="redacted_market_reference"):
        facts(redacted_market_reference=" market_ref_bbbbbbbbbbbbbbbb")
    with pytest.raises(ValueError, match="watch_score_threshold"):
        config(watch_score_threshold=d("0.900000"), blocked_score_threshold=d("0.700000"))
    with pytest.raises(ValueError, match="minimum_fee_cost_buffer_ratio"):
        config(minimum_fee_cost_buffer_ratio=d("1.000001"))
    with pytest.raises(ValueError, match="duplicate redacted_candidate_reference"):
        report(candidates=(facts(), facts()))
    with pytest.raises(ValueError, match="report_only"):
        replace(config(), report_only=False)
    tampered_config = config()
    object.__setattr__(tampered_config, "readonly", False)
    with pytest.raises(ValueError, match="config readonly must be True"):
        report(cfg=tampered_config)
    tampered_facts = facts()
    object.__setattr__(tampered_facts, "paper_only", False)
    with pytest.raises(ValueError, match="facts paper_only must be True"):
        report(candidates=(tampered_facts,))
    with pytest.raises(ValueError, match="candidates"):
        report(candidates=object())

    frozen = facts()
    with pytest.raises(FrozenInstanceError):
        frozen.redacted_candidate_reference = "candidate_ref_0123456789abcdef"  # type: ignore[misc]


def test_report_rejects_misordered_rows_and_mismatched_aggregates() -> None:
    result = report(
        candidates=(
            facts(
                redacted_candidate_reference="candidate_ref_aaaaaaaaaaaaaaaa",
                proposed_paper_notional=d("8000.000000"),
                days_to_expected_resolution=d("110.000000"),
                settlement_lag_days=d("20.000000"),
                dispute_revision_risk=d("0.950000"),
                portfolio_cash_lockup_pressure=d("0.820000"),
                fee_cost_buffer=ZERO,
            ),
            facts(
                redacted_candidate_reference="candidate_ref_bbbbbbbbbbbbbbbb",
                proposed_paper_notional=d("1000.000000"),
                days_to_expected_resolution=d("45.000000"),
                settlement_lag_days=d("8.000000"),
                portfolio_cash_lockup_pressure=d("0.350000"),
                fee_cost_buffer=d("5.000000"),
            ),
        ),
    )

    with pytest.raises(ValueError, match="deterministically sorted"):
        replace(result, rows=tuple(reversed(result.rows)))
    with pytest.raises(ValueError, match="candidate_count"):
        replace(result, candidate_count=d("99"))
    with pytest.raises(ValueError, match="pass_count"):
        replace(result, pass_count=d("99"))
    with pytest.raises(ValueError, match="watch_count"):
        replace(result, watch_count=d("99"))
    with pytest.raises(ValueError, match="blocked_count"):
        replace(result, blocked_count=d("99"))
    with pytest.raises(ValueError, match="max_settlement_cash_drag_score"):
        replace(result, max_settlement_cash_drag_score=d("0.111111"))
    with pytest.raises(ValueError, match="risk_support"):
        replace(result, risk_support="pass")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(result, reason_codes=("settlement_cash_drag_passed",))


def test_row_rejects_conflicting_support_reasons_and_empty_reason() -> None:
    module = api()

    with pytest.raises(ValueError, match="conflicting risk_support"):
        module.CandidateSettlementCashDragScoreRow(
            redacted_candidate_reference="candidate_ref_aaaaaaaaaaaaaaaa",
            redacted_market_reference="market_ref_bbbbbbbbbbbbbbbb",
            settlement_cash_drag_score=d("0.100000"),
            risk_support="pass",
            reason_codes=(
                "settlement_cash_drag_passed",
                "settlement_cash_drag_watch",
            ),
        )
    with pytest.raises(ValueError, match="empty report reason"):
        module.CandidateSettlementCashDragScoreRow(
            redacted_candidate_reference="candidate_ref_aaaaaaaaaaaaaaaa",
            redacted_market_reference="market_ref_bbbbbbbbbbbbbbbb",
            settlement_cash_drag_score=d("0.100000"),
            risk_support="pass",
            reason_codes=(
                "settlement_cash_drag_passed",
                "settlement_cash_drag_score_empty",
            ),
        )


def test_payload_requires_report_type_and_hard_flags() -> None:
    module = api()
    result = report(candidates=(facts(),))

    with pytest.raises(ValueError, match="report must be"):
        module.candidate_settlement_cash_drag_score_payload(object())

    with pytest.raises(ValueError, match="report_only must be True"):
        module.candidate_settlement_cash_drag_score_payload(
            replace(result, report_only=False),
        )


def test_config_version_is_fixed_public_token_and_rechecked_for_payload() -> None:
    module = api()

    for bad_version in (
        "candidate-settlement-cash-drag-score-v1",
        "candidate-settlement-cash-drag-score-v0-wallet",
        " candidate-settlement-cash-drag-score-v0",
    ):
        with pytest.raises(ValueError, match="config_version"):
            config(config_version=bad_version)

    result = report(candidates=(facts(),))
    object.__setattr__(
        result,
        "config_version",
        "candidate-settlement-cash-drag-score-v0-order",
    )
    with pytest.raises(ValueError, match="config_version"):
        module.candidate_settlement_cash_drag_score_payload(result)


def test_payload_revalidates_tampered_report_and_rows_before_rendering() -> None:
    module = api()
    result = report(candidates=(facts(),))

    object.__setattr__(result, "candidate_count", 1.0)
    with pytest.raises(ValueError, match="candidate_count"):
        module.candidate_settlement_cash_drag_score_payload(result)

    result = report(candidates=(facts(),))
    row = result.rows[0]
    object.__setattr__(row, "reason_codes", ("settlement_cash_drag_passed", "secret_token"))
    with pytest.raises(ValueError, match="reason_code"):
        module.candidate_settlement_cash_drag_score_payload(result)

    result = report(candidates=(facts(),))
    row = result.rows[0]
    object.__setattr__(row, "readonly", False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        module.candidate_settlement_cash_drag_score_payload(result)


def test_module_has_no_external_io_or_unsafe_surface_terms() -> None:
    source_path = Path(
        "src/polymarket_alpha_lab/candidate_settlement_cash_drag_score.py",
    )
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "httpx",
        "requests",
        "socket",
        "urllib",
        "aiohttp",
        "websocket",
        "sqlite3",
        "duckdb",
        "psycopg",
        "sqlalchemy",
        "pymongo",
        "redis",
        "pathlib",
        "os",
        "subprocess",
    }
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert imports.isdisjoint(forbidden_import_roots)

    forbidden_calls = {"open", "connect", "execute", "urlopen", "getenv", "putenv"}
    call_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert call_names.isdisjoint(forbidden_calls)

    lowered_source = source.lower()
    for forbidden in (
        "account",
        "wallet",
        "auth",
        "order",
        "sign",
        "cancel",
        "replace",
        "recommendation",
        "sizing",
        "trade",
        "trading",
        "position",
        "execution",
        "live",
        "network",
        "database",
        "db",
        "env",
        "file",
        "persist",
    ):
        assert forbidden not in lowered_source
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
