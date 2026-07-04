from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
BASELINE_X_DATE = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
LATEST_X_DATE = datetime(2026, 7, 13, 12, 0, tzinfo=UTC)
LAST_SIGNAL_AT = datetime(2026, 7, 4, 11, 30, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_policy_debt_ceiling_x_date_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "debt-ceiling-x-date-digest-test-v0",
        "watch_days_to_x_date": d("14.000000"),
        "blocked_days_to_x_date": d("7.000000"),
        "watch_slippage_days": d("3.000000"),
        "blocked_slippage_days": d("7.000000"),
        "watch_negotiation_stress_ratio": d("0.400000"),
        "blocked_negotiation_stress_ratio": d("0.700000"),
        "max_signal_age_hours": d("48.000000"),
    }
    values.update(overrides)
    return module.MarketResearchPolicyDebtCeilingXDateDigestConfig(**values)


def signal(
    signal_id: str,
    *,
    market_slug: str = "will-us-debt-ceiling-x-date-be-before-2026-07-15",
    source_label: str = "treasury-cash-balance",
    baseline_x_date: datetime = BASELINE_X_DATE,
    latest_x_date: datetime = LATEST_X_DATE,
    observed_at: datetime = LAST_SIGNAL_AT,
    negotiation_stress_ratio: Decimal = d("0.500000"),
    probability_event_relevance: Decimal = d("0.800000"),
    upstream_reason_codes: tuple[str, ...] = ("treasury_cash_balance_update",),
) -> Any:
    module = api()
    return module.DebtCeilingXDateSignal(
        signal_id=signal_id,
        market_slug=market_slug,
        source_label=source_label,
        baseline_x_date=baseline_x_date,
        latest_x_date=latest_x_date,
        observed_at=observed_at,
        negotiation_stress_ratio=negotiation_stress_ratio,
        probability_event_relevance=probability_event_relevance,
        upstream_reason_codes=upstream_reason_codes,
    )


