from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_outcome_resolution_postmortem_learning_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 10, 30, tzinfo=timezone(timedelta(hours=2)))
RESOLVED_AT = datetime(2026, 7, 7, 22, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_outcome_resolution_postmortem_learning_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    report = api()
    values: dict[str, object] = {
        "config_version": "outcome-resolution-postmortem-learning-test-v0",
        "forecast_error_watch_threshold": d("0.100000"),
        "forecast_error_block_threshold": d("0.300000"),
        "evidence_miss_watch_threshold": d("0.100000"),
        "evidence_miss_block_threshold": d("0.250000"),
        "resolution_ambiguity_watch_threshold": d("0.150000"),
        "resolution_ambiguity_block_threshold": d("0.350000"),
        "cost_friction_miss_watch_threshold": d("0.080000"),
        "cost_friction_miss_block_threshold": d("0.200000"),
        "source_reliability_loss_watch_threshold": d("0.050000"),
        "source_reliability_loss_block_threshold": d("0.250000"),
    }
    values.update(overrides)
    return report.ResearchOutcomeResolutionPostmortemLearningConfig(**values)


def signal(**overrides: object):
    report = api()
    values: dict[str, object] = {
        "specialist_team_ref": "macro_team",
        "outcome_ref": "macro-fomc-resolution-market",
        "source_ref": "vendor-source-raw-link",
        "resolved_at": RESOLVED_AT,
        "aggregate_forecast_error": d("0.040000"),
        "evidence_miss_rate": d("0.030000"),
        "resolution_ambiguity_score": d("0.060000"),
        "cost_friction_miss": d("0.020000"),
        "source_reliability_delta": d("0.040000"),
    }
    values.update(overrides)
    return report.ResearchOutcomeResolutionPostmortemLearningSignal(**values)


def build_report(*signals: object, cfg=None, generated_at: datetime = GENERATED_AT):
    report = api()
    return report.build_research_outcome_resolution_postmortem_learning_report(
        signals,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_payload_numbers(value: Any) -> None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        raise AssertionError(f"unexpected JSON numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_payload_numbers(item)
    if isinstance(value, list):
        for item in value:
            assert_no_payload_numbers(item)


def assert_not_in_payload(value: Any, forbidden: str) -> None:
    if isinstance(value, str):
        assert forbidden not in value
    elif isinstance(value, dict):
        for item in value.values():
            assert_not_in_payload(item, forbidden)
    elif isinstance(value, list):
        for item in value:
            assert_not_in_payload(item, forbidden)


def test_postmortem_learning_report_summarizes_resolution_learning_signals() -> None:
    report = api()
    learning_report = build_report(
        signal(
            specialist_team_ref="sports_team",
            outcome_ref="sports-raw-market-slug-42",
            source_ref="https://raw.example/source/sports/42",
            aggregate_forecast_error=d("0.420000"),
            evidence_miss_rate=d("0.350000"),
            resolution_ambiguity_score=d("0.200000"),
            cost_friction_miss=d("0.270000"),
            source_reliability_delta=d("-0.310000"),
        ),
        signal(
            specialist_team_ref="macro_team",
            outcome_ref="macro-raw-market-slug-17",
            source_ref="private-source-feed-macro-17",
            aggregate_forecast_error=d("0.180000"),
            evidence_miss_rate=d("0.120000"),
            resolution_ambiguity_score=d("0.300000"),
            cost_friction_miss=d("0.070000"),
            source_reliability_delta=d("-0.110000"),
        ),
        signal(
            specialist_team_ref="crypto_team",
            outcome_ref="crypto-raw-market-slug-03",
            source_ref="exchange-flow-source-03",
            aggregate_forecast_error=d("0.040000"),
            evidence_miss_rate=d("0.030000"),
            resolution_ambiguity_score=d("0.060000"),
            cost_friction_miss=d("0.020000"),
            source_reliability_delta=d("0.040000"),
        ),
    )

    assert is_dataclass(learning_report)
    assert learning_report.generated_at == datetime(2026, 7, 8, 8, 30, tzinfo=UTC)
    assert learning_report.config_version == "outcome-resolution-postmortem-learning-test-v0"
    assert learning_report.source_signal_count == d("3")
    assert learning_report.learning_row_count == d("3")
    assert learning_report.pass_count == d("1")
    assert learning_report.watch_count == d("1")
    assert learning_report.block_count == d("1")
    assert learning_report.average_forecast_error == d("0.213333")
    assert learning_report.average_evidence_miss_rate == d("0.166667")
    assert learning_report.average_resolution_ambiguity_score == d("0.186667")
    assert learning_report.average_cost_friction_miss == d("0.120000")
    assert learning_report.average_source_reliability_delta == d("-0.126667")
    assert learning_report.max_learning_pressure_score == d("0.310000")
    assert learning_report.report_status == "block"
    assert learning_report.reason_codes == (
        "outcome_resolution_postmortem_forecast_error_block",
        "outcome_resolution_postmortem_evidence_miss_block",
        "outcome_resolution_postmortem_cost_friction_miss_block",
        "outcome_resolution_postmortem_source_reliability_delta_block",
        "outcome_resolution_postmortem_forecast_error_watch",
        "outcome_resolution_postmortem_evidence_miss_watch",
        "outcome_resolution_postmortem_resolution_ambiguity_watch",
        "outcome_resolution_postmortem_source_reliability_delta_watch",
    )
    assert learning_report.paper_only is True
    assert learning_report.report_only is True
    assert learning_report.readonly is True
    assert learning_report.validation_digest.startswith("rorplr-v1:")

    assert tuple(row.learning_status for row in learning_report.learning_rows) == (
        "block",
        "watch",
        "pass",
    )
    blocked, watched, passed = learning_report.learning_rows
    assert blocked.redacted_team_ref == "<redacted-team-003>"
    assert blocked.redacted_outcome_ref == "<redacted-outcome-003>"
    assert blocked.learning_pressure_score == d("0.310000")
    assert blocked.reason_codes == (
        "outcome_resolution_postmortem_forecast_error_block",
        "outcome_resolution_postmortem_evidence_miss_block",
        "outcome_resolution_postmortem_cost_friction_miss_block",
        "outcome_resolution_postmortem_source_reliability_delta_block",
    )
    assert watched.learning_pressure_score == d("0.156000")
    assert watched.reason_codes == (
        "outcome_resolution_postmortem_forecast_error_watch",
        "outcome_resolution_postmortem_evidence_miss_watch",
        "outcome_resolution_postmortem_resolution_ambiguity_watch",
        "outcome_resolution_postmortem_source_reliability_delta_watch",
    )
    assert passed.learning_pressure_score == d("0.030000")
    assert passed.reason_codes == ("outcome_resolution_postmortem_passed",)

    payload = report.research_outcome_resolution_postmortem_learning_report_payload(
        learning_report,
    )
    assert_not_in_payload(payload, "sports-raw-market-slug-42")
    assert_not_in_payload(payload, "raw.example")
    assert_not_in_payload(payload, "vendor-source-raw-link")


def test_empty_postmortem_learning_report_is_watch_and_readonly() -> None:
    empty = build_report()

    assert empty.source_signal_count == d("0")
    assert empty.learning_row_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.block_count == d("0")
    assert empty.average_forecast_error == d("0.000000")
    assert empty.average_evidence_miss_rate == d("0.000000")
    assert empty.average_resolution_ambiguity_score == d("0.000000")
    assert empty.average_cost_friction_miss == d("0.000000")
    assert empty.average_source_reliability_delta == d("0.000000")
    assert empty.max_learning_pressure_score == d("0.000000")
    assert empty.report_status == "watch"
    assert empty.learning_rows == ()
    assert empty.reason_codes == ("outcome_resolution_postmortem_empty",)
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def test_postmortem_learning_payload_uses_decimal_strings_and_stable_digest() -> None:
    report = api()
    learning_report = build_report(
        signal(
            specialist_team_ref="sports_team",
            outcome_ref="sports-raw-market-slug-42",
            source_ref="https://raw.example/source/sports/42",
            aggregate_forecast_error=d("0.420000"),
            evidence_miss_rate=d("0.350000"),
            resolution_ambiguity_score=d("0.200000"),
            cost_friction_miss=d("0.270000"),
            source_reliability_delta=d("-0.310000"),
        ),
    )
    rebuilt = build_report(
        signal(
            specialist_team_ref="sports_team",
            outcome_ref="sports-raw-market-slug-42",
            source_ref="https://raw.example/source/sports/42",
            aggregate_forecast_error=d("0.420000"),
            evidence_miss_rate=d("0.350000"),
            resolution_ambiguity_score=d("0.200000"),
            cost_friction_miss=d("0.270000"),
            source_reliability_delta=d("-0.310000"),
        ),
    )

    payload = report.research_outcome_resolution_postmortem_learning_report_payload(
        learning_report,
    )
    rebuilt_payload = report.research_outcome_resolution_postmortem_learning_report_payload(
        rebuilt,
    )

    assert payload == rebuilt_payload
    assert learning_report.validation_digest == rebuilt.validation_digest
    assert payload["generated_at"] == "2026-07-08T08:30:00+00:00"
    assert payload["source_signal_count"] == "1"
    assert payload["average_forecast_error"] == "0.420000"
    assert payload["learning_rows"][0]["aggregate_forecast_error"] == "0.420000"
    assert payload["learning_rows"][0]["learning_rank"] == "1"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_payload_numbers(payload)


def test_postmortem_learning_validation_rejects_bad_types_flags_and_leaks() -> None:
    report = api()

    with pytest.raises(ValueError, match="config"):
        report.build_research_outcome_resolution_postmortem_learning_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="aggregate_forecast_error must be a Decimal"):
        signal(aggregate_forecast_error=1)
    with pytest.raises(ValueError, match="evidence_miss_rate must be a Decimal"):
        signal(evidence_miss_rate=0.2)
    with pytest.raises(ValueError, match="source_reliability_delta must be a Decimal"):
        signal(source_reliability_delta=_DecimalSubclass("-0.100000"))
    with pytest.raises(ValueError, match="resolved_at must be timezone-aware"):
        signal(resolved_at=datetime(2026, 7, 7, 22, 0))
    with pytest.raises(ValueError, match="resolved_at must be timezone-aware"):
        signal(resolved_at=datetime(2026, 7, 7, 22, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_report(
            signal(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 8, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(signal(), readonly=False)
    with pytest.raises(ValueError, match="team outcome pairs"):
        build_report(signal(), signal())
    with pytest.raises(ValueError, match="resolved_at must not be after generated_at"):
        build_report(signal(resolved_at=GENERATED_AT + timedelta(seconds=1)))

    learning_report = build_report(signal())
    with pytest.raises(ValueError, match="source_signal_count"):
        replace(learning_report, source_signal_count=d("2"))
    with pytest.raises(ValueError, match="learning_status"):
        replace(learning_report.learning_rows[0], learning_status="alert")
    with pytest.raises(ValueError, match="validation_digest"):
        replace(learning_report, validation_digest="rorplr-v1:" + "0" * 64)
    with pytest.raises(ValueError, match="unsafe public payload"):
        report.research_outcome_resolution_postmortem_learning_report_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "market_id": "raw"},
        )
    with pytest.raises(FrozenInstanceError):
        learning_report.learning_rows[0].learning_status = "watch"  # type: ignore[misc]


def test_postmortem_learning_public_types_are_frozen_and_decimal_only() -> None:
    report = api()
    learning_report = build_report(signal())
    values = (
        config(),
        signal(),
        learning_report.learning_rows[0],
        learning_report,
    )
    numeric_suffixes = (
        "_count",
        "_delta",
        "_error",
        "_miss",
        "_rate",
        "_score",
        "_threshold",
        "_rank",
    )

    assert report.__all__ == (
        "DEFAULT_RESEARCH_OUTCOME_RESOLUTION_POSTMORTEM_LEARNING_CONFIG_VERSION",
        "OUTCOME_RESOLUTION_POSTMORTEM_LEARNING_STATUSES",
        "ResearchOutcomeResolutionPostmortemLearningConfig",
        "ResearchOutcomeResolutionPostmortemLearningReport",
        "ResearchOutcomeResolutionPostmortemLearningRow",
        "ResearchOutcomeResolutionPostmortemLearningSignal",
        "build_research_outcome_resolution_postmortem_learning_report",
        "research_outcome_resolution_postmortem_learning_report_payload",
    )
    assert report.OUTCOME_RESOLUTION_POSTMORTEM_LEARNING_STATUSES == (
        "pass",
        "watch",
        "block",
    )

    for exported_name in report.__all__:
        exported = getattr(report, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True

    for value in values:
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        for field in fields(value):
            if field.name.endswith(numeric_suffixes):
                assert type(getattr(value, field.name)) is Decimal

    for dataclass_type in (
        report.ResearchOutcomeResolutionPostmortemLearningConfig,
        report.ResearchOutcomeResolutionPostmortemLearningReport,
        report.ResearchOutcomeResolutionPostmortemLearningRow,
        report.ResearchOutcomeResolutionPostmortemLearningSignal,
    ):
        hints = get_type_hints(dataclass_type)
        for field in fields(dataclass_type):
            if field.name.endswith(numeric_suffixes):
                assert hints[field.name] is Decimal


def test_postmortem_learning_module_scope_stays_pure_public_report_only() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live_trading",
        "wallet",
        "account",
        "broker",
        "cancel",
        "network",
        "database",
        "durable",
        "store",
        "payload_json",
        "private_key",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "psycopg",
        "sqlite",
        "supabase",
        "execute(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "os",
        "pathlib",
        "requests",
        "socket",
        "subprocess",
        "urllib",
    }
    forbidden_call_names = {
        "__import__",
        "connect",
        "eval",
        "exec",
        "executemany",
        "float",
        "open",
        "print",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
