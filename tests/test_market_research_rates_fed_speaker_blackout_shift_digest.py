from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.market_research_rates_fed_speaker_blackout_shift_digest"
)
GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(module: Any, **overrides: object) -> Any:
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_MARKET_RESEARCH_RATES_FED_SPEAKER_BLACKOUT_SHIFT_DIGEST_CONFIG_VERSION
        ),
        "watch_schedule_shift_hours": d("12.000000"),
        "blocked_schedule_shift_hours": d("24.000000"),
        "watch_blackout_proximity_hours": d("72.000000"),
        "blocked_blackout_proximity_hours": d("24.000000"),
        "watch_tone_shift_count": d("1.000000"),
        "blocked_tone_shift_count": d("2.000000"),
        "watch_market_move_score": d("0.250000"),
        "blocked_market_move_score": d("0.600000"),
        "watch_communication_risk_score": d("0.350000"),
        "blocked_communication_risk_score": d("0.650000"),
        "max_source_age_seconds": d("600.000000"),
        "stale_confidence_cap": d("0.300000"),
        "watch_confidence_cap": d("0.600000"),
    }
    values.update(overrides)
    return module.RatesFedSpeakerBlackoutShiftDigestConfig(**values)


def observation(
    module: Any,
    source_id: str = "source-alpha",
    *,
    market_slug: str = "july-fomc-rate-cut-probability",
    meeting_id: str = "fomc-2026-07-29",
    speaker_key: str = "fed.speaker.bowman",
    scheduled_at: datetime = datetime(2026, 8, 1, 14, 0, tzinfo=UTC),
    previous_scheduled_at: datetime | None = datetime(2026, 8, 1, 14, 0, tzinfo=UTC),
    blackout_start_at: datetime = datetime(2026, 8, 5, 0, 0, tzinfo=UTC),
    blackout_end_at: datetime = datetime(2026, 8, 6, 0, 0, tzinfo=UTC),
    observed_at: datetime = GENERATED_AT - timedelta(minutes=1),
    tone_shift_count: Decimal = d("0.000000"),
    hawkish_tone_shift_count: Decimal = d("0.000000"),
    dovish_tone_shift_count: Decimal = d("0.000000"),
    market_move_score: Decimal = d("0.050000"),
    base_confidence: Decimal = d("0.850000"),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return module.RatesFedSpeakerBlackoutShiftObservation(
        source_id=source_id,
        market_slug=market_slug,
        meeting_id=meeting_id,
        speaker_key=speaker_key,
        scheduled_at=scheduled_at,
        previous_scheduled_at=previous_scheduled_at,
        blackout_start_at=blackout_start_at,
        blackout_end_at=blackout_end_at,
        observed_at=observed_at,
        tone_shift_count=tone_shift_count,
        hawkish_tone_shift_count=hawkish_tone_shift_count,
        dovish_tone_shift_count=dovish_tone_shift_count,
        market_move_score=market_move_score,
        base_confidence=base_confidence,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(
    rows: tuple[object, ...],
    *,
    module: Any | None = None,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    digest_module = api() if module is None else module
    return digest_module.build_market_research_rates_fed_speaker_blackout_shift_digest(
        rows,
        config=cfg or config(digest_module),
        generated_at=generated_at,
    )


def test_builds_blackout_shift_digest_for_rates_probability_events() -> None:
    module = api()

    report = digest(
        (
            observation(
                module,
                "beta-watch",
                market_slug="september-fomc-25bp-cut-watch",
                meeting_id="fomc-2026-09-16",
                speaker_key="fed.speaker.waller",
                scheduled_at=datetime(2026, 7, 27, 10, 0, tzinfo=UTC),
                previous_scheduled_at=datetime(2026, 7, 26, 18, 0, tzinfo=UTC),
                blackout_start_at=datetime(2026, 7, 29, 0, 0, tzinfo=UTC),
                blackout_end_at=datetime(2026, 7, 30, 0, 0, tzinfo=UTC),
                tone_shift_count=d("1.000000"),
                hawkish_tone_shift_count=d("0.000000"),
                dovish_tone_shift_count=d("1.000000"),
                market_move_score=d("0.350000"),
                upstream_reason_codes=("fedwatch_calendar",),
            ),
            observation(
                module,
                "alpha-pass",
                market_slug="december-fomc-hold-calm",
                meeting_id="fomc-2026-12-16",
                speaker_key="fed.speaker.bowman",
                observed_at=datetime(
                    2026,
                    7,
                    4,
                    7,
                    59,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
            ),
            observation(
                module,
                "zeta-high",
                market_slug="july-fomc-hawkish-speaker-risk",
                speaker_key="fed.speaker.powell",
                scheduled_at=datetime(2026, 7, 27, 13, 0, tzinfo=UTC),
                previous_scheduled_at=datetime(2026, 7, 26, 8, 0, tzinfo=UTC),
                blackout_start_at=datetime(2026, 7, 27, 20, 0, tzinfo=UTC),
                blackout_end_at=datetime(2026, 7, 28, 20, 0, tzinfo=UTC),
                observed_at=GENERATED_AT - timedelta(seconds=900),
                tone_shift_count=d("3.000000"),
                hawkish_tone_shift_count=d("3.000000"),
                dovish_tone_shift_count=d("0.000000"),
                market_move_score=d("0.720000"),
                base_confidence=d("0.900000"),
                upstream_reason_codes=("primary_calendar_update", "fedwatch_calendar"),
            ),
        ),
        module=module,
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-rates-fed-speaker-blackout-shift-digest-v0"
    )
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.blocked_signal_count == d("1.000000")
    assert report.watch_signal_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.schedule_shift_count == d("2.000000")
    assert report.blackout_proximity_count == d("2.000000")
    assert report.tone_shift_event_count == d("2.000000")
    assert report.total_tone_shift_count == d("4.000000")
    assert report.hawkish_tone_shift_count == d("1.000000")
    assert report.dovish_tone_shift_count == d("1.000000")
    assert report.market_move_count == d("2.000000")
    assert report.stale_source_count == d("1.000000")
    assert report.max_schedule_shift_hours == d("29.000000")
    assert report.min_blackout_proximity_hours == d("7.000000")
    assert report.max_communication_risk_score == d("0.916000")
    assert report.average_communication_risk_score == d("0.478667")
    assert report.average_market_move_score == d("0.373333")
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_rates_fed_speaker_blackout_shift_digest"
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert [(row.source_id, row.signal_status, row.communication_risk_score) for row in report.rows] == [
        ("zeta-high", "blocked", d("0.916000")),
        ("beta-watch", "watch", d("0.505000")),
        ("alpha-pass", "pass", d("0.015000")),
    ]

    blocked, watched, passed = report.rows
    assert blocked.schedule_shift_hours == d("29.000000")
    assert blocked.blackout_proximity_hours == d("7.000000")
    assert blocked.source_age_seconds == d("900.000000")
    assert blocked.confidence_cap == d("0.300000")
    assert blocked.capped_confidence == d("0.300000")
    assert blocked.reason_codes == (
        "fedwatch_calendar",
        "primary_calendar_update",
        "rates_fed_speaker_blackout_shift_blackout_proximity_blocked",
        "rates_fed_speaker_blackout_shift_communication_risk_high",
        "rates_fed_speaker_blackout_shift_market_move_blocked",
        "rates_fed_speaker_blackout_shift_schedule_moved_blocked",
        "rates_fed_speaker_blackout_shift_source_stale",
        "rates_fed_speaker_blackout_shift_tone_hawkish",
        "rates_fed_speaker_blackout_shift_tone_shift_blocked",
    )
    assert watched.confidence_cap == d("0.600000")
    assert watched.capped_confidence == d("0.600000")
    assert watched.reason_codes == (
        "fedwatch_calendar",
        "rates_fed_speaker_blackout_shift_blackout_proximity_watch",
        "rates_fed_speaker_blackout_shift_communication_risk_watch",
        "rates_fed_speaker_blackout_shift_market_move_watch",
        "rates_fed_speaker_blackout_shift_schedule_moved_watch",
        "rates_fed_speaker_blackout_shift_source_fresh",
        "rates_fed_speaker_blackout_shift_tone_dovish",
        "rates_fed_speaker_blackout_shift_tone_shift_watch",
    )
    assert passed.observed_at == datetime(2026, 7, 4, 11, 59, tzinfo=UTC)
    assert passed.reason_codes == (
        "rates_fed_speaker_blackout_shift_communication_risk_calm",
        "rates_fed_speaker_blackout_shift_schedule_unchanged",
        "rates_fed_speaker_blackout_shift_source_fresh",
        "rates_fed_speaker_blackout_shift_tone_none",
    )
    assert report.reason_codes == tuple(
        item.reason_code for item in report.reason_code_counts
    )
    assert report.reason_code_counts[0] == (
        module.RatesFedSpeakerBlackoutShiftReasonCodeCount(
            reason_code="fedwatch_calendar",
            count=d("2.000000"),
            row_ratio=d("0.666667"),
        )
    )


def test_empty_digest_is_blocked_report_only_and_decimal_stringed() -> None:
    module = api()

    report = digest((), module=module)
    payload = module.market_research_rates_fed_speaker_blackout_shift_digest_payload(
        report,
    )
    json.dumps(payload, sort_keys=True)

    assert report.digest_status == "blocked"
    assert report.input_count == ZERO
    assert report.row_count == ZERO
    assert report.schedule_shift_count == ZERO
    assert report.blackout_proximity_count == ZERO
    assert report.total_tone_shift_count == ZERO
    assert report.max_schedule_shift_hours == ZERO
    assert report.min_blackout_proximity_hours == ZERO
    assert report.max_communication_risk_score == ZERO
    assert report.average_communication_risk_score == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("rates_fed_speaker_blackout_shift_digest_empty",)
    assert report.reason_code_counts == (
        module.RatesFedSpeakerBlackoutShiftReasonCodeCount(
            reason_code="rates_fed_speaker_blackout_shift_digest_empty",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["row_count"] == "0.000000"
    assert payload["reason_code_counts"][0]["row_ratio"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_decimal_or_datetime(payload)


def test_non_default_thresholds_can_downgrade_schedule_shift_to_watch() -> None:
    module = api()
    tuned_config = config(
        module,
        blocked_schedule_shift_hours=d("40.000000"),
        blocked_communication_risk_score=d("0.900000"),
    )

    report = digest(
        (
            observation(
                module,
                scheduled_at=datetime(2026, 7, 27, 13, 0, tzinfo=UTC),
                previous_scheduled_at=datetime(2026, 7, 26, 8, 0, tzinfo=UTC),
                blackout_start_at=datetime(2026, 8, 5, 0, 0, tzinfo=UTC),
                blackout_end_at=datetime(2026, 8, 6, 0, 0, tzinfo=UTC),
                market_move_score=d("0.100000"),
            ),
        ),
        module=module,
        cfg=tuned_config,
    )

    assert report.digest_status == "watch"
    assert report.blocked_signal_count == ZERO
    assert report.watch_signal_count == d("1.000000")
    assert report.rows[0].signal_status == "watch"
    assert "rates_fed_speaker_blackout_shift_schedule_moved_watch" in (
        report.rows[0].reason_codes
    )
    assert "rates_fed_speaker_blackout_shift_schedule_moved_blocked" not in (
        report.rows[0].reason_codes
    )


def test_rejects_bad_inputs_duplicates_inconsistent_rows_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="tone_shift_count"):
        observation(module, tone_shift_count=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="tone_shift_count must equal"):
        observation(
            module,
            tone_shift_count=d("2.000000"),
            hawkish_tone_shift_count=d("1.000000"),
            dovish_tone_shift_count=d("0.000000"),
        )
    with pytest.raises(ValueError, match="market_move_score"):
        observation(module, market_move_score=d("1.000001"))
    with pytest.raises(ValueError, match="observed_at"):
        observation(module, observed_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="scheduled_at"):
        observation(module, scheduled_at=_DatetimeSubclass(2026, 7, 27, tzinfo=UTC))
    with pytest.raises(ValueError, match="blackout_end_at"):
        observation(
            module,
            blackout_start_at=datetime(2026, 8, 6, 0, 0, tzinfo=UTC),
            blackout_end_at=datetime(2026, 8, 5, 0, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="watch_schedule_shift_hours"):
        config(module, watch_schedule_shift_hours=d("30.000000"))
    with pytest.raises(ValueError, match="blocked_blackout_proximity_hours"):
        config(module, blocked_blackout_proximity_hours=d("80.000000"))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        digest(
            (observation(module, observed_at=GENERATED_AT + timedelta(seconds=1)),),
            module=module,
        )
    with pytest.raises(ValueError, match="duplicate source_id"):
        digest((observation(module, "dupe"), observation(module, "dupe")), module=module)
    with pytest.raises(ValueError, match="paper_only"):
        observation(module, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(module, readonly=False)
    with pytest.raises(ValueError, match="config"):
        module.build_market_research_rates_fed_speaker_blackout_shift_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    report = digest((observation(module),), module=module)
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]
    with pytest.raises(ValueError, match="schedule_shift_hours"):
        replace(report.rows[0], schedule_shift_hours=d("99.000000"))
    with pytest.raises(ValueError, match="signal_status"):
        replace(report.rows[0], signal_status="blocked")
    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=d("2.000000"))


def test_public_numeric_fields_are_decimal_and_payload_uses_six_decimal_strings() -> None:
    module = api()
    report = digest((observation(module),), module=module)
    payload = module.market_research_rates_fed_speaker_blackout_shift_digest_payload(
        report,
    )

    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["schedule_shift_hours"] == "0.000000"
    assert payload["rows"][0]["scheduled_at"] == "2026-08-01T14:00:00+00:00"
    assert_no_float_decimal_or_datetime(payload)

    for public_record in (
        config(module),
        observation(module),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        assert_decimal_public_numeric_fields(public_record)


def test_module_scope_is_pure_without_live_or_durable_surfaces() -> None:
    module = api()
    source = inspect.getsource(module).lower()
    tree = ast.parse(
        Path(
            "src/polymarket_alpha_lab/market_research_rates_fed_speaker_blackout_shift_digest.py",
        ).read_text(encoding="utf-8"),
    )

    imported_modules: set[str] = set()
    call_names: list[str] = []
    attribute_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    forbidden_import_fragments = (
        "db",
        "env",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "websocket",
        "aiohttp",
        "psycopg",
        "supabase",
        "sqlite",
        "sqlalchemy",
        "pathlib",
        "subprocess",
    )
    forbidden_call_or_attribute_names = (
        "connect",
        "execute",
        "fetch",
        "get",
        "post",
        "put",
        "delete",
        "request",
        "open",
        "read",
        "write",
        "mkdir",
        "unlink",
        "rename",
        "submit",
        "cancel",
        "order",
        "trade",
        "wallet",
        "account",
        "sign",
        "auth",
    )

    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert not any(
        name.lower() in forbidden_call_or_attribute_names
        for name in (*call_names, *attribute_names)
    )
    for forbidden in (
        "live trading",
        "private_key",
        "wallet",
        "submit_order",
        "cancel_order",
        "replace_order",
        "auth",
        "secret",
        "database",
        "network",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "http",
    ):
        assert forbidden not in source


def assert_no_float_decimal_or_datetime(value: object) -> None:
    if isinstance(value, (float, Decimal, datetime)):
        pytest.fail("payload must contain only JSON-ready scalar numerics and datetimes")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_float_decimal_or_datetime(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_float_decimal_or_datetime(child)


def assert_decimal_public_numeric_fields(value: object) -> None:
    numeric_markers = (
        "age_seconds",
        "average",
        "cap",
        "count",
        "hours",
        "max_",
        "min_",
        "ratio",
        "score",
        "threshold",
    )
    for field in fields(value):
        if field.name.endswith(("codes", "counts", "rows")):
            continue
        field_value = getattr(value, field.name)
        if any(marker in field.name for marker in numeric_markers):
            if field_value is not None:
                assert type(field_value) is Decimal, field.name
