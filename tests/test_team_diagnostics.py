from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
EXPECTED_EXPORTS = (
    "TeamDiagnosticsConfig",
    "TeamDiagnosticsReport",
    "TeamDiagnosticsRow",
    "build_team_diagnostics_report",
)
FORBIDDEN_IMPORT_PREFIXES = {
    "argparse",
    "os",
    "psycopg",
    "sqlite3",
    "sqlalchemy",
    "redis",
    "pymongo",
    "web3",
    "eth_account",
    "py_clob_client",
}


class _FakeBundleReport:
    paper_only = True
    report_only = True
    readonly = True

    def __init__(self) -> None:
        self.generated_at = GENERATED_AT
        self.config_version = "team-diagnostics-bundle-test-v0"
        self.forecast_row_count = 2
        self.evidence_row_count = 3
        self.outcome_row_count = 1
        self.memory_synthesis_report = _FakeNestedReport(
            "memory_synthesis",
            forecast_row_count=2,
            evidence_row_count=3,
            outcome_row_count=1,
            reference_count=4,
        )
        self.forecast_calibration_report = _FakeNestedReport(
            "forecast_calibration",
            forecast_count=2,
            settled_count=1,
            status="watch",
        )
        self.event_template_performance_report = _FakeNestedReport(
            "event_template_performance",
            row_count=1,
            status="pass",
        )
        self.source_reliability_report = _FakeNestedReport(
            "source_reliability",
            row_count=2,
            status="watch",
        )
        self.evidence_quality_report = _FakeNestedReport(
            "evidence_quality",
            total_count=3,
            pass_count=2,
            watch_count=1,
            blocked_count=0,
        )


class _FakeNestedReport:
    paper_only = True
    report_only = True
    readonly = True

    def __init__(self, config_version: str, **values: object) -> None:
        self.generated_at = GENERATED_AT
        self.config_version = config_version
        for key, value in values.items():
            setattr(self, key, value)


def _module() -> Any:
    return importlib.import_module("polymarket_alpha_lab.team_diagnostics")


