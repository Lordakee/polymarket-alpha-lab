from __future__ import annotations

import ast
import importlib
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
    / "strategy_team_capital_rotation_digest.py"
)
GENERATED_AT = datetime(2026, 7, 3, 18, 30, tzinfo=timezone(timedelta(hours=2)))
OBSERVED_AT = datetime(2026, 7, 3, 15, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_team_capital_rotation_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-team-capital-rotation-digest-test-v0",
        "total_paper_capital": d("10000.000000"),
        "minimum_rotation_score": d("0.050000"),
        "watch_rotation_gap": d("0.020000"),
        "block_drawdown_pressure": d("0.800000"),
        "min_liquidity_capacity_share": d("0.050000"),
    }
    values.update(overrides)
    return module.StrategyTeamCapitalRotationDigestConfig(**values)


def team(**overrides: object):
    module = api()
    values = {
        "team_id": "macro_team",
        "team_reference": "macro-public",
        "observed_at": OBSERVED_AT,
        "current_budget_share": d("0.300000"),
        "target_budget_share": d("0.500000"),
        "expected_edge": d("0.080000"),
        "liquidity_capacity_share": d("0.600000"),
        "drawdown_pressure": d("0.100000"),
        "learning_value": d("0.700000"),
        "reason_codes": ("capital_rotation_input",),
    }
    values.update(overrides)
    return module.StrategyTeamCapitalRotationDigestTeam(**values)


def report(*, teams=(), cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_team_capital_rotation_digest(
        teams,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_reducer_recommends_paper_capital_rotation_across_specialist_teams() -> None:
    digest = report(
        teams=(
            team(
                team_id="macro_team",
                team_reference="macro-public",
                current_budget_share=d("0.300000"),
                target_budget_share=d("0.500000"),
                expected_edge=d("0.080000"),
                liquidity_capacity_share=d("0.600000"),
                drawdown_pressure=d("0.100000"),
                learning_value=d("0.700000"),
            ),
            team(
                team_id="crypto_team",
                team_reference="secret-wallet-token-team",
                current_budget_share=d("0.400000"),
                target_budget_share=d("0.300000"),
                expected_edge=d("0.040000"),
                liquidity_capacity_share=d("0.250000"),
                drawdown_pressure=d("0.350000"),
                learning_value=d("0.500000"),
            ),
            team(
                team_id="sports_team",
                team_reference="sports-public",
                current_budget_share=d("0.300000"),
                target_budget_share=d("0.200000"),
                expected_edge=d("-0.010000"),
                liquidity_capacity_share=d("0.020000"),
                drawdown_pressure=d("0.900000"),
                learning_value=d("0.100000"),
            ),
        ),
    )

    assert is_dataclass(digest)
    assert digest.generated_at == datetime(2026, 7, 3, 16, 30, tzinfo=UTC)
    assert digest.generated_at.tzinfo is UTC
    assert digest.config_version == "strategy-team-capital-rotation-digest-test-v0"
    assert digest.team_count == d("3")
    assert digest.pass_count == d("1")
    assert digest.watch_count == d("1")
    assert digest.blocked_count == d("1")
    assert digest.total_recommended_paper_rotation == d("2000.000000")
    assert digest.net_target_budget_shift == d("0.400000")
    assert digest.max_rotation_score == d("0.300000")
    assert digest.status == "blocked"
    assert digest.reason_codes == (
        "capital_rotation_block",
        "capital_rotation_pass",
        "capital_rotation_watch",
        "drawdown_pressure_high",
        "liquidity_capacity_low",
        "expected_edge_negative",
    )
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True

    assert tuple(row.team_id for row in digest.rows) == (
        "macro_team",
        "crypto_team",
        "sports_team",
    )
    passed, watched, blocked = digest.rows

    assert passed.rotation_status == "pass"
    assert passed.rotation_direction == "increase"
    assert passed.budget_gap_share == d("0.200000")
    assert passed.rotation_score == d("0.300000")
    assert passed.recommended_paper_rotation == d("2000.000000")
    assert passed.reason_codes == (
        "capital_rotation_input",
        "capital_rotation_pass",
        "budget_share_below_target",
        "expected_edge_positive",
        "liquidity_capacity_available",
        "drawdown_pressure_contained",
        "learning_value_high",
    )

    assert watched.rotation_status == "watch"
    assert watched.rotation_direction == "decrease"
    assert watched.budget_gap_share == d("-0.100000")
    assert watched.rotation_score == d("0.000000")
    assert watched.recommended_paper_rotation == ZERO
    assert watched.redacted_team_reference.startswith("team_ref_")
    assert "secret" not in watched.redacted_team_reference
    assert "wallet" not in watched.redacted_team_reference
    assert "token" not in watched.redacted_team_reference
    assert watched.reason_codes == (
        "capital_rotation_input",
        "capital_rotation_watch",
        "budget_share_above_target",
        "expected_edge_positive",
        "liquidity_capacity_available",
        "drawdown_pressure_contained",
        "learning_value_moderate",
    )

    assert blocked.rotation_status == "blocked"
    assert blocked.rotation_direction == "decrease"
    assert blocked.budget_gap_share == d("-0.100000")
    assert blocked.rotation_score == ZERO
    assert blocked.recommended_paper_rotation == ZERO
    assert blocked.reason_codes == (
        "capital_rotation_input",
        "capital_rotation_block",
        "budget_share_above_target",
        "expected_edge_negative",
        "liquidity_capacity_low",
        "drawdown_pressure_high",
        "learning_value_low",
    )


def test_empty_digest_is_watch_with_decimal_fields_and_readonly_guards() -> None:
    empty = report()

    assert empty.team_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.blocked_count == d("0")
    assert empty.total_recommended_paper_rotation == ZERO
    assert empty.net_target_budget_shift == ZERO
    assert empty.max_rotation_score == ZERO
    assert empty.status == "watch"
    assert empty.reason_codes == ("strategy_team_capital_rotation_digest_empty",)
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    populated = report(teams=(team(),))
    for value in (empty, populated, *populated.rows):
        for item in fields(value):
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(
                (
                    "_count",
                    "_capital",
                    "_rotation",
                    "_score",
                    "_edge",
                    "_pressure",
                    "_value",
                    "_share",
                    "_shift",
                    "_gap_share",
                ),
            ):
                assert type(item_value) is Decimal


def test_payload_redacts_sensitive_references_and_uses_decimal_strings() -> None:
    module = api()
    digest = report(
        teams=(
            team(
                team_id="crypto_team",
                team_reference="private-key-wallet-secret",
            ),
        ),
    )

    payload = module.strategy_team_capital_rotation_digest_payload(digest)

    assert payload["generated_at"] == "2026-07-03T16:30:00+00:00"
    assert payload["total_paper_capital"] == "10000.000000"
    assert payload["total_recommended_paper_rotation"] == "2000.000000"
    assert payload["rows"][0]["redacted_team_reference"].startswith("team_ref_")
    assert "private" not in repr(payload)
    assert "wallet" not in repr(payload)
    assert "secret" not in repr(payload)
    assert_no_float_values(payload)

    with pytest.raises(ValueError, match="unsafe live surface field"):
        module.strategy_team_capital_rotation_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "order_submission": "forbidden",
            },
        )

    with pytest.raises(ValueError, match="sensitive string value"):
        module.strategy_team_capital_rotation_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "rows": [{"team_id": "wallet_secret_team"}],
            },
        )
    with pytest.raises(ValueError, match="sensitive string value"):
        module.strategy_team_capital_rotation_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "rows": [{"bearer_token": "redacted"}],
            },
        )
    with pytest.raises(ValueError, match="readonly must be True"):
        module.strategy_team_capital_rotation_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "rows": [
                    {
                        "paper_only": True,
                        "report_only": True,
                        "readonly": False,
                    },
                ],
            },
        )


