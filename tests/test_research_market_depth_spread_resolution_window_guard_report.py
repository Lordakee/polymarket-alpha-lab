from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_market_depth_spread_resolution_window_guard_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_DEPTH_SPREAD_RESOLUTION_WINDOW_GUARD_REPORT_CONFIG_VERSION
        ),
        "minimum_pass_available_depth": d("1000.000000"),
        "minimum_watch_available_depth": d("250.000000"),
        "maximum_pass_spread_width_ratio": d("0.030000"),
        "maximum_watch_spread_width_ratio": d("0.080000"),
        "minimum_pass_resolution_window_hours": d("48.000000"),
        "minimum_watch_resolution_window_hours": d("12.000000"),
        "minimum_pass_guard_score": d("0.750000"),
        "minimum_watch_guard_score": d("0.450000"),
        "available_depth_weight": d("0.350000"),
        "spread_width_weight": d("0.350000"),
        "resolution_window_weight": d("0.300000"),
    }
    values.update(overrides)
    return module.ResearchMarketDepthSpreadResolutionWindowGuardConfig(**values)


def guard_input(
    private_signal_ref: str = "private-pass",
    *,
    observed_at: datetime | None = None,
    available_depth: Decimal = d("1500.000000"),
    spread_width_ratio: Decimal = d("0.010000"),
    resolution_window_hours: Decimal = d("72.000000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketDepthSpreadResolutionWindowGuardInput(
        private_signal_ref=private_signal_ref,
        observed_at=(
            observed_at
            if observed_at is not None
            else GENERATED_AT - timedelta(minutes=5)
        ),
        available_depth=available_depth,
        spread_width_ratio=spread_width_ratio,
        resolution_window_hours=resolution_window_hours,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_depth_spread_resolution_window_guard_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_report_blocks_and_exports_report_only_contract() -> None:
    module = api()
    built = report()

    assert module.MARKET_DEPTH_SPREAD_RESOLUTION_WINDOW_GUARD_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert module.__all__ == (
        "MARKET_DEPTH_SPREAD_RESOLUTION_WINDOW_GUARD_STATUSES",
        "DEFAULT_RESEARCH_MARKET_DEPTH_SPREAD_RESOLUTION_WINDOW_GUARD_REPORT_CONFIG_VERSION",
        "ResearchMarketDepthSpreadResolutionWindowGuardConfig",
        "ResearchMarketDepthSpreadResolutionWindowGuardInput",
        "ResearchMarketDepthSpreadResolutionWindowGuardReasonCodeCount",
        "ResearchMarketDepthSpreadResolutionWindowGuardReport",
        "ResearchMarketDepthSpreadResolutionWindowGuardRow",
        "build_research_market_depth_spread_resolution_window_guard_report",
        "research_market_depth_spread_resolution_window_guard_report_digest",
        "research_market_depth_spread_resolution_window_guard_report_payload",
    )
    assert type(built) is module.ResearchMarketDepthSpreadResolutionWindowGuardReport
    assert is_dataclass(built)
    assert built.__dataclass_params__.frozen
    assert built.generated_at == GENERATED_AT
    assert built.config_version == (
        "research-market-depth-spread-resolution-window-guard-report-v0"
    )
    assert built.input_count == ZERO
    assert built.row_count == ZERO
    assert built.pass_count == ZERO
    assert built.watch_count == ZERO
    assert built.block_count == ZERO
    assert built.thin_depth_count == ZERO
    assert built.wide_spread_count == ZERO
    assert built.narrow_resolution_window_count == ZERO
    assert built.average_guard_score is None
    assert built.min_available_depth == ZERO
    assert built.max_spread_width_ratio == ZERO
    assert built.min_resolution_window_hours == ZERO
    assert built.status == "block"
    assert built.rows == ()
    assert built.reason_codes == ("guard_no_inputs",)
    assert built.reason_code_counts == (
        module.ResearchMarketDepthSpreadResolutionWindowGuardReasonCodeCount(
            reason_code="guard_no_inputs",
            count=ONE,
            row_ratio=ZERO,
        ),
    )
    assert len(built.derived_validation_digest) == 64
    int(built.derived_validation_digest, 16)
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True


def test_scores_depth_spread_and_resolution_window_guard_rows() -> None:
    built = report(
        guard_input(
            "z-block",
            available_depth=d("100.000000"),
            spread_width_ratio=d("0.100000"),
            resolution_window_hours=d("4.000000"),
            reason_codes=("manual_review",),
        ),
        guard_input(
            "m-watch",
            available_depth=d("625.000000"),
            spread_width_ratio=d("0.050000"),
            resolution_window_hours=d("24.000000"),
        ),
        guard_input("a-pass"),
    )

    assert built.input_count == d("3.000000")
    assert built.row_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.thin_depth_count == d("2.000000")
    assert built.wide_spread_count == d("2.000000")
    assert built.narrow_resolution_window_count == d("2.000000")
    assert built.average_guard_score == d("0.505417")
    assert built.min_available_depth == d("100.000000")
    assert built.max_spread_width_ratio == d("0.100000")
    assert built.min_resolution_window_hours == d("4.000000")
    assert built.status == "block"
    assert built.reason_codes == (
        "guard_block",
        "guard_available_depth_block",
        "guard_spread_width_block",
        "guard_resolution_window_block",
        "guard_available_depth_watch",
        "guard_spread_width_watch",
        "guard_resolution_window_watch",
    )

    pass_row, watch_row, block_row = built.rows
    assert tuple(row.public_row_ref for row in built.rows) == (
        "depth_spread_window_group_001",
        "depth_spread_window_group_002",
        "depth_spread_window_group_003",
    )
    assert tuple(row.status for row in built.rows) == ("pass", "watch", "block")
    assert pass_row.guard_score == d("0.956250")
    assert pass_row.reason_codes == (
        "guard_available_depth_pass",
        "guard_resolution_window_pass",
        "guard_spread_width_pass",
        "guard_status_pass",
    )
    assert watch_row.available_depth_score == d("0.625000")
    assert watch_row.spread_width_score == d("0.375000")
    assert watch_row.resolution_window_score == d("0.500000")
    assert watch_row.guard_score == d("0.500000")
    assert block_row.available_depth_score == d("0.100000")
    assert block_row.spread_width_score == ZERO
    assert block_row.resolution_window_score == d("0.083333")
    assert block_row.guard_score == d("0.060000")
    assert block_row.reason_codes == (
        "guard_available_depth_block",
        "guard_resolution_window_block",
        "guard_spread_width_block",
        "guard_status_block",
        "input_manual_review",
    )


def test_payload_digest_is_deterministic_decimal_stringed_and_public_safe() -> None:
    module = api()
    first = report(
        guard_input("z-private", reason_codes=("zeta", "alpha")),
        guard_input("a-private"),
    )
    second = report(
        guard_input("a-private"),
        guard_input("z-private", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_market_depth_spread_resolution_window_guard_report_payload(
        first,
    )
    second_payload = module.research_market_depth_spread_resolution_window_guard_report_payload(
        second,
    )
    digest_payload = dict(first_payload)
    digest_payload.pop("derived_validation_digest")
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    public_encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert (
        module.research_market_depth_spread_resolution_window_guard_report_digest(first)
        == digest
    )
    assert first.derived_validation_digest == digest
    assert first_payload["derived_validation_digest"] == digest
    assert first_payload["rows"][0]["public_row_ref"] == "depth_spread_window_group_001"
    assert first_payload["rows"][0]["available_depth"] == "1500.000000"
    assert first_payload["rows"][0]["guard_score"] == "0.956250"
    assert "a-private" not in public_encoded
    assert "z-private" not in public_encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert not any(
        _has_forbidden_public_surface(value)
        for value in _walk_payload_keys(first_payload)
        + _walk_payload_strings(first_payload)
    )


def test_validation_rejects_bad_types_flags_unsafe_text_and_digest_tampering() -> None:
    module = api()
    populated = report(guard_input())

    for value in (
        config(),
        guard_input(),
        populated,
        *populated.rows,
        *populated.reason_code_counts,
    ):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item_value is None:
                continue
            if item.name.endswith(
                (
                    "_count",
                    "_depth",
                    "_hours",
                    "_ratio",
                    "_score",
                    "_weight",
                ),
            ):
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].guard_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="available_depth"):
        guard_input(available_depth=100)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="available_depth"):
        guard_input(available_depth=d("-0.0000001"))
    with pytest.raises(ValueError, match="spread_width_ratio"):
        guard_input(spread_width_ratio=DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="spread_width_ratio"):
        guard_input(spread_width_ratio=d("-0.0000001"))
    with pytest.raises(ValueError, match="spread_width_ratio"):
        guard_input(spread_width_ratio=d("1.0000001"))
    with pytest.raises(ValueError, match="resolution_window_hours"):
        guard_input(resolution_window_hours=-d("1.000000"))
    with pytest.raises(ValueError, match="observed_at"):
        guard_input(observed_at=datetime(2026, 7, 8, 18, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(guard_input(), generated_at=DatetimeSubclass(2026, 7, 8, 18, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        report(guard_input(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="private_signal_ref"):
        guard_input("market_id_alpha")
    with pytest.raises(ValueError, match="reason_codes"):
        guard_input(reason_codes=("source_url_seen",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(guard_input(), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(populated, readonly=False)
    with pytest.raises(ValueError, match="weights"):
        config(resolution_window_weight=d("0.200000"))
    with pytest.raises(ValueError, match="minimum_pass_available_depth"):
        config(minimum_pass_available_depth=d("100.000000"))
    with pytest.raises(ValueError, match="maximum_pass_spread_width_ratio"):
        config(maximum_pass_spread_width_ratio=d("0.090000"))
    with pytest.raises(ValueError, match="minimum_pass_resolution_window_hours"):
        config(minimum_pass_resolution_window_hours=d("6.000000"))
    with pytest.raises(ValueError, match="guard_score"):
        replace(populated.rows[0], guard_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(populated, status="watch")
    with pytest.raises(ValueError, match="input_count"):
        replace(populated, input_count=d("1.0000004"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="report"):
        module.research_market_depth_spread_resolution_window_guard_report_payload(object())


def test_owned_module_has_no_durable_live_or_private_public_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_depth_spread_resolution_window_guard_report.py"
    )
    text = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "database",
        "network",
        "wallet",
        "auth",
        "candidate_id",
        "condition_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token_id",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recommend",
        "sizing",
    )

    assert all(term not in text for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)


def _walk_payload_keys(value: object) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(key)
            keys.extend(_walk_payload_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_payload_keys(item))
    return tuple(keys)


def _walk_payload_strings(value: object) -> tuple[str, ...]:
    strings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            strings.append(str(key))
            strings.extend(_walk_payload_strings(item))
    elif isinstance(value, list):
        for item in value:
            strings.extend(_walk_payload_strings(item))
    elif isinstance(value, str):
        strings.append(value)
    return tuple(strings)


def _has_forbidden_public_surface(value: str) -> bool:
    lowered = value.lower()
    return any(
        term in lowered
        for term in (
            "candidate_id",
            "condition_id",
            "market_id",
            "market_slug",
            "question",
            "source_url",
            "source_text",
            "dsn",
            "table_name",
            "token",
            "wallet",
            "order",
            "trade",
        )
    )