def _assert_no_float_values(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("team diagnostics facade must not expose float values")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _assert_no_float_values(getattr(value, field.name))
    elif isinstance(value, dict):
        for key, item in value.items():
            _assert_no_float_values(key)
            _assert_no_float_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_float_values(item)


def test_public_exports_are_exact_and_dataclasses_are_frozen() -> None:
    module = _module()

    assert module.__all__ == EXPECTED_EXPORTS

    config = module.TeamDiagnosticsConfig()
    row = module.TeamDiagnosticsRow("bundle", "forecast_row_count", "0")
    report = module.TeamDiagnosticsReport(
        generated_at=GENERATED_AT,
        config_version=config.config_version,
        rows=(row,),
        row_count=1,
    )

    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    with pytest.raises(FrozenInstanceError):
        config.config_version = "mutated"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.value = "mutated"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.row_count = 2  # type: ignore[misc]


def test_build_report_handles_empty_inputs_without_bundle_rows() -> None:
    module = _module()
    generated_at = datetime(2026, 7, 1, 8, 0, tzinfo=timezone(timedelta(hours=-4)))

    report = module.build_team_diagnostics_report(
        [],
        (),
        [],
        config=module.TeamDiagnosticsConfig(config_version="team-diagnostics-test-v0"),
        generated_at=generated_at,
        bundle_builder=lambda *args, **kwargs: None,
    )

    assert type(report) is module.TeamDiagnosticsReport
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "team-diagnostics-test-v0"
    assert report.row_count == 3
    assert report.rows == (
        module.TeamDiagnosticsRow("input", "forecast_row_count", "0"),
        module.TeamDiagnosticsRow("input", "evidence_row_count", "0"),
        module.TeamDiagnosticsRow("input", "outcome_row_count", "0"),
    )
    assert report.bundle_report is None
    _assert_no_float_values(report)


def test_build_report_delegates_to_stub_bundle_builder_and_flattens_rows() -> None:
    module = _module()
    calls: list[dict[str, object]] = []
    forecasts = (object(), object())
    evidence = (object(), object(), object())
    outcomes = (object(),)
    expected_bundle = _FakeBundleReport()

    def fake_bundle_builder(
        received_forecasts: object,
        received_evidence: object,
        received_outcomes: object,
        *,
        generated_at: datetime,
    ) -> _FakeBundleReport:
        calls.append(
            {
                "forecasts": received_forecasts,
                "evidence": received_evidence,
                "outcomes": received_outcomes,
                "generated_at": generated_at,
            },
        )
        return expected_bundle

    report = module.build_team_diagnostics_report(
        forecasts,
        evidence,
        outcomes,
        config=module.TeamDiagnosticsConfig(config_version="team-diagnostics-test-v0"),
        generated_at=GENERATED_AT,
        bundle_builder=fake_bundle_builder,
    )

    assert calls == [
        {
            "forecasts": forecasts,
            "evidence": evidence,
            "outcomes": outcomes,
            "generated_at": GENERATED_AT,
        },
    ]
    assert report.bundle_report is expected_bundle
    assert report.row_count == len(report.rows)
    assert report.rows == (
        module.TeamDiagnosticsRow("input", "forecast_row_count", "2"),
        module.TeamDiagnosticsRow("input", "evidence_row_count", "3"),
        module.TeamDiagnosticsRow("input", "outcome_row_count", "1"),
        module.TeamDiagnosticsRow("bundle", "config_version", "team-diagnostics-bundle-test-v0"),
        module.TeamDiagnosticsRow("bundle", "forecast_row_count", "2"),
        module.TeamDiagnosticsRow("bundle", "evidence_row_count", "3"),
        module.TeamDiagnosticsRow("bundle", "outcome_row_count", "1"),
        module.TeamDiagnosticsRow("memory_synthesis", "config_version", "memory_synthesis"),
        module.TeamDiagnosticsRow("memory_synthesis", "forecast_row_count", "2"),
        module.TeamDiagnosticsRow("memory_synthesis", "evidence_row_count", "3"),
        module.TeamDiagnosticsRow("memory_synthesis", "outcome_row_count", "1"),
        module.TeamDiagnosticsRow("memory_synthesis", "reference_count", "4"),
        module.TeamDiagnosticsRow(
            "forecast_calibration",
            "config_version",
            "forecast_calibration",
        ),
        module.TeamDiagnosticsRow("forecast_calibration", "forecast_count", "2"),
        module.TeamDiagnosticsRow("forecast_calibration", "settled_count", "1"),
        module.TeamDiagnosticsRow("forecast_calibration", "status", "watch"),
        module.TeamDiagnosticsRow(
            "event_template_performance",
            "config_version",
            "event_template_performance",
        ),
        module.TeamDiagnosticsRow("event_template_performance", "row_count", "1"),
        module.TeamDiagnosticsRow("event_template_performance", "status", "pass"),
        module.TeamDiagnosticsRow(
            "source_reliability",
            "config_version",
            "source_reliability",
        ),
        module.TeamDiagnosticsRow("source_reliability", "row_count", "2"),
        module.TeamDiagnosticsRow("source_reliability", "status", "watch"),
        module.TeamDiagnosticsRow("evidence_quality", "config_version", "evidence_quality"),
        module.TeamDiagnosticsRow("evidence_quality", "total_count", "3"),
        module.TeamDiagnosticsRow("evidence_quality", "pass_count", "2"),
        module.TeamDiagnosticsRow("evidence_quality", "watch_count", "1"),
        module.TeamDiagnosticsRow("evidence_quality", "blocked_count", "0"),
    )
    _assert_no_float_values(report)


def test_config_report_and_rows_validate_canonical_metadata_and_flags() -> None:
    module = _module()

    with pytest.raises(ValueError, match="config_version"):
        module.TeamDiagnosticsConfig(config_version=" team-diagnostics-test-v0 ")
    with pytest.raises(ValueError, match="paper_only"):
        module.TeamDiagnosticsConfig(paper_only=False)
    with pytest.raises(ValueError, match="section"):
        module.TeamDiagnosticsRow(" input ", "forecast_row_count", "0")
    with pytest.raises(ValueError, match="label"):
        module.TeamDiagnosticsRow("input", "", "0")
    with pytest.raises(ValueError, match="value"):
        module.TeamDiagnosticsRow("input", "forecast_row_count", 0)
    with pytest.raises(ValueError, match="generated_at"):
        module.build_team_diagnostics_report(
            [],
            [],
            [],
            config=module.TeamDiagnosticsConfig(),
            generated_at="2026-07-01T12:00:00Z",
            bundle_builder=None,
        )
    with pytest.raises(ValueError, match="row_count"):
        module.TeamDiagnosticsReport(
            generated_at=GENERATED_AT,
            config_version="team-diagnostics-test-v0",
            rows=(),
            row_count=1,
        )
    with pytest.raises(ValueError, match="readonly"):
        module.TeamDiagnosticsReport(
            generated_at=GENERATED_AT,
            config_version="team-diagnostics-test-v0",
            rows=(),
            row_count=0,
            readonly=False,
        )


def test_forbidden_imports_are_not_used_by_facade_module() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "team_diagnostics.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)

    assert not {
        module_name
        for module_name in imported
        for prefix in FORBIDDEN_IMPORT_PREFIXES
        if module_name == prefix or module_name.startswith(f"{prefix}.")
    }