def test_direct_report_validation_rejects_contradictory_or_unsorted_rows() -> None:
    module = api()
    digest = report(
        teams=(
            team(team_id="macro_team", team_reference="macro-public"),
            team(
                team_id="crypto_team",
                team_reference="crypto-public",
                current_budget_share=d("0.400000"),
                target_budget_share=d("0.300000"),
                expected_edge=d("0.040000"),
                liquidity_capacity_share=d("0.250000"),
                drawdown_pressure=d("0.350000"),
                learning_value=d("0.500000"),
            ),
        ),
    )

    with pytest.raises(ValueError, match="status must match rows"):
        replace(digest, status="watch")
    with pytest.raises(ValueError, match="reason_codes must match rows"):
        replace(digest, reason_codes=("capital_rotation_watch",))
    with pytest.raises(ValueError, match="rows must use stable sequence"):
        module.StrategyTeamCapitalRotationDigestReport(
            generated_at=digest.generated_at,
            config_version=digest.config_version,
            total_paper_capital=digest.total_paper_capital,
            team_count=digest.team_count,
            pass_count=digest.pass_count,
            watch_count=digest.watch_count,
            blocked_count=digest.blocked_count,
            total_recommended_paper_rotation=digest.total_recommended_paper_rotation,
            net_target_budget_shift=digest.net_target_budget_shift,
            max_rotation_score=digest.max_rotation_score,
            status=digest.status,
            reason_codes=digest.reason_codes,
            rows=tuple(reversed(digest.rows)),
        )


def test_validates_phase_one_contract_and_inputs() -> None:
    module = api()

    with pytest.raises(FrozenInstanceError):
        replace(team()).team_id = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        team(report_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        report(cfg=config(readonly=False))

    with pytest.raises(ValueError, match="current_budget_share must be a Decimal"):
        team(current_budget_share=_DecimalSubclass("0.300000"))

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(generated_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(generated_at=datetime(2026, 7, 3, 16, 30))

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        team(observed_at=datetime(2026, 7, 3, 15, 45, tzinfo=_NoOffsetTimezone()))

    with pytest.raises(ValueError, match="current_budget_share must be between 0 and 1"):
        team(current_budget_share=d("1.100000"))

    with pytest.raises(ValueError, match="reason_codes must not contain sensitive content"):
        team(reason_codes=("contains_secret_token",))

    with pytest.raises(ValueError, match="config_version must not contain sensitive content"):
        config(config_version="secret_wallet_config")

    with pytest.raises(ValueError, match="team_id must not contain sensitive content"):
        team(team_id="wallet_secret_team")

    hockey = team(team_id="hockey_team", reason_codes=("hockey_signal",))
    assert hockey.team_id == "hockey_team"
    assert hockey.reason_codes == ("hockey_signal",)

    with pytest.raises(ValueError, match="teams must be an iterable"):
        report(teams="macro_team")

    with pytest.raises(ValueError, match="team must be a StrategyTeamCapitalRotationDigestTeam"):
        report(teams=(object(),))

    parsed = ast.parse(MODULE_PATH.read_text())
    banned_fragments = ("requests", "psycopg", "sqlite", "open(", "Order", "Trade")
    source = MODULE_PATH.read_text()
    for fragment in banned_fragments:
        assert fragment not in source
    imported_modules = {
        alias.name
        for node in parsed.body
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_modules.update(
        node.module
        for node in parsed.body
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    assert "requests" not in imported_modules
    assert "psycopg" not in imported_modules
