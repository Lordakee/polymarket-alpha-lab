from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_recommendation_artifact_index import (
    build_paper_recommendation_artifact_index_report,
)
from polymarket_alpha_lab.paper_recommendation_cycle_snapshot import (
    PaperRecommendationCycleSnapshotReport,
    build_paper_recommendation_cycle_snapshot_report,
)
from polymarket_alpha_lab.paper_recommendation_cycle_snapshot_log import (
    _json_ready,
    append_paper_recommendation_cycle_snapshot_log,
    read_paper_recommendation_cycle_snapshot_log,
)
from polymarket_alpha_lab.paper_recommendation_pipeline import (
    PaperRecommendationPipelineStage,
    build_paper_recommendation_pipeline_report,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "paper_recommendation_cycle_snapshot_log.py"
)
GENERATED_AT = datetime(2026, 6, 19, 17, 45, tzinfo=UTC)
CONFIG_VERSION = "paper-recommendation-cycle-snapshot-v0"


class PaperRecommendationCycleSnapshotReportSubclass(
    PaperRecommendationCycleSnapshotReport,
):
    pass


@dataclass(frozen=True)
class FakeArtifact:
    artifact_name: str
    status: str
    item_count: int
    reason_codes: tuple[str, ...] = ()
    generated_at: datetime = GENERATED_AT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class DecimalSummary:
    generated_at: datetime
    ratio: Decimal
    quantiles: tuple[Decimal, Decimal]


def _stage(stage_name: str, status: str) -> PaperRecommendationPipelineStage:
    return PaperRecommendationPipelineStage(
        stage_name=stage_name,
        status=status,
        message=f"{stage_name} {status}",
        input_count=1,
        output_count=1,
    )


def _snapshot(
    *,
    generated_at: datetime = GENERATED_AT,
    artifact_name: str = "alpha",
    artifact_status: str = "pass",
    stage_status: str = "pass",
) -> PaperRecommendationCycleSnapshotReport:
    pipeline_report = build_paper_recommendation_pipeline_report(
        generated_at=generated_at,
        config_version="paper-recommendation-pipeline-v0",
        stages=(_stage("stage_1", stage_status),),
    )
    artifact_index_report = build_paper_recommendation_artifact_index_report(
        generated_at=generated_at,
        config_version="paper-recommendation-artifact-index-v0",
        artifacts=(
            FakeArtifact(
                artifact_name=artifact_name,
                status=artifact_status,
                item_count=1,
                generated_at=generated_at,
            ),
        ),
    )
    return build_paper_recommendation_cycle_snapshot_report(
        generated_at=generated_at,
        config_version=CONFIG_VERSION,
        pipeline_report=pipeline_report,
        artifact_index_report=artifact_index_report,
    )


