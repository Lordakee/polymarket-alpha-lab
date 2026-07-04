from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_team_edge_decay_rotation_digest.py"
)
GENERATED_AT = datetime(2026, 7, 3, 16, 30, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 3, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_team_edge_decay_rotation_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-team-edge-decay-rotation-digest-test-v0",
        "total_paper_capital": d("10000.000000"),
        "rotate_out_decay_ratio": d("0.400000"),
        "watch_decay_ratio": d("0.200000"),
        "block_drawdown_pressure": d("0.800000"),
        "min_liquidity_capacity_share": d("0.050000"),
        "min_signal_freshness": d("0.250000"),
    }
    values.update(overrides)
    return module.StrategyTeamEdgeDecayRotationDigestConfig(**values)


def team(**overrides: object):
    module = api()
    values = {
        "team_id": "macro_team",
        "team_reference": "macro-public",
        "observed_at": OBSERVED_AT,
        "peak_edge": d("0.100000"),
        "current_edge": d("0.030000"),
        "current_budget_share": d("0.200000"),
        "liquidity_capacity_share": d("0.400000"),
        "drawdown_pressure": d("0.300000"),
        "signal_freshness": d("0.800000"),
        "reason_codes": ("edge_decay_input",),
    }
    values.update(overrides)
    return module.StrategyTeamEdgeDecayRotationDigestTeam(**values)


def report(*, teams=(), cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_team_edge_decay_rotation_digest(
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


def test_reducer_flags_edge_decay_and_recommends_paper_rotation() -> None:
    digest = report(
        teams=(
            team(
                team_id="macro_team",
                team_reference="private-wallet-macro-team",
                peak_edge=d("0.100000"),
                current_edge=d("0.030000"),
                current_budget_share=d("0.200000"),
                liquidity_capacity_share=d("0.400000"),
                drawdown_pressure=d("0.300000"),
                signal_freshness=d("0.800000"),
            ),
            team(
                team_id="crypto_team",
                team_reference="crypto-public",
                peak_edge=d("0.100000"),
                current_edge=d("0.075000"),
                current_budget_share=d("0.300000"),
                liquidity_capacity_share=d("0.250000"),
                drawdown_pressure=d("0.350000"),
                signal_freshness=d("0.600000"),
            ),
            team(
                team_id="sports_team",
                team_reference="sports-public",
                peak_edge=d("0.100000"),
                current_edge=d("0.090000"),
                current_budget_share=d("0.100000"),
                liquidity_capacity_share=d("0.500000"),
                drawdown_pressure=d("0.100000"),
                signal_freshness=d("0.900000"),
            ),
        ),
    )

    assert is_dataclass(digest)
    assert digest.generated_at == GENERATED_AT
    assert digest.generated_at.tzinfo is UTC
    assert digest.config_version == "strategy-team-edge-decay-rotation-digest-test-v0"
    assert digest.team_count == d("3")
    assert digest.rotate_out_count == d("1")
    assert digest.watch_count == d("1")
    assert digest.hold_count == d("1")
    assert digest.total_recommended_paper_rotation == d("1400.000000")
    assert digest.max_edge_decay_ratio == d("0.700000")
    assert digest.average_edge_decay_ratio == d("0.350000")
    assert digest.status == "blocked"
    assert digest.reason_codes == (
        "team_edge_decay_rotate_out",
        "team_edge_decay_watch",
        "team_edge_decay_hold",
        "edge_decay_high",
        "edge_decay_moderate",
        "edge_decay_low",
    )
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True

    assert tuple(row.team_id for row in digest.rows) == (
        "macro_team",
        "crypto_team",
        "sports_team",
    )
    rotate_out, watched, held = digest.rows

    assert rotate_out.rotation_status == "rotate_out"
    assert rotate_out.rotation_direction == "decrease"
    assert rotate_out.edge_decay_ratio == d("0.700000")
    assert rotate_out.edge_retention_ratio == d("0.300000")
    assert rotate_out.recommended_paper_rotation == d("1400.000000")
    assert rotate_out.redacted_team_reference.startswith("team_ref_")
    assert "private" not in rotate_out.redacted_team_reference
    assert "wallet" not in rotate_out.redacted_team_reference
    assert rotate_out.reason_codes == (
        "edge_decay_input",
        "team_edge_decay_rotate_out",
        "edge_decay_high",
        "current_edge_positive",
        "liquidity_capacity_available",
        "drawdown_pressure_contained",
        "signal_freshness_available",
    )

    assert watched.rotation_status == "watch"
    assert watched.rotation_direction == "hold"
    assert watched.edge_decay_ratio == d("0.250000")
    assert watched.edge_retention_ratio == d("0.750000")
    assert watched.recommended_paper_rotation == ZERO
    assert watched.reason_codes == (
        "edge_decay_input",
        "team_edge_decay_watch",
        "edge_decay_moderate",
        "current_edge_positive",
        "liquidity_capacity_available",
        "drawdown_pressure_contained",
        "signal_freshness_available",
    )

    assert held.rotation_status == "hold"
    assert held.rotation_direction == "hold"
    assert held.edge_decay_ratio == d("0.100000")
    assert held.edge_retention_ratio == d("0.900000")
    assert held.recommended_paper_rotation == ZERO
    assert held.reason_codes == (
        "edge_decay_input",
        "team_edge_decay_hold",
        "edge_decay_low",
        "current_edge_positive",
        "liquidity_capacity_available",
        "drawdown_pressure_contained",
        "signal_freshness_available",
    )


def test_empty_digest_is_watch_with_decimal_fields_and_readonly_flags() -> None:
    empty = report()

    assert empty.team_count == d("0")
    assert empty.rotate_out_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.hold_count == d("0")
    assert empty.total_recommended_paper_rotation == ZERO
    assert empty.max_edge_decay_ratio == ZERO
    assert empty.average_edge_decay_ratio == ZERO
    assert empty.status == "watch"
    assert empty.reason_codes == ("strategy_team_edge_decay_rotation_digest_empty",)
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
                    "_edge",
                    "_ratio",
                    "_pressure",
                    "_freshness",
                    "_share",
                ),
            ):
                assert type(item_value) is Decimal


