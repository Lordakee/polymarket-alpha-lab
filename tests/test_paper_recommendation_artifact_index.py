import ast
import inspect
from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta, timezone

import pytest

from polymarket_alpha_lab.paper_recommendation_artifact_index import (
    PaperRecommendationArtifactIndexReport,
    PaperRecommendationArtifactIndexRow,
    build_paper_recommendation_artifact_index_report,
)


GENERATED_AT = datetime(2026, 6, 19, 15, 30, tzinfo=UTC)
CONFIG_VERSION = "paper-recommendation-artifact-index-v0"


@dataclass(frozen=True)
class FakeArtifact:
    artifact_name: str
    config_version: str = "artifact-v0"
    generated_at: datetime = GENERATED_AT
    final_status: str | None = None
    pipeline_status: str | None = None
    manifest_status: str | None = None
    health_status: str | None = None
    readiness_status: str | None = None
    consistency_status: str | None = None
    fee_schedule_status: str | None = None
    status: str | None = None
    row_count: int | None = None
    stage_count: int | None = None
    artifact_count: int | None = None
    item_count: int | None = None
    reason_codes: tuple[str, ...] = ()
    flags: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def _artifact(name: str, **overrides: object) -> FakeArtifact:
    values = {"artifact_name": name}
    values.update(overrides)
    return FakeArtifact(**values)


def _index(*artifacts: FakeArtifact) -> PaperRecommendationArtifactIndexReport:
    return build_paper_recommendation_artifact_index_report(
        generated_at=GENERATED_AT,
        config_version=CONFIG_VERSION,
        artifacts=artifacts,
    )


def test_paper_recommendation_artifact_index_indexes_statuses_counts_and_flags():
    report = _index(
        _artifact(
            "Zeta Pipeline",
            config_version="zeta-v1",
            pipeline_status="healthy",
            stage_count=3,
            reason_codes=("pipeline_ready",),
            flags=("pipeline_manifest",),
        ),
        _artifact(
            "alpha report",
            config_version="alpha-v1",
            final_status="fail",
            row_count=2,
            reason_codes=("missing_cost_floor",),
        ),
        _artifact(
            "Beta Report",
            config_version="beta-v1",
            readiness_status="incomplete",
            artifact_count=4,
        ),
        _artifact(
            "gamma-report",
            config_version="gamma-v1",
            status="pass",
            item_count=5,
        ),
    )

    assert isinstance(report, PaperRecommendationArtifactIndexReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.row_count == 4
    assert report.pass_count == 2
    assert report.watch_count == 1
    assert report.blocked_count == 1
    assert report.index_status == "blocked"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.flags == ("paper_only", "report_only", "readonly")

    assert tuple(row.artifact_name for row in report.rows) == (
        "alpha_report",
        "beta_report",
        "gamma_report",
        "zeta_pipeline",
    )
    assert report.rows == (
        PaperRecommendationArtifactIndexRow(
            artifact_name="alpha_report",
            config_version="alpha-v1",
            generated_at=GENERATED_AT,
            status="blocked",
            item_count=2,
            reason_codes=("missing_cost_floor",),
            flags=("paper_only", "report_only", "readonly"),
        ),
        PaperRecommendationArtifactIndexRow(
            artifact_name="beta_report",
            config_version="beta-v1",
            generated_at=GENERATED_AT,
            status="watch",
            item_count=4,
            reason_codes=(),
            flags=("paper_only", "report_only", "readonly"),
        ),
        PaperRecommendationArtifactIndexRow(
            artifact_name="gamma_report",
            config_version="gamma-v1",
            generated_at=GENERATED_AT,
            status="pass",
            item_count=5,
            reason_codes=(),
            flags=("paper_only", "report_only", "readonly"),
        ),
        PaperRecommendationArtifactIndexRow(
            artifact_name="zeta_pipeline",
            config_version="zeta-v1",
            generated_at=GENERATED_AT,
            status="pass",
            item_count=3,
            reason_codes=("pipeline_ready",),
            flags=("paper_only", "report_only", "readonly", "pipeline_manifest"),
        ),
    )


def test_paper_recommendation_artifact_index_rejects_duplicate_artifact_names():
    with pytest.raises(ValueError, match="duplicate artifact_name"):
        _index(
            _artifact("Alpha Report", final_status="pass"),
            _artifact("alpha_report", final_status="watch"),
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_paper_recommendation_artifact_index_rejects_unsafe_safety_flags(
    flag_name: str,
):
    artifact = _artifact("alpha", final_status="pass")
    object.__setattr__(artifact, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        _index(artifact)


def test_paper_recommendation_artifact_index_rejects_unsafe_source_flags():
    with pytest.raises(ValueError, match="unsafe flags"):
        _index(_artifact("alpha", final_status="pass", flags=("live_trading",)))


def test_paper_recommendation_artifact_index_rejects_generated_at_mismatch():
    with pytest.raises(ValueError, match="generated_at"):
        _index(
            _artifact(
                "alpha",
                final_status="pass",
                generated_at=GENERATED_AT + timedelta(minutes=1),
            ),
        )


def test_paper_recommendation_artifact_index_normalizes_report_time_to_utc():
    report = build_paper_recommendation_artifact_index_report(
        generated_at=datetime(2026, 6, 19, 8, 30, tzinfo=timezone(timedelta(hours=-7))),
        config_version=CONFIG_VERSION,
        artifacts=(
            _artifact(
                "alpha",
                final_status="pass",
                generated_at=GENERATED_AT,
            ),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].generated_at == GENERATED_AT


def test_paper_recommendation_artifact_index_dataclasses_are_frozen_and_revalidate():
    report = _index(_artifact("alpha", final_status="pass", item_count=1))
    row = report.rows[0]

    with pytest.raises(FrozenInstanceError):
        report.row_count = 99
    with pytest.raises(FrozenInstanceError):
        row.item_count = 99
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=2)
    with pytest.raises(ValueError, match="counts"):
        replace(report, pass_count=0)
    with pytest.raises(ValueError, match="status"):
        replace(row, status="live")
    with pytest.raises(ValueError, match="item_count"):
        replace(row, item_count=-1)


def test_paper_recommendation_artifact_index_has_no_live_auth_order_network_imports():
    from polymarket_alpha_lab import paper_recommendation_artifact_index as module

    tree = ast.parse(inspect.getsource(module))
    forbidden_import_roots = {
        "aiohttp",
        "eth_account",
        "httpx",
        "polymarket",
        "polymarket_clob_client",
        "py_clob_client",
        "requests",
        "web3",
        "websocket",
        "websockets",
    }
    imported_roots: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(
                alias.name.split(".", maxsplit=1)[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert called_names.isdisjoint(
        {
            "authenticate",
            "cancel_order",
            "create_order",
            "delete",
            "login",
            "patch",
            "post",
            "put",
            "request",
            "sign",
            "sign_message",
            "submit_order",
        },
    )