def _assert_contains_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("cycle snapshot JSONL payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_contains_no_floats(item)
    elif isinstance(value, list):
        for item in value:
            _assert_contains_no_floats(item)


def test_cycle_snapshot_log_appends_and_round_trips_one_record(tmp_path):
    path = tmp_path / "nested" / "cycle-snapshot.jsonl"
    report = _snapshot(
        generated_at=datetime(
            2026,
            6,
            19,
            10,
            45,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )

    append_paper_recommendation_cycle_snapshot_log(path, report)

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["generated_at"] == "2026-06-19T17:45:00+00:00"
    assert payload["config_version"] == CONFIG_VERSION
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["pipeline_report"]["readonly"] is True
    assert payload["artifact_index_report"]["readonly"] is True
    _assert_contains_no_floats(payload)

    recovered = read_paper_recommendation_cycle_snapshot_log(path)
    assert recovered == (report,)
    assert type(recovered[0]) is PaperRecommendationCycleSnapshotReport


def test_cycle_snapshot_log_appends_two_records_and_skips_blank_lines(tmp_path):
    path = tmp_path / "cycle-snapshot.jsonl"
    first = _snapshot(artifact_name="alpha")
    second = _snapshot(artifact_name="beta", artifact_status="watch")

    append_paper_recommendation_cycle_snapshot_log(path, first)
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n")
    append_paper_recommendation_cycle_snapshot_log(path, second)

    assert read_paper_recommendation_cycle_snapshot_log(path) == (first, second)


def test_cycle_snapshot_log_append_does_not_read_existing_file(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
):
    path = tmp_path / "cycle-snapshot.jsonl"
    path.write_text("existing\n", encoding="utf-8")
    original_read_text = Path.read_text

    def fail_read_text(self: Path, *args: object, **kwargs: object) -> str:
        if self == path:
            raise AssertionError("append must not read existing JSONL content")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fail_read_text)

    append_paper_recommendation_cycle_snapshot_log(path, _snapshot())

    with path.open("r", encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    assert lines[0] == "existing"
    assert json.loads(lines[1])["config_version"] == CONFIG_VERSION


def test_cycle_snapshot_log_json_ready_decimal_strings_and_rejects_floats():
    payload = _json_ready(
        DecimalSummary(
            generated_at=GENERATED_AT,
            ratio=Decimal("0.750000"),
            quantiles=(Decimal("0.100000"), Decimal("0.900000")),
        ),
    )

    assert payload == {
        "generated_at": "2026-06-19T17:45:00+00:00",
        "ratio": "0.750000",
        "quantiles": ["0.100000", "0.900000"],
    }
    _assert_contains_no_floats(payload)
    with pytest.raises(ValueError, match="float"):
        _json_ready({"ratio": 0.75})


def test_cycle_snapshot_log_invalid_json_reports_line_number(tmp_path):
    path = tmp_path / "cycle-snapshot.jsonl"
    append_paper_recommendation_cycle_snapshot_log(path, _snapshot())
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n")
        handle.write("not json\n")

    with pytest.raises(
        ValueError,
        match="paper recommendation cycle snapshot log line 3 is not valid JSON",
    ):
        read_paper_recommendation_cycle_snapshot_log(path)


def test_cycle_snapshot_log_malformed_report_reports_line_number(tmp_path):
    path = tmp_path / "cycle-snapshot.jsonl"
    append_paper_recommendation_cycle_snapshot_log(path, _snapshot())
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n")
        handle.write(
            '{"paper_only": true, "report_only": true, "readonly": true}\n',
        )

    with pytest.raises(
        ValueError,
        match="paper recommendation cycle snapshot log line 3 is not a valid report",
    ):
        read_paper_recommendation_cycle_snapshot_log(path)


def test_cycle_snapshot_log_false_hard_flag_reports_line_number(tmp_path):
    path = tmp_path / "cycle-snapshot.jsonl"
    append_paper_recommendation_cycle_snapshot_log(path, _snapshot())
    payload = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    payload["readonly"] = False
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")

    with pytest.raises(
        ValueError,
        match="paper recommendation cycle snapshot log line 2 is not a valid report",
    ):
        read_paper_recommendation_cycle_snapshot_log(path)


def test_cycle_snapshot_log_false_nested_hard_flag_reports_line_number(tmp_path):
    path = tmp_path / "cycle-snapshot.jsonl"
    append_paper_recommendation_cycle_snapshot_log(path, _snapshot())
    payload = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    payload["pipeline_report"]["stages"][0]["readonly"] = False
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")

    with pytest.raises(
        ValueError,
        match="paper recommendation cycle snapshot log line 2 is not a valid report",
    ):
        read_paper_recommendation_cycle_snapshot_log(path)


def test_cycle_snapshot_log_numeric_float_reports_line_number(tmp_path):
    path = tmp_path / "cycle-snapshot.jsonl"
    append_paper_recommendation_cycle_snapshot_log(path, _snapshot())
    payload = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    payload["pipeline_report"]["stages"][0]["input_count"] = 1.5
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")

    with pytest.raises(
        ValueError,
        match="paper recommendation cycle snapshot log line 2 is not a valid report",
    ):
        read_paper_recommendation_cycle_snapshot_log(path)


def test_cycle_snapshot_log_rejects_wrong_report_type_without_writing(tmp_path):
    path = tmp_path / "cycle-snapshot.jsonl"

    with pytest.raises(ValueError, match="PaperRecommendationCycleSnapshotReport"):
        append_paper_recommendation_cycle_snapshot_log(path, object())

    assert not path.exists()


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_cycle_snapshot_log_rejects_false_top_level_flags_without_writing(
    tmp_path,
    flag_name,
):
    path = tmp_path / "cycle-snapshot.jsonl"
    report = _snapshot()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        append_paper_recommendation_cycle_snapshot_log(path, report)

    assert not path.exists()


def test_cycle_snapshot_log_rejects_false_nested_flags_without_writing(tmp_path):
    path = tmp_path / "cycle-snapshot.jsonl"
    report = _snapshot()
    object.__setattr__(report.pipeline_report.stages[0], "readonly", False)

    with pytest.raises(ValueError, match="pipeline_report.*stages.*readonly"):
        append_paper_recommendation_cycle_snapshot_log(path, report)

    assert not path.exists()


def test_cycle_snapshot_log_rejects_subclass_reports_without_writing(tmp_path):
    path = tmp_path / "cycle-snapshot.jsonl"
    report = _snapshot()
    subclass = PaperRecommendationCycleSnapshotReportSubclass(**report.__dict__)

    with pytest.raises(ValueError, match="PaperRecommendationCycleSnapshotReport"):
        append_paper_recommendation_cycle_snapshot_log(path, subclass)

    assert not path.exists()


def test_cycle_snapshot_log_path_validation_matches_recommendation_logs(tmp_path):
    report = _snapshot()
    existing_directory = tmp_path / "existing-directory"
    existing_directory.mkdir()
    parent_file = tmp_path / "parent-file"
    parent_file.write_text("not a directory", encoding="utf-8")

    with pytest.raises(ValueError, match="path is required"):
        append_paper_recommendation_cycle_snapshot_log("", report)
    with pytest.raises(ValueError, match="path must be path-like"):
        append_paper_recommendation_cycle_snapshot_log(object(), report)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="path must be a file path"):
        append_paper_recommendation_cycle_snapshot_log(existing_directory, report)
    with pytest.raises(ValueError, match="path parent must be a directory"):
        append_paper_recommendation_cycle_snapshot_log(parent_file / "log.jsonl", report)


def test_cycle_snapshot_log_module_has_no_live_auth_order_network_imports_or_calls():
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
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
