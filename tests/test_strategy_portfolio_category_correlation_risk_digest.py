from __future__ import annotations

import ast
import importlib
import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_portfolio_category_correlation_risk_digest"
GENERATED_AT = datetime(2026, 7, 4, 16, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 4, 15, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_PORTFOLIO_CATEGORY_CORRELATION_RISK_DIGEST_CONFIG_VERSION
        ),
        "category_watch_share": d("0.300000"),
        "category_block_share": d("0.600000"),
        "shared_catalyst_watch_share": d("0.300000"),
        "shared_catalyst_block_share": d("0.550000"),
        "category_rotation_watch_count": d("2"),
        "category_rotation_block_count": d("3"),
        "correlation_risk_watch_score": d("0.450000"),
        "correlation_risk_block_score": d("0.650000"),
    }
    values.update(overrides)
    return module.StrategyPortfolioCategoryCorrelationRiskDigestConfig(**values)


def exposure(
    position_id: str = "pos-macro-a",
    *,
    market_slug: str | None = None,
    category: str = "macro",
    catalyst_id: str = "rates-cpi",
    observed_at: datetime = OBSERVED_AT,
    notional: Decimal = d("100.000000"),
    category_rotation_count: Decimal = d("1"),
    correlation_score: Decimal = d("0.200000"),
    public_reference: str = "plain-ticket",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.StrategyPortfolioCategoryCorrelationRiskInput(
        position_id=position_id,
        market_slug=market_slug or position_id,
        category=category,
        catalyst_id=catalyst_id,
        observed_at=observed_at,
        notional=notional,
        category_rotation_count=category_rotation_count,
        correlation_score=correlation_score,
        public_reference=public_reference,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(*rows: Any, cfg: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_strategy_portfolio_category_correlation_risk_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_public_numeric_fields_are_decimal(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if type(value) is bool:
            continue
        assert type(value) is not float
        assert type(value) is not int
        if isinstance(value, tuple):
            for item in value:
                if is_dataclass(item):
                    assert_public_numeric_fields_are_decimal(item)


def assert_no_float_values(value: object) -> None:
    assert type(value) is not float
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_digest_aggregates_category_exposure_shared_catalysts_and_correlation_risk() -> None:
    result = digest(
        exposure(
            "pos-crypto-a",
            category="crypto",
            catalyst_id="election-night",
            notional=d("400.000000"),
            category_rotation_count=d("3"),
            correlation_score=d("0.700000"),
            public_reference="wallet://private-key",
        ),
        exposure(
            "pos-crypto-b",
            category="crypto",
            catalyst_id="election-night",
            notional=d("250.000000"),
            category_rotation_count=d("2"),
            correlation_score=d("0.650000"),
            public_reference="https://example.test/feed?token=secret",
        ),
        exposure(
            "pos-macro-a",
            category="macro",
            catalyst_id="rates-cpi",
            notional=d("300.000000"),
            category_rotation_count=d("2"),
            correlation_score=d("0.400000"),
        ),
        exposure(
            "pos-sports-a",
            category="sports",
            catalyst_id="finals",
            notional=d("50.000000"),
            category_rotation_count=d("1"),
            correlation_score=d("0.150000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.generated_at.tzinfo is UTC
    assert result.config_version == "strategy-portfolio-category-correlation-risk-digest-v0"
    assert result.position_count == d("4")
    assert result.category_count == d("3")
    assert result.catalyst_count == d("3")
    assert result.total_notional == d("1000.000000")
    assert result.max_category_exposure_share == d("0.650000")
    assert result.max_shared_catalyst_exposure_share == d("0.650000")
    assert result.max_category_rotation_count == d("3")
    assert result.max_correlation_score == d("0.700000")
    assert result.blocked_position_count == d("2")
    assert result.watch_position_count == d("1")
    assert result.pass_position_count == d("1")
    assert result.digest_status == "blocked"
    assert result.reason_codes == (
        "category_exposure_blocked",
        "category_exposure_watch",
        "category_rotation_blocked",
        "category_rotation_watch",
        "correlation_risk_blocked",
        "shared_catalyst_exposure_blocked",
        "shared_catalyst_exposure_watch",
    )
    assert_public_numeric_fields_are_decimal(result)

    assert tuple(row.position_id for row in result.rows) == (
        "pos-crypto-a",
        "pos-crypto-b",
        "pos-macro-a",
        "pos-sports-a",
    )
    blocked = result.rows[0]
    assert blocked.rank == d("1")
    assert blocked.category_exposure_notional == d("650.000000")
    assert blocked.category_exposure_share == d("0.650000")
    assert blocked.shared_catalyst_exposure_notional == d("650.000000")
    assert blocked.shared_catalyst_exposure_share == d("0.650000")
    assert blocked.risk_score == d("0.700000")
    assert blocked.risk_status == "blocked"
    assert blocked.redacted_public_reference == "<redacted>"
    assert blocked.reason_codes == (
        "category_exposure_blocked",
        "category_rotation_blocked",
        "correlation_risk_blocked",
        "shared_catalyst_exposure_blocked",
    )

    watch = result.rows[2]
    assert watch.rank == d("3")
    assert watch.position_id == "pos-macro-a"
    assert watch.risk_score == d("0.400000")
    assert watch.risk_status == "watch"
    assert watch.reason_codes == (
        "category_exposure_watch",
        "category_rotation_watch",
        "shared_catalyst_exposure_watch",
    )


def test_empty_digest_is_report_only_readonly_and_decimal_zeroed() -> None:
    result = digest()

    assert result.position_count == d("0")
    assert result.category_count == d("0")
    assert result.catalyst_count == d("0")
    assert result.total_notional == ZERO
    assert result.max_category_exposure_share == ZERO
    assert result.max_shared_catalyst_exposure_share == ZERO
    assert result.max_category_rotation_count == d("0")
    assert result.max_correlation_score == ZERO
    assert result.blocked_position_count == d("0")
    assert result.watch_position_count == d("0")
    assert result.pass_position_count == d("0")
    assert result.digest_status == "blocked"
    assert result.reason_codes == (
        "strategy_portfolio_category_correlation_risk_digest_empty",
    )
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_public_numeric_fields_are_decimal(result)


def test_payload_is_json_ready_decimal_stringed_and_redacted() -> None:
    module = api()
    result = digest(
        exposure(public_reference="https://example.test/private?api_key=secret"),
        generated_at=datetime(2026, 7, 4, 12, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = module.strategy_portfolio_category_correlation_risk_digest_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["generated_at"] == "2026-07-04T16:00:00+00:00"
    assert payload["position_count"] == "1"
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["risk_score"] == "1.000000"
    assert payload["rows"][0]["redacted_public_reference"] == "<redacted>"
    assert "api_key=secret" not in encoded
    assert "public_reference" not in payload["rows"][0]
    assert not re.search(r":\s*-?\d+\.\d+", encoded)
    assert_no_float_values(payload)


def test_payload_dict_path_enforces_phase1_boundaries() -> None:
    module = api()
    payload = module.strategy_portfolio_category_correlation_risk_digest_payload(
        digest(exposure(public_reference="plain-ticket")),
    )

    assert module.strategy_portfolio_category_correlation_risk_digest_payload(payload) == payload

    with pytest.raises(ValueError, match="readonly"):
        module.strategy_portfolio_category_correlation_risk_digest_payload(
            {**payload, "readonly": False},
        )

    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_portfolio_category_correlation_risk_digest_payload(
            {**payload, "wallet": {"address": "0x0"}},
        )

    with pytest.raises(ValueError, match="unsafe|sensitive"):
        module.strategy_portfolio_category_correlation_risk_digest_payload(
            {**payload, "public_reference": "https://example.test/feed?token=secret"},
        )

    with pytest.raises(ValueError, match="Decimal"):
        module.strategy_portfolio_category_correlation_risk_digest_payload(
            {**payload, "position_count": 1},
        )

    with pytest.raises(ValueError, match="float"):
        module.strategy_portfolio_category_correlation_risk_digest_payload(
            {**payload, "max_correlation_score": 0.58},
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        module.strategy_portfolio_category_correlation_risk_digest_payload(
            {**payload, "generated_at": datetime(2026, 7, 4, 16, 0)},
        )

    with pytest.raises(ValueError, match="JSON object keys"):
        module.strategy_portfolio_category_correlation_risk_digest_payload({1: "x", **payload})


def test_inputs_config_and_times_reject_non_decimal_subclasses_and_unsafe_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="notional must be a Decimal"):
        exposure(notional=100)
    with pytest.raises(ValueError, match="notional must be exactly Decimal"):
        exposure(notional=_DecimalSubclass("100.000000"))
    with pytest.raises(ValueError, match="category must be a nonblank trimmed string"):
        exposure(category=_StringSubclass("macro"))
    with pytest.raises(ValueError, match="correlation_score must be between zero and one"):
        exposure(correlation_score=d("1.100000"))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        exposure(observed_at=datetime(2026, 7, 4, 15, 30))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        exposure(
            observed_at=datetime(
                2026,
                7,
                4,
                15,
                30,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        exposure(paper_only=False)
    with pytest.raises(ValueError, match="category_watch_share must be a Decimal"):
        config(category_watch_share=1)
    with pytest.raises(ValueError, match="config must be"):
        module.build_strategy_portfolio_category_correlation_risk_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_report_dataclasses_are_frozen_and_datetimes_normalize_to_utc() -> None:
    result = digest(
        exposure(
            observed_at=datetime(2026, 7, 4, 11, 30, tzinfo=timezone(timedelta(hours=-4))),
        ),
        generated_at=datetime(2026, 7, 4, 12, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert result.generated_at == GENERATED_AT
    assert result.generated_at.tzinfo is UTC
    assert result.rows[0].observed_at == OBSERVED_AT
    assert result.rows[0].observed_at.tzinfo is UTC
    assert result.rows[0].paper_only is True
    assert result.rows[0].report_only is True
    assert result.rows[0].readonly is True

    with pytest.raises(FrozenInstanceError):
        result.rows[0].rank = d("99")

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        digest(exposure(), generated_at=_DatetimeSubclass(2026, 7, 4, tzinfo=UTC))

    with pytest.raises(ValueError, match="digest report must contain exact rows"):
        replace(result, rows=(object(),))

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        digest(exposure(observed_at=GENERATED_AT + timedelta(seconds=1)))


def test_reason_codes_are_deterministic_unique_and_rows_have_stable_tie_breakers() -> None:
    result = digest(
        exposure(
            "pos-b",
            market_slug="same-b",
            category="crypto",
            catalyst_id="same-catalyst",
            notional=d("100.000000"),
            category_rotation_count=d("3"),
            correlation_score=d("0.700000"),
        ),
        exposure(
            "pos-a",
            market_slug="same-a",
            category="crypto",
            catalyst_id="same-catalyst",
            notional=d("100.000000"),
            category_rotation_count=d("3"),
            correlation_score=d("0.700000"),
        ),
    )

    assert tuple(row.position_id for row in result.rows) == ("pos-a", "pos-b")
    for row in result.rows:
        assert row.reason_codes == tuple(sorted(set(row.reason_codes)))
    assert result.reason_codes == tuple(sorted(set(result.reason_codes)))


def test_module_is_pure_report_only_and_contains_no_io_or_trading_behavior() -> None:
    path = Path(
        "src/polymarket_alpha_lab/strategy_portfolio_category_correlation_risk_digest.py",
    )
    tree = ast.parse(path.read_text())

    banned_imports = {
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "psycopg",
    }
    banned_names = {
        "open",
        "connect",
        "cancel",
        "replace",
        "wallet",
        "order",
        "create_order",
        "place_order",
        "submit_order",
        "trade",
        "auth",
        "login",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_names
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_names


def test_static_forbidden_surface_terms_are_absent_from_digest_source() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_portfolio_category_correlation_risk_digest.py",
    ).read_text(encoding="utf-8").lower()

    forbidden_terms = (
        "live trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "signing",
        "trade",
        "execute",
        "database",
        "supabase",
    )

    assert [term for term in forbidden_terms if term in source] == []
