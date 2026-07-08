from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
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
    / "research_domain_baseball_signal_memory_quality_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_domain_baseball_signal_memory_quality_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def input_row(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "event_bucket": "mlb_regular_season",
        "memory_scope": "probable_pitcher_lineup_weather_schedule",
        "pitcher_memory_observed_at": GENERATED_AT - timedelta(minutes=25),
        "lineup_memory_observed_at": GENERATED_AT - timedelta(minutes=20),
        "weather_memory_observed_at": GENERATED_AT - timedelta(minutes=45),
        "schedule_memory_observed_at": GENERATED_AT - timedelta(minutes=50),
        "pitcher_memory_score": d("0.920000"),
        "lineup_memory_score": d("0.880000"),
        "weather_memory_score": d("0.860000"),
        "schedule_memory_score": d("0.900000"),
        "pitcher_conflict_count": d("0.000000"),
        "lineup_conflict_count": d("0.000000"),
        "weather_conflict_count": d("0.000000"),
        "schedule_conflict_count": d("0.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchDomainBaseballSignalMemoryQualityInputRow(**values)


def report(rows: tuple[Any, ...], **overrides: object):
    module = api()
    cfg = overrides.pop("config", None) or (
        module.ResearchDomainBaseballSignalMemoryQualityConfig()
    )
    return module.build_research_domain_baseball_signal_memory_quality_report(
        rows,
        config=cfg,
        generated_at=overrides.pop("generated_at", GENERATED_AT),
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


def test_baseball_signal_memory_quality_flags_stale_conflicting_and_missing_inputs() -> None:
    module = api()

    summary = report(
        (
            input_row(
                event_bucket="alpha_ready",
                pitcher_memory_observed_at=GENERATED_AT - timedelta(minutes=20),
                lineup_memory_observed_at=GENERATED_AT - timedelta(minutes=15),
                weather_memory_observed_at=GENERATED_AT - timedelta(minutes=30),
                schedule_memory_observed_at=GENERATED_AT - timedelta(minutes=40),
                pitcher_memory_score=d("0.940000"),
                lineup_memory_score=d("0.900000"),
                weather_memory_score=d("0.880000"),
                schedule_memory_score=d("0.920000"),
            ),
            input_row(
                event_bucket="beta_watch",
                pitcher_memory_observed_at=GENERATED_AT - timedelta(minutes=70),
                lineup_memory_observed_at=GENERATED_AT - timedelta(minutes=50),
                weather_memory_observed_at=GENERATED_AT - timedelta(hours=3),
                schedule_memory_observed_at=GENERATED_AT - timedelta(minutes=40),
                pitcher_memory_score=d("0.760000"),
                lineup_memory_score=d("0.700000"),
                weather_memory_score=d("0.660000"),
                schedule_memory_score=d("0.740000"),
                pitcher_conflict_count=d("1.000000"),
                weather_conflict_count=d("1.000000"),
            ),
            input_row(
                event_bucket="gamma_block",
                pitcher_memory_observed_at=None,
                lineup_memory_observed_at=GENERATED_AT - timedelta(hours=5),
                weather_memory_observed_at=None,
                schedule_memory_observed_at=GENERATED_AT - timedelta(hours=8),
                pitcher_memory_score=d("0.420000"),
                lineup_memory_score=d("0.480000"),
                weather_memory_score=d("0.500000"),
                schedule_memory_score=d("0.440000"),
                lineup_conflict_count=d("2.000000"),
                schedule_conflict_count=d("3.000000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, module.ResearchDomainBaseballSignalMemoryQualityReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.report_status == "block"
    assert summary.handoff_gate_label == (
        "block_report_only_baseball_signal_memory_forecast_handoff"
    )
    assert summary.event_bucket_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.stale_bucket_count == d("2.000000")
    assert summary.conflicting_bucket_count == d("2.000000")
    assert summary.missing_bucket_count == d("1.000000")
    assert summary.average_memory_score == d("0.695000")
    assert summary.average_freshness_score == d("0.500000")
    assert summary.average_conflict_score == d("0.500000")
    assert summary.pitcher_missing_count == d("1.000000")
    assert summary.lineup_stale_count == d("1.000000")
    assert summary.weather_missing_count == d("1.000000")
    assert summary.schedule_stale_count == d("1.000000")
    assert summary.max_schedule_age_seconds == d("28800.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.event_bucket for row in summary.rows) == (
        "gamma_block",
        "beta_watch",
        "alpha_ready",
    )

    blocked, watched, passed = summary.rows
    assert blocked.public_status == "block"
    assert blocked.freshness_status == "block"
    assert blocked.conflict_status == "block"
    assert blocked.pitcher_age_seconds is None
    assert blocked.lineup_age_seconds == d("18000.000000")
    assert blocked.weather_age_seconds is None
    assert blocked.schedule_age_seconds == d("28800.000000")
    assert blocked.composite_memory_score == d("0.460000")
    assert blocked.freshness_score == d("0.000000")
    assert blocked.conflict_score == d("0.000000")
    assert blocked.reason_codes == (
        "baseball_signal_memory_quality_conflict_block",
        "baseball_signal_memory_quality_lineup_conflicting",
        "baseball_signal_memory_quality_lineup_stale",
        "baseball_signal_memory_quality_memory_score_block",
        "baseball_signal_memory_quality_pitcher_missing",
        "baseball_signal_memory_quality_schedule_conflicting",
        "baseball_signal_memory_quality_schedule_stale",
        "baseball_signal_memory_quality_weather_missing",
    )

    assert watched.public_status == "watch"
    assert watched.freshness_status == "watch"
    assert watched.conflict_status == "watch"
    assert watched.composite_memory_score == d("0.715000")
    assert watched.freshness_score == d("0.500000")
    assert watched.conflict_score == d("0.500000")
    assert watched.reason_codes == (
        "baseball_signal_memory_quality_conflict_watch",
        "baseball_signal_memory_quality_memory_score_watch",
        "baseball_signal_memory_quality_pitcher_conflicting",
        "baseball_signal_memory_quality_pitcher_stale",
        "baseball_signal_memory_quality_watch",
        "baseball_signal_memory_quality_weather_conflicting",
        "baseball_signal_memory_quality_weather_stale",
    )

    assert passed.public_status == "pass"
    assert passed.freshness_status == "pass"
    assert passed.conflict_status == "pass"
    assert passed.composite_memory_score == d("0.910000")
    assert passed.freshness_score == d("1.000000")
    assert passed.conflict_score == d("1.000000")
    assert passed.reason_codes == (
        "baseball_signal_memory_quality_fresh",
        "baseball_signal_memory_quality_no_conflict",
        "baseball_signal_memory_quality_pass",
    )

    assert summary.reason_code_counts == (
        module.ResearchDomainBaseballSignalMemoryQualityReasonCodeCount(
            reason_code="baseball_signal_memory_quality_conflict_block",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchDomainBaseballSignalMemoryQualityReasonCodeCount(
            reason_code="baseball_signal_memory_quality_conflict_watch",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchDomainBaseballSignalMemoryQualityReasonCodeCount(
            reason_code="baseball_signal_memory_quality_fresh",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchDomainBaseballSignalMemoryQualityReasonCodeCount(
            reason_code="baseball_signal_memory_quality_lineup_conflicting",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchDomainBaseballSignalMemoryQualityReasonCodeCount(
            reason_code="baseball_signal_memory_quality_lineup_stale",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchDomainBaseballSignalMemoryQualityReasonCodeCount(
            reason_code="baseball_signal_memory_quality_memory_score_block",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchDomainBaseballSignalMemoryQualityReasonCodeCount(
            reason_code="baseball_signal_memory_quality_memory_score_watch",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchDomainBaseballSignalMemoryQualityReasonCodeCount(
            reason_code="baseball_signal_memory_quality_no_conflict",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchDomainBaseballSignalMemoryQualityReasonCodeCount(
            reason_code="baseball_signal_memory_quality_pass",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchDomainBaseballSignalMemoryQualityReasonCodeCount(
            reason_code="baseball_signal_memory_quality_pitcher_conflicting",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchDomainBaseballSignalMemoryQualityReasonCodeCount(
            reason_code="baseball_signal_memory_quality_pitcher_missing",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchDomainBaseballSignalMemoryQualityReasonCodeCount(
            reason_code="baseball_signal_memory_quality_pitcher_stale",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchDomainBaseballSignalMemoryQualityReasonCodeCount(
            reason_code="baseball_signal_memory_quality_schedule_conflicting",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchDomainBaseballSignalMemoryQualityReasonCodeCount(
            reason_code="baseball_signal_memory_quality_schedule_stale",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchDomainBaseballSignalMemoryQualityReasonCodeCount(
            reason_code="baseball_signal_memory_quality_watch",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchDomainBaseballSignalMemoryQualityReasonCodeCount(
            reason_code="baseball_signal_memory_quality_weather_conflicting",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchDomainBaseballSignalMemoryQualityReasonCodeCount(
            reason_code="baseball_signal_memory_quality_weather_missing",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchDomainBaseballSignalMemoryQualityReasonCodeCount(
            reason_code="baseball_signal_memory_quality_weather_stale",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(row.reason_code for row in summary.reason_code_counts)


def test_empty_inputs_return_block_report_only_digest() -> None:
    module = api()
    summary = report(())

    assert summary.report_status == "block"
    assert summary.event_bucket_count == d("0.000000")
    assert summary.rows == ()
    assert summary.reason_codes == ("baseball_signal_memory_quality_no_inputs",)
    assert summary.reason_code_counts == (
        module.ResearchDomainBaseballSignalMemoryQualityReasonCodeCount(
            reason_code="baseball_signal_memory_quality_no_inputs",
            count=d("1.000000"),
            event_ratio=d("0.000000"),
        ),
    )
    assert summary.derived_validation_digest == (
        module.research_domain_baseball_signal_memory_quality_report_digest(summary)
    )


def test_payload_is_deterministic_public_decimal_only_and_digest_validated() -> None:
    module = api()
    first = report(
        (
            input_row(
                event_bucket="zeta_watch",
                pitcher_memory_observed_at=GENERATED_AT - timedelta(minutes=70),
                weather_memory_observed_at=GENERATED_AT - timedelta(hours=3),
                pitcher_memory_score=d("0.760000"),
                lineup_memory_score=d("0.700000"),
                weather_memory_score=d("0.660000"),
                schedule_memory_score=d("0.740000"),
                pitcher_conflict_count=d("1.000000"),
                weather_conflict_count=d("1.000000"),
            ),
            input_row(event_bucket="alpha_pass"),
        ),
    )
    second = report(
        (
            input_row(event_bucket="alpha_pass"),
            input_row(
                event_bucket="zeta_watch",
                pitcher_memory_observed_at=GENERATED_AT - timedelta(minutes=70),
                weather_memory_observed_at=GENERATED_AT - timedelta(hours=3),
                pitcher_memory_score=d("0.760000"),
                lineup_memory_score=d("0.700000"),
                weather_memory_score=d("0.660000"),
                schedule_memory_score=d("0.740000"),
                pitcher_conflict_count=d("1.000000"),
                weather_conflict_count=d("1.000000"),
            ),
        ),
    )

    first_payload = module.research_domain_baseball_signal_memory_quality_report_payload(first)
    second_payload = module.research_domain_baseball_signal_memory_quality_report_payload(second)
    first_digest = module.research_domain_baseball_signal_memory_quality_report_digest(first)

    assert first_payload == second_payload
    assert first_digest == (
        module.research_domain_baseball_signal_memory_quality_report_digest(second)
    )
    assert first.payload == first_payload
    assert first.derived_validation_digest == first_digest
    assert len(first_digest) == 64
    assert first_payload["derived_validation_digest"] == first_digest
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert first_payload["rows"][0]["public_status"] == "watch"
    assert first_payload["rows"][0]["composite_memory_score"] == "0.715000"

    public = repr(first_payload).lower()
    for token in (
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "http",
        "source_text",
        "source_id",
        "source_reference",
        "raw_",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "trading",
        "size",
        "position",
        "buy",
        "sell",
        "recommend",
    ):
        assert token not in public
    assert_no_float_values(first_payload)

    tampered = asdict(first)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.ResearchDomainBaseballSignalMemoryQualityReport(**tampered)


def test_validates_types_statuses_flags_and_freezing() -> None:
    module = api()

    with pytest.raises(TypeError, match="Decimal"):
        input_row(pitcher_memory_score=0.9)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="datetime"):
        report((input_row(),), generated_at="2026-07-08T18:00:00Z")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="UTC-aware"):
        report((input_row(),), generated_at=datetime(2026, 7, 8, 18, 0))

    with pytest.raises(ValueError, match="whole second"):
        report((input_row(),), generated_at=datetime(2026, 7, 8, 18, 0, 0, 1, tzinfo=UTC))

    with pytest.raises(TypeError, match="exactly"):
        input_row(event_bucket=_StringSubclass("alpha_ready"))

    with pytest.raises(TypeError, match="exactly"):
        input_row(weather_memory_score=_DecimalSubclass("0.900000"))

    with pytest.raises(ValueError, match="unit interval"):
        input_row(lineup_memory_score=d("1.000001"))

    with pytest.raises(ValueError, match="nonnegative"):
        input_row(schedule_conflict_count=d("-1.000000"))

    with pytest.raises(ValueError, match="whole"):
        input_row(pitcher_conflict_count=d("1.500000"))

    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        input_row(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        input_row(readonly=False)

    with pytest.raises(TypeError, match="Decimal"):
        module.ResearchDomainBaseballSignalMemoryQualityConfig(
            pass_memory_score=1,  # type: ignore[arg-type]
        )

    frozen = input_row()
    with pytest.raises(FrozenInstanceError):
        frozen.pitcher_memory_score = d("0.100000")  # type: ignore[misc]

    summary = report((input_row(),))
    with pytest.raises(FrozenInstanceError):
        summary.report_status = "pass"  # type: ignore[misc]

    assert replace(frozen, pitcher_memory_score=d("0.880000")).pitcher_memory_score == (
        d("0.880000")
    )
    assert {summary.report_status, *(row.public_status for row in summary.rows)} <= {
        "pass",
        "watch",
        "block",
    }
    for obj in (summary, *summary.rows, *summary.reason_code_counts):
        for field in fields(obj):
            if field.name.endswith("status"):
                assert getattr(obj, field.name) in {"pass", "watch", "block"}


def test_public_inputs_reject_private_and_actionable_surfaces() -> None:
    leak_values = (
        _join_parts("raw_", "candidate", "_17"),
        _join_parts("market", "_slug"),
        _join_parts("will", "_team", "_win", "_question"),
        _join_parts("https", "://example.test/path"),
        _join_parts("source", "_text"),
        _join_parts("dsn", "_analytics"),
        _join_parts("table", "_name"),
        _join_parts("to", "ken", "_abc"),
        _join_parts("wal", "let", "_field"),
        _join_parts("sub", "mit", "_order"),
        _join_parts("trade", "_surface"),
        _join_parts("size", "_edge"),
        _join_parts("rec", "ommend", "_yes"),
    )

    for value in leak_values:
        with pytest.raises(ValueError, match="public"):
            input_row(memory_scope=value)


def test_module_is_pure_report_only_and_has_no_io_or_action_surface() -> None:
    module = api()
    module_source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(module_source)

    forbidden_import_roots = {
        "builtins",
        "io",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "sys",
        "urllib",
    }
    forbidden_calls = {
        "connect",
        "delete",
        "cursor",
        "execute",
        "open",
        "post",
        "put",
        "read_text",
        "send",
        "submit",
        "write_text",
    }
    forbidden_terms = (
        _join_parts("wal", "let"),
        _join_parts("au", "th"),
        _join_parts("order"),
        _join_parts("trade"),
        _join_parts("trading"),
        _join_parts("position"),
        _join_parts("buy"),
        _join_parts("sell"),
        _join_parts("rec", "ommend"),
    )

    imported_roots: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.add(func.id)
            elif isinstance(func, ast.Attribute):
                calls.add(func.attr)

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert calls.isdisjoint(forbidden_calls)
    assert not any(term in module_source.lower() for term in forbidden_terms)

    for cls_name in (
        "ResearchDomainBaseballSignalMemoryQualityConfig",
        "ResearchDomainBaseballSignalMemoryQualityInputRow",
        "ResearchDomainBaseballSignalMemoryQualityReasonCodeCount",
        "ResearchDomainBaseballSignalMemoryQualityReport",
        "ResearchDomainBaseballSignalMemoryQualityReportRow",
    ):
        cls = getattr(module, cls_name)
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
