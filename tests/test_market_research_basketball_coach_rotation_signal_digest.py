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


GENERATED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_basketball_coach_rotation_signal_digest.py",
)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_basketball_coach_rotation_signal_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def signal(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "condition_id": "nba-lal-bos-2026-11-15-rotation",
        "league_key": "nba",
        "team_key": "lal",
        "coach_key": "coach-redick",
        "rotation_unit_key": "lal-second-unit",
        "source_ref": "team-availability-note",
        "observed_at": GENERATED_AT - timedelta(hours=3),
        "baseline_minutes": d("32.000000"),
        "projected_minutes": d("22.000000"),
        "baseline_bench_share": d("0.240000"),
        "projected_bench_share": d("0.420000"),
        "signal_confidence": d("0.820000"),
        "coach_rotation_signal_active": True,
    }
    values.update(overrides)
    return module.MarketResearchBasketballCoachRotationSignalDigestSignal(**values)


def report(*signals: object, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_market_research_basketball_coach_rotation_signal_digest(
        signals,
        config=module.MarketResearchBasketballCoachRotationSignalDigestConfig(),
        generated_at=generated_at,
    )


def assert_no_floats(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in JSON payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_floats(item)
    if isinstance(value, list):
        for item in value:
            assert_no_floats(item)


def assert_no_public_int_payload_numerics(value: object) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, int):
        raise AssertionError(f"int found in public payload: {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_public_int_payload_numerics(child)
    if isinstance(value, list):
        for child in value:
            assert_no_public_int_payload_numerics(child)


def test_empty_input_returns_report_only_pass_digest() -> None:
    digest = report()

    assert digest.generated_at == GENERATED_AT
    assert (
        digest.config_version
        == "market-research-basketball-coach-rotation-signal-digest-v0"
    )
    assert digest.research_scope == (
        "basketball coach rotation signal research digest only"
    )
    assert digest.digest_status == "pass"
    assert digest.recommended_next_step == (
        "continue_report_only_basketball_coach_rotation_signal_monitoring"
    )
    assert digest.rotation_unit_count == d("0.000000")
    assert digest.signal_count == d("0.000000")
    assert digest.clear_unit_count == d("0.000000")
    assert digest.watch_unit_count == d("0.000000")
    assert digest.high_score_unit_count == d("0.000000")
    assert digest.active_signal_unit_count == d("0.000000")
    assert digest.high_minutes_delta_unit_count == d("0.000000")
    assert digest.high_bench_share_delta_unit_count == d("0.000000")
    assert digest.high_confidence_unit_count == d("0.000000")
    assert digest.stale_signal_unit_count == d("0.000000")
    assert digest.max_rotation_signal_score == d("0.000000")
    assert digest.max_minutes_delta_abs == d("0.000000")
    assert digest.max_signal_age_seconds == d("0.000000")
    assert digest.average_signal_confidence == d("0.000000")
    assert digest.rows == ()
    assert digest.reason_code_counts == ()
    assert digest.reason_codes == ("basketball_coach_rotation_signal_empty",)
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True


def test_active_coach_signal_builds_watch_row_with_decimal_metrics() -> None:
    digest = report(signal())

    assert digest.digest_status == "watch"
    assert digest.recommended_next_step == (
        "review_report_only_basketball_coach_rotation_signals"
    )
    assert digest.rotation_unit_count == d("1.000000")
    assert digest.signal_count == d("1.000000")
    assert digest.clear_unit_count == d("0.000000")
    assert digest.watch_unit_count == d("1.000000")
    assert digest.high_score_unit_count == d("1.000000")
    assert digest.active_signal_unit_count == d("1.000000")
    assert digest.high_minutes_delta_unit_count == d("1.000000")
    assert digest.high_bench_share_delta_unit_count == d("1.000000")
    assert digest.high_confidence_unit_count == d("1.000000")
    assert digest.stale_signal_unit_count == d("1.000000")
    assert digest.max_rotation_signal_score == d("1.000000")
    assert digest.max_minutes_delta_abs == d("10.000000")
    assert digest.max_signal_age_seconds == d("10800.000000")
    assert digest.average_signal_confidence == d("0.820000")
    assert digest.reason_codes == (
        "basketball_coach_rotation_signal_score_high",
        "basketball_coach_rotation_signal_active",
        "basketball_coach_rotation_minutes_delta_high",
        "basketball_coach_rotation_bench_share_delta_high",
        "basketball_coach_rotation_confidence_high",
        "basketball_coach_rotation_signal_stale",
    )

    row = digest.rows[0]
    assert row.condition_id == "nba-lal-bos-2026-11-15-rotation"
    assert row.league_key == "nba"
    assert row.team_key == "lal"
    assert row.coach_key == "coach-redick"
    assert row.rotation_unit_key == "lal-second-unit"
    assert row.signal_count == d("1.000000")
    assert row.observed_at_latest == GENERATED_AT - timedelta(hours=3)
    assert row.minutes_delta_abs_max == d("10.000000")
    assert row.bench_share_delta_abs_max == d("0.180000")
    assert row.signal_confidence_max == d("0.820000")
    assert row.rotation_signal_score == d("1.000000")
    assert row.signal_age_seconds == d("10800.000000")
    assert row.digest_status == "watch"
    assert row.reason_codes == digest.reason_codes
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_rows_and_reason_code_counts_sort_deterministically() -> None:
    digest = report(
        signal(
            condition_id="z-condition",
            rotation_unit_key="z-unit",
            source_ref="z-source",
            coach_rotation_signal_active=False,
            baseline_minutes=d("28.000000"),
            projected_minutes=d("27.000000"),
            baseline_bench_share=d("0.250000"),
            projected_bench_share=d("0.260000"),
            signal_confidence=d("0.500000"),
            observed_at=GENERATED_AT - timedelta(minutes=30),
        ),
        signal(
            condition_id="a-condition",
            rotation_unit_key="a-unit",
            source_ref="a-source",
            coach_rotation_signal_active=False,
            baseline_minutes=d("34.000000"),
            projected_minutes=d("25.000000"),
            baseline_bench_share=d("0.180000"),
            projected_bench_share=d("0.210000"),
            signal_confidence=d("0.660000"),
            observed_at=GENERATED_AT - timedelta(hours=1),
        ),
        signal(
            condition_id="m-condition",
            rotation_unit_key="m-unit",
            source_ref="m-source",
            coach_rotation_signal_active=False,
            baseline_minutes=d("20.000000"),
            projected_minutes=d("20.000000"),
            baseline_bench_share=d("0.100000"),
            projected_bench_share=d("0.300000"),
            signal_confidence=d("0.720000"),
            observed_at=GENERATED_AT - timedelta(hours=2),
        ),
    )

    assert tuple(row.rotation_unit_key for row in digest.rows) == (
        "m-unit",
        "a-unit",
        "z-unit",
    )
    assert tuple((item.reason_code, item.unit_count) for item in digest.reason_code_counts) == (
        ("basketball_coach_rotation_signal_score_high", d("2.000000")),
        ("basketball_coach_rotation_minutes_delta_high", d("1.000000")),
        ("basketball_coach_rotation_bench_share_delta_high", d("1.000000")),
        ("basketball_coach_rotation_confidence_high", d("1.000000")),
    )


def test_offset_datetimes_normalize_to_utc_and_naive_datetimes_are_rejected() -> None:
    digest = report(
        signal(
            observed_at=datetime(
                2026,
                7,
                4,
                8,
                0,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        generated_at=datetime(2026, 7, 4, 11, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    row = digest.rows[0]
    assert digest.generated_at == GENERATED_AT
    assert row.observed_at_latest == datetime(2026, 7, 4, 15, 0, tzinfo=UTC)
    assert row.signal_age_seconds == d("10800.000000")

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(signal(), generated_at=datetime(2026, 7, 4, 18, 0))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 4, 15, 0))
    with pytest.raises(ValueError, match="observed_at values must be at or before generated_at"):
        report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        signal(observed_at=_DatetimeSubclass(2026, 7, 4, 15, 0, tzinfo=UTC))


def test_payload_uses_six_decimal_strings_iso_datetimes_and_no_public_ints() -> None:
    payload = api().market_research_basketball_coach_rotation_signal_digest_payload(
        report(signal()),
    )

    json.dumps(payload, sort_keys=True)
    assert_no_floats(payload)
    assert_no_public_int_payload_numerics(payload)
    assert payload["generated_at"] == "2026-07-04T18:00:00Z"
    assert payload["rotation_unit_count"] == "1.000000"
    assert payload["signal_count"] == "1.000000"
    assert payload["max_rotation_signal_score"] == "1.000000"
    assert payload["rows"][0]["observed_at_latest"] == "2026-07-04T15:00:00Z"
    assert payload["rows"][0]["minutes_delta_abs_max"] == "10.000000"
    assert payload["reason_code_counts"][0]["unit_count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_validation_rejects_bad_values_flags_duplicates_and_manual_drift() -> None:
    module = api()

    with pytest.raises(ValueError, match="baseline_minutes must be a Decimal"):
        signal(baseline_minutes=_DecimalSubclass("32.000000"))
    with pytest.raises(ValueError, match="baseline_minutes must be nonnegative"):
        signal(baseline_minutes=d("-1.000000"))
    with pytest.raises(ValueError, match="projected_bench_share must be at most 1"):
        signal(projected_bench_share=d("1.000001"))
    with pytest.raises(ValueError, match="coach_rotation_signal_active must be a bool"):
        signal(coach_rotation_signal_active="true")
    with pytest.raises(ValueError, match="reason_codes must be unique"):
        module.MarketResearchBasketballCoachRotationSignalDigestRow(
            condition_id="c",
            league_key="nba",
            team_key="lal",
            coach_key="coach-redick",
            rotation_unit_key="unit",
            signal_count=d("1.000000"),
            observed_at_latest=GENERATED_AT,
            minutes_delta_abs_max=d("0.000000"),
            bench_share_delta_abs_max=d("0.000000"),
            signal_confidence_max=d("0.000000"),
            rotation_signal_score=d("0.000000"),
            signal_age_seconds=d("0.000000"),
            digest_status="clear",
            reason_codes=(
                "basketball_coach_rotation_signal_clear",
                "basketball_coach_rotation_signal_clear",
            ),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        module.MarketResearchBasketballCoachRotationSignalDigestConfig(report_only=False)
    with pytest.raises(ValueError, match="signals must not contain duplicate"):
        report(signal(), signal())

    digest = report(signal())
    with pytest.raises(ValueError, match="rotation_unit_count must match rows"):
        replace(digest, rotation_unit_count=d("2.000000"))
    with pytest.raises(ValueError, match="reason_code_counts must match rows"):
        replace(digest, reason_code_counts=tuple(reversed(digest.reason_code_counts)))
    with pytest.raises(ValueError, match="clear rows must use the clear reason"):
        replace(digest.rows[0], digest_status="clear")
    with pytest.raises(
        ValueError,
        match="report must be exactly "
        "MarketResearchBasketballCoachRotationSignalDigestReport",
    ):
        module.market_research_basketball_coach_rotation_signal_digest_payload(
            report="bad",
        )


def test_public_dataclasses_are_frozen_and_decimal_only() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_MARKET_RESEARCH_BASKETBALL_COACH_ROTATION_SIGNAL_DIGEST_CONFIG_VERSION",
        "BASKETBALL_COACH_ROTATION_SIGNAL_RESEARCH_SCOPE",
        "MarketResearchBasketballCoachRotationSignalDigestConfig",
        "MarketResearchBasketballCoachRotationSignalDigestSignal",
        "MarketResearchBasketballCoachRotationSignalDigestReasonCodeCount",
        "MarketResearchBasketballCoachRotationSignalDigestRow",
        "MarketResearchBasketballCoachRotationSignalDigestReport",
        "build_market_research_basketball_coach_rotation_signal_digest",
        "market_research_basketball_coach_rotation_signal_digest_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    digest = report(signal())
    with pytest.raises(FrozenInstanceError):
        digest.digest_status = "pass"
    with pytest.raises(FrozenInstanceError):
        digest.rows[0].digest_status = "clear"

    for value in (
        module.MarketResearchBasketballCoachRotationSignalDigestConfig(),
        signal(),
        digest,
        digest.rows[0],
        digest.reason_code_counts[0],
    ):
        for field in fields(value):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            public_value = getattr(value, field.name)
            if field.name.endswith(
                (
                    "_count",
                    "_score",
                    "_threshold",
                    "_seconds",
                    "_confidence",
                    "_minutes",
                    "_share",
                    "_delta_abs",
                ),
            ):
                assert type(public_value) is Decimal


def test_static_forbidden_surface_terms_and_io_are_absent() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live_trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "exchange_mutation",
        "private_key",
        "api_key",
        "secret",
        "client",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
        "sqlite",
        "postgres",
        "supabase",
        "write_text",
        "write_bytes",
        "fast_mode",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "int", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