def build_report(*signals: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_market_research_policy_debt_ceiling_x_date_digest(
        signals,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    report = build_report()

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "debt-ceiling-x-date-digest-test-v0"
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_policy_debt_ceiling_x_date_digest"
    )
    assert report.input_count == d("0.000000")
    assert report.high_risk_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.low_risk_count == d("0.000000")
    assert report.stale_signal_count == d("0.000000")
    assert report.max_slippage_days == d("0.000000")
    assert report.min_days_to_x_date == d("0.000000")
    assert report.max_negotiation_stress_ratio == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("debt_ceiling_x_date_digest_empty",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_high_risk_slippage_digest_sorts_deterministically_for_event_screening() -> None:
    report = build_report(
        signal(
            "treasury-low",
            market_slug="low-risk-market",
            source_label="treasury-cash-balance",
            baseline_x_date=GENERATED_AT + timedelta(days=20),
            latest_x_date=GENERATED_AT + timedelta(days=18),
            observed_at=GENERATED_AT - timedelta(hours=2),
            negotiation_stress_ratio=d("0.100000"),
            probability_event_relevance=d("0.300000"),
            upstream_reason_codes=("treasury_cash_balance_update",),
        ),
        signal(
            "cbo-watch",
            market_slug="watch-risk-market",
            source_label="cbo-update",
            baseline_x_date=GENERATED_AT + timedelta(days=20),
            latest_x_date=GENERATED_AT + timedelta(days=15),
            observed_at=GENERATED_AT - timedelta(hours=1),
            negotiation_stress_ratio=d("0.500000"),
            probability_event_relevance=d("0.700000"),
            upstream_reason_codes=("cbo_x_date_window_update",),
        ),
        signal(
            "treasury-high",
            market_slug="high-risk-market",
            source_label="treasury-cash-balance",
            baseline_x_date=GENERATED_AT + timedelta(days=17),
            latest_x_date=GENERATED_AT + timedelta(days=5),
            observed_at=datetime(
                2026,
                7,
                4,
                7,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            negotiation_stress_ratio=d("0.800000"),
            probability_event_relevance=d("0.950000"),
            upstream_reason_codes=("treasury_cash_balance_update", "negotiation_impasse"),
        ),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_policy_debt_ceiling_x_date_digest"
    )
    assert report.input_count == d("3.000000")
    assert report.high_risk_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.low_risk_count == d("1.000000")
    assert report.stale_signal_count == d("0.000000")
    assert report.max_slippage_days == d("12.000000")
    assert report.min_days_to_x_date == d("5.000000")
    assert report.max_negotiation_stress_ratio == d("0.800000")
    assert report.reason_codes == (
        "debt_ceiling_x_date_high_risk_present",
        "debt_ceiling_x_date_watch_present",
        "x_date_slippage_blocked_present",
        "x_date_slippage_watch_present",
        "days_to_x_date_blocked_present",
        "negotiation_stress_blocked_present",
        "negotiation_stress_watch_present",
    )

    assert tuple(row.signal_id for row in report.rows) == (
        "treasury-high",
        "cbo-watch",
        "treasury-low",
    )
    high, watched, low = report.rows
    assert high.risk_status == "high_risk"
    assert high.days_to_x_date == d("5.000000")
    assert high.slippage_days == d("12.000000")
    assert high.signal_age_hours == d("1.000000")
    assert high.observed_at == datetime(2026, 7, 4, 11, 0, tzinfo=UTC)
    assert high.reason_codes == (
        "days_to_x_date_blocked",
        "negotiation_impasse",
        "negotiation_stress_blocked",
        "treasury_cash_balance_update",
        "x_date_slippage_blocked",
    )
    assert watched.risk_status == "watch"
    assert watched.reason_codes == (
        "cbo_x_date_window_update",
        "negotiation_stress_watch",
        "x_date_slippage_watch",
    )
    assert low.risk_status == "low_risk"
    assert low.reason_codes == ("treasury_cash_balance_update",)


def test_non_default_thresholds_change_classification() -> None:
    strict_report = build_report(
        signal(
            "deadline-sensitive",
            baseline_x_date=GENERATED_AT + timedelta(days=30),
            latest_x_date=GENERATED_AT + timedelta(days=23),
            negotiation_stress_ratio=d("0.200000"),
            probability_event_relevance=d("0.900000"),
        ),
        cfg=config(
            watch_days_to_x_date=d("14.000000"),
            blocked_days_to_x_date=d("7.000000"),
            watch_slippage_days=d("2.000000"),
            blocked_slippage_days=d("10.000000"),
            watch_negotiation_stress_ratio=d("0.300000"),
            blocked_negotiation_stress_ratio=d("0.900000"),
        ),
    )

    assert strict_report.digest_status == "watch"
    assert strict_report.watch_count == d("1.000000")
    assert strict_report.rows[0].risk_status == "watch"
    assert strict_report.rows[0].reason_codes == (
        "treasury_cash_balance_update",
        "x_date_slippage_watch",
    )


def test_validates_decimal_datetime_reason_codes_duplicates_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="negotiation_stress_ratio must be a Decimal"):
        signal("float-stress", negotiation_stress_ratio=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="probability_event_relevance must be a Decimal"):
        signal(
            "decimal-subclass",
            probability_event_relevance=_DecimalSubclass("0.500000"),
        )
    with pytest.raises(ValueError, match="probability_event_relevance must be between 0 and 1"):
        signal("bad-probability", probability_event_relevance=d("1.100000"))
    with pytest.raises(ValueError, match="latest_x_date must be timezone-aware"):
        signal("naive-latest", latest_x_date=datetime(2026, 7, 13, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_policy_debt_ceiling_x_date_digest(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        build_report(signal("future-signal", observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="inputs must not contain duplicate signal_id values"):
        build_report(signal("dupe"), signal("dupe"))
    with pytest.raises(ValueError, match="reason_codes must not contain duplicates"):
        signal("duplicate-reasons", upstream_reason_codes=("dup", "dup"))
    with pytest.raises(ValueError, match="watch_days_to_x_date must be at least blocked_days_to_x_date"):
        config(
            watch_days_to_x_date=d("5.000000"),
            blocked_days_to_x_date=d("10.000000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.DebtCeilingXDateSignal(
            signal_id="bad-flag",
            market_slug="bad-flag-market",
            source_label="treasury-cash-balance",
            baseline_x_date=BASELINE_X_DATE,
            latest_x_date=LATEST_X_DATE,
            observed_at=LAST_SIGNAL_AT,
            negotiation_stress_ratio=d("0.500000"),
            probability_event_relevance=d("0.800000"),
            upstream_reason_codes=("treasury_cash_balance_update",),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="config report_only must be True"):
        config(report_only=False)

    report = build_report(signal("frozen"))
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]


def test_public_contract_payload_decimal_strings_and_no_io_or_action_surfaces() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_MARKET_RESEARCH_POLICY_DEBT_CEILING_X_DATE_DIGEST_CONFIG_VERSION",
        "MarketResearchPolicyDebtCeilingXDateDigestConfig",
        "DebtCeilingXDateSignal",
        "DebtCeilingXDateDigestRow",
        "DebtCeilingXDateDigestReport",
        "build_market_research_policy_debt_ceiling_x_date_digest",
        "market_research_policy_debt_ceiling_x_date_digest_payload",
    )
    report = build_report(signal("payload"))
    payload = module.market_research_policy_debt_ceiling_x_date_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["days_to_x_date"] == "9.000000"
    assert payload["rows"][0]["slippage_days"] == "4.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_floats_or_public_decimals(payload)

    for value in (
        config(),
        signal("dataclass-contract"),
        report.rows[0],
        report,
    ):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen is True
        for field in fields(value):
            public_type = str(field.type).lower()
            assert "float" not in public_type
            assert "int" not in public_type
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if field.name.endswith(("_count", "_days", "_hours", "_ratio", "_relevance")):
                assert type(getattr(value, field.name)) is Decimal, field.name

    source = inspect.getsource(module)
    lowered = source.lower()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"

    for forbidden in (
        "requests",
        "httpx",
        "urlopen",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "connect(",
        "execute(",
        "open(",
        "private_key",
        "wallet",
        "order",
        "cancel",
        "replace",
        "exchange",
        "auth",
    ):
        assert forbidden not in lowered


def assert_no_floats_or_public_decimals(value: object) -> None:
    if isinstance(value, (float, Decimal)):
        pytest.fail("serialized payload must not contain floats or Decimals")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_floats_or_public_decimals(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_floats_or_public_decimals(item)
