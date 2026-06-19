import ast
from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_recommendation_cycle_bundle import (
    PaperRecommendationCycleBundleReport,
    build_paper_recommendation_cycle_bundle_report,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "paper_recommendation_cycle_bundle.py"
)
GENERATED_AT = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)


@dataclass(frozen=True)
class FakePipelineReport:
    generated_at: datetime = GENERATED_AT
    final_status: str = "pass"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class FakeGateSummaryReport:
    name: str = "gate_summary"
    generated_at: datetime = GENERATED_AT
    primary_status: str = "watch"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class NamedHealthShape:
    name: str
    status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class MultiStatusShape:
    final_status: str
    primary_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def _bundle(
    artifacts: tuple[object, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    config_version: str = "cycle-v1",
) -> PaperRecommendationCycleBundleReport:
    return build_paper_recommendation_cycle_bundle_report(
        generated_at=generated_at,
        config_version=config_version,
        artifacts=artifacts,
    )


def test_cycle_bundle_combines_frozen_reports_with_names_counts_status_and_utc():
    generated_at = datetime(2026, 6, 19, 5, 0, tzinfo=timezone(timedelta(hours=-7)))
    pipeline = FakePipelineReport(generated_at=generated_at)
    gate_summary = FakeGateSummaryReport(generated_at=GENERATED_AT)

    report = _bundle((pipeline, gate_summary), generated_at=generated_at)

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "cycle-v1"
    assert report.artifact_count == 2
    assert report.ready_artifact_count == 1
    assert report.blocked_artifact_count == 0
    assert report.final_status == "watch"
    assert report.artifact_names == ("FakePipelineReport", "gate_summary")
    assert report.artifacts == (pipeline, gate_summary)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    with pytest.raises(FrozenInstanceError):
        report.final_status = "blocked"  # type: ignore[misc]


def test_cycle_bundle_blocks_when_any_artifact_has_blocking_status():
    report = _bundle(
        (
            NamedHealthShape(name="health", status="unhealthy"),
            NamedHealthShape(name="allocation", status="pass"),
        ),
    )

    assert report.ready_artifact_count == 1
    assert report.blocked_artifact_count == 1
    assert report.final_status == "blocked"


def test_cycle_bundle_uses_most_severe_known_status_on_each_artifact():
    report = _bundle((MultiStatusShape(final_status="pass", primary_status="blocked"),))

    assert report.ready_artifact_count == 0
    assert report.blocked_artifact_count == 1
    assert report.final_status == "blocked"


def test_cycle_bundle_rejects_artifacts_without_hard_readonly_flags():
    valid = FakePipelineReport()

    with pytest.raises(ValueError, match="artifact FakePipelineReport must be paper_only"):
        _bundle((replace(valid, paper_only=False),))
    with pytest.raises(ValueError, match="artifact FakePipelineReport must be report_only"):
        _bundle((replace(valid, report_only=False),))
    with pytest.raises(ValueError, match="artifact FakePipelineReport must be readonly"):
        _bundle((replace(valid, readonly=False),))


def test_cycle_bundle_rejects_generated_at_mismatch_when_artifact_exposes_generated_at():
    stale = FakePipelineReport(generated_at=datetime(2026, 6, 19, 12, 1, tzinfo=UTC))

    with pytest.raises(ValueError, match="artifact FakePipelineReport generated_at"):
        _bundle((stale,))


def test_cycle_bundle_rejects_duplicate_artifact_names_from_name_attr_or_class_name():
    with pytest.raises(ValueError, match="artifact names must be unique"):
        _bundle(
            (
                NamedHealthShape(name="health", status="pass"),
                NamedHealthShape(name="health", status="watch"),
            ),
        )
    with pytest.raises(ValueError, match="artifact names must be unique"):
        _bundle((FakePipelineReport(), FakePipelineReport()))


def test_cycle_bundle_module_has_no_live_auth_order_or_network_imports():
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported_modules.append(node.module or "")

    assert set(imported_modules) <= {
        "__future__",
        "collections.abc",
        "dataclasses",
        "datetime",
    }
    for module in imported_modules:
        normalized = "".join(character for character in module.lower() if character.isalnum())
        for fragment in ("api", "auth", "wallet", "privatekey", "client", "network", "order"):
            assert fragment not in normalized, (module, fragment)