def test_payload_redacts_sensitive_references_and_uses_decimal_strings() -> None:
    module = api()
    digest = report(
        teams=(
            team(
                team_id="macro_team",
                team_reference="secret-token-private-wallet",
                observed_at=datetime(
                    2026,
                    7,
                    3,
                    9,
                    0,
                    tzinfo=timezone(timedelta(hours=-7)),
                ),
            ),
        ),
        generated_at=datetime(2026, 7, 3, 9, 30, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.strategy_team_edge_decay_rotation_digest_payload(digest)

    assert payload["generated_at"] == "2026-07-03T16:30:00+00:00"
    assert payload["team_count"] == "1"
    assert payload["total_recommended_paper_rotation"] == "1400.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-03T16:00:00+00:00"
    assert payload["rows"][0]["edge_decay_ratio"] == "0.700000"
    assert payload["rows"][0]["redacted_team_reference"].startswith("team_ref_")
    assert "secret" not in repr(payload)
    assert "token" not in repr(payload)
    assert "wallet" not in repr(payload)
    assert_no_float_values(payload)

    with pytest.raises(ValueError, match="unsafe live surface field"):
        module.strategy_team_edge_decay_rotation_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "signed_order_payload": "forbidden",
            },
        )


def test_public_string_values_reject_sensitive_content() -> None:
    module = api()

    with pytest.raises(ValueError, match="team_id must not contain sensitive content"):
        team(team_id="secret_team")

    with pytest.raises(
        ValueError,
        match="config_version must not contain sensitive content",
    ):
        config(config_version="token_config")

    payload = module.strategy_team_edge_decay_rotation_digest_payload(
        report(teams=(team(),)),
    )
    payload["rows"][0]["team_id"] = "secret_team"

    with pytest.raises(ValueError, match="payload string value"):
        module.strategy_team_edge_decay_rotation_digest_payload(payload)


def test_custom_reason_codes_are_sorted_deterministically() -> None:
    digest = report(
        teams=(
            team(
                reason_codes=(
                    "z_custom_reason",
                    "edge_decay_input",
                    "a_custom_reason",
                    "z_custom_reason",
                ),
            ),
        ),
    )

    assert digest.rows[0].reason_codes == (
        "edge_decay_input",
        "team_edge_decay_rotate_out",
        "edge_decay_high",
        "current_edge_positive",
        "liquidity_capacity_available",
        "drawdown_pressure_contained",
        "signal_freshness_available",
        "a_custom_reason",
        "z_custom_reason",
    )


def test_validation_rejects_bad_types_duplicates_datetimes_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_strategy_team_edge_decay_rotation_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="peak_edge must be a Decimal"):
        team(peak_edge=1)

    with pytest.raises(ValueError, match="current_edge must be finite"):
        team(current_edge=Decimal("NaN"))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(generated_at=datetime(2026, 7, 3, 16, 30))

    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        team(observed_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC))

    with pytest.raises(ValueError, match="current_budget_share must be a Decimal"):
        team(current_budget_share=_DecimalSubclass("0.200000"))

    with pytest.raises(ValueError, match="peak_edge must be positive"):
        team(peak_edge=d("0.000000"))

    with pytest.raises(ValueError, match="duplicate team_id"):
        report(
            teams=(
                team(team_id="macro_team"),
                team(team_id="macro_team"),
            ),
        )

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.StrategyTeamEdgeDecayRotationDigestConfig(paper_only=False)

    row = report(teams=(team(),)).rows[0]
    with pytest.raises(FrozenInstanceError):
        row.rotation_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(row, readonly=False)


def test_payload_requires_report_type_and_hard_flags() -> None:
    module = api()
    digest = report(teams=(team(),))

    with pytest.raises(ValueError, match="report must be"):
        module.strategy_team_edge_decay_rotation_digest_payload(object())

    with pytest.raises(ValueError, match="report_only must be True"):
        module.strategy_team_edge_decay_rotation_digest_payload(
            replace(digest, report_only=False),
        )


def test_module_scope_has_no_live_trading_persistence_network_or_sensitive_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.level == 0
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "env",
        "http",
        "network",
        "order",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "rollback",
        "send",
        "sign",
        "submit",
        "trade",
        "write",
    }

    assert imports
    assert all(
        fragment not in module_name.lower()
        for module_name in imports
        for fragment in forbidden_import_fragments
    )
    assert not (set(call_names) & forbidden_call_or_attribute_names)
    assert not (set(attribute_names) & forbidden_call_or_attribute_names)


def test_public_api_exports_digest_contract() -> None:
    module = api()

    assert module.__all__ == (
        "StrategyTeamEdgeDecayRotationDigestConfig",
        "StrategyTeamEdgeDecayRotationDigestReport",
        "StrategyTeamEdgeDecayRotationDigestRow",
        "StrategyTeamEdgeDecayRotationDigestTeam",
        "build_strategy_team_edge_decay_rotation_digest",
        "strategy_team_edge_decay_rotation_digest_payload",
    )
