from __future__ import annotations

import ast
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import importlib
import importlib.util
from pathlib import Path
import sys
import types
from typing import Any

import pytest

from polymarket_alpha_lab.team_diagnostics_snapshot_history import (
    TeamDiagnosticsSnapshotHistoryConfig,
)
from polymarket_alpha_lab.team_diagnostics_snapshot_history_gate import (
    DEFAULT_TEAM_DIAGNOSTICS_SNAPSHOT_HISTORY_GATE_CONFIG_VERSION,
    TeamDiagnosticsSnapshotHistoryGateConfig,
    TeamDiagnosticsSnapshotHistoryGateReasonCodeCount,
    TeamDiagnosticsSnapshotHistoryGateReport,
)
from polymarket_alpha_lab.team_taxonomy import TEAM_IDS


MODULE_UNDER_TEST = "polymarket_alpha_lab.team_memory_readiness_digest_db_source"
DIGEST_CONTRACT_MODULE = "polymarket_alpha_lab.team_memory_readiness_digest"
GENERATED_AT = datetime(2026, 7, 1, 14, 0, tzinfo=UTC)


@dataclass(frozen=True)
class _DigestReport:
    digest_status: str = "pass"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class _DigestSource:
    team_id: str
    gate_report: object


_GATE_NEXT_STEPS = {
    "pass": "allow_team_diagnostics_snapshot_history_memory_use",
    "watch": "throttle_team_diagnostics_snapshot_history_memory_use",
    "blocked": "block_team_diagnostics_snapshot_history_memory_use",
}
_GATE_REASON_CODES = {
    "pass": "team_diagnostics_snapshot_history_gate_passed",
    "watch": "team_diagnostics_snapshot_history_evidence_quality_deteriorated",
    "blocked": "insufficient_team_diagnostics_snapshot_history_samples",
}


def _gate_report(
    gate_status: str = "pass",
    *,
    source_config_version: str = "source-history-v0",
    latest_snapshot_age_seconds: int | None = 60,
    source_snapshot_count: int = 3,
    source_required_snapshot_count: int = 3,
    source_status: str = "ready",
) -> TeamDiagnosticsSnapshotHistoryGateReport:
    source_generated_at = (
        None
        if latest_snapshot_age_seconds is None
        else GENERATED_AT - timedelta(seconds=latest_snapshot_age_seconds)
    )
    reason_code = _GATE_REASON_CODES[gate_status]
    return TeamDiagnosticsSnapshotHistoryGateReport(
        generated_at=GENERATED_AT,
        config_version=DEFAULT_TEAM_DIAGNOSTICS_SNAPSHOT_HISTORY_GATE_CONFIG_VERSION,
        source_config_version=source_config_version,
        source_generated_at=source_generated_at,
        latest_snapshot_age_seconds=latest_snapshot_age_seconds,
        gate_status=gate_status,
        recommended_next_step=_GATE_NEXT_STEPS[gate_status],
        reason_code_counts=(
            TeamDiagnosticsSnapshotHistoryGateReasonCodeCount(
                reason_code=reason_code,
                count=1,
            ),
        ),
        source_snapshot_count=source_snapshot_count,
        source_required_snapshot_count=source_required_snapshot_count,
        source_status=source_status,
        source_span_seconds=120,
        source_status_counts=((source_status, source_snapshot_count),),
        source_reason_codes=(),
        evidence_quality_average_delta=Decimal("0.000000"),
        memory_eligible_delta=0,
        settled_calibration_delta=0,
        duplicate_latest_generated_at=False,
        reason_codes=(reason_code,),
    )


def _digest_contract_types(monkeypatch: pytest.MonkeyPatch) -> tuple[type, type]:
    existing = sys.modules.get(DIGEST_CONTRACT_MODULE)
    if existing is None and importlib.util.find_spec(DIGEST_CONTRACT_MODULE) is not None:
        existing = importlib.import_module(DIGEST_CONTRACT_MODULE)

    digest_contract = existing or types.ModuleType(DIGEST_CONTRACT_MODULE)

    if not hasattr(digest_contract, "TeamMemoryReadinessDigestConfig"):

        @dataclass(frozen=True)
        class TeamMemoryReadinessDigestConfig:
            config_version: str = "team-memory-readiness-digest-v0"
            paper_only: bool = True
            report_only: bool = True
            readonly: bool = True

        digest_contract.TeamMemoryReadinessDigestConfig = TeamMemoryReadinessDigestConfig
    if not hasattr(digest_contract, "TeamMemoryReadinessDigestSource"):
        monkeypatch.setattr(
            digest_contract,
            "TeamMemoryReadinessDigestSource",
            _DigestSource,
            raising=False,
        )
    monkeypatch.setitem(sys.modules, DIGEST_CONTRACT_MODULE, digest_contract)
    return (
        digest_contract.TeamMemoryReadinessDigestConfig,  # type: ignore[attr-defined]
        digest_contract.TeamMemoryReadinessDigestSource,  # type: ignore[attr-defined]
    )


def _digest_config_type(monkeypatch: pytest.MonkeyPatch) -> type:
    return _digest_contract_types(monkeypatch)[0]


def _digest_source_type(monkeypatch: pytest.MonkeyPatch) -> type:
    return _digest_contract_types(monkeypatch)[1]


def _module_under_test(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    _digest_contract_types(monkeypatch)
    sys.modules.pop(MODULE_UNDER_TEST, None)
    try:
        return importlib.import_module(MODULE_UNDER_TEST)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_UNDER_TEST:
            pytest.fail(f"{MODULE_UNDER_TEST} does not exist")
        raise


def test_loads_each_team_gate_then_builds_digest_in_team_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _module_under_test(monkeypatch)
    digest_config = _digest_config_type(monkeypatch)()
    digest_source_type = _digest_source_type(monkeypatch)
    history_config = TeamDiagnosticsSnapshotHistoryConfig()
    gate_config = TeamDiagnosticsSnapshotHistoryGateConfig()
    digest_report = _DigestReport()
    loader_calls: list[dict[str, object]] = []
    builder_calls: list[tuple[tuple[object, ...], object, datetime]] = []
    gate_reports = {
        TEAM_IDS[1]: _gate_report(),
        TEAM_IDS[0]: _gate_report("watch"),
    }

    def gate_loader(**kwargs: object) -> TeamDiagnosticsSnapshotHistoryGateReport:
        loader_calls.append(kwargs)
        team_id = kwargs["team_id"]
        assert type(team_id) is str
        return gate_reports[team_id]

    def digest_builder(
        source_reports: object,
        *,
        config: object,
        generated_at: datetime,
    ) -> _DigestReport:
        sources = tuple(source_reports)  # type: ignore[arg-type]
        assert tuple(type(source) for source in sources) == (
            digest_source_type,
            digest_source_type,
        )
        assert tuple(source.team_id for source in sources) == (TEAM_IDS[1], TEAM_IDS[0])
        assert tuple(source.gate_report for source in sources) == (
            gate_reports[TEAM_IDS[1]],
            gate_reports[TEAM_IDS[0]],
        )
        builder_calls.append((sources, config, generated_at))
        return digest_report

    result = module.load_team_memory_readiness_digest_report(
        team_ids=(TEAM_IDS[1], TEAM_IDS[0]),
        gate_loader=gate_loader,
        digest_builder=digest_builder,
        digest_config=digest_config,
        history_config=history_config,
        gate_config=gate_config,
        generated_at=GENERATED_AT,
        config_version="snapshot-v1",
        limit=25,
    )

    assert result is digest_report
    assert loader_calls == [
        {
            "team_id": TEAM_IDS[1],
            "history_config": history_config,
            "gate_config": gate_config,
            "generated_at": GENERATED_AT,
            "config_version": "snapshot-v1",
            "limit": 25,
        },
        {
            "team_id": TEAM_IDS[0],
            "history_config": history_config,
            "gate_config": gate_config,
            "generated_at": GENERATED_AT,
            "config_version": "snapshot-v1",
            "limit": 25,
        },
    ]
    assert len(builder_calls) == 1
    source_tuple, builder_config, builder_generated_at = builder_calls[0]
    assert source_tuple == (
        digest_source_type(team_id=TEAM_IDS[1], gate_report=gate_reports[TEAM_IDS[1]]),
        digest_source_type(team_id=TEAM_IDS[0], gate_report=gate_reports[TEAM_IDS[0]]),
    )
    assert builder_config is digest_config
    assert builder_generated_at == GENERATED_AT
    assert "load_team_memory_readiness_digest_report" in module.__all__


def test_rejects_empty_duplicate_or_invalid_team_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _module_under_test(monkeypatch)
    digest_config = _digest_config_type(monkeypatch)()
    history_config = TeamDiagnosticsSnapshotHistoryConfig()
    gate_config = TeamDiagnosticsSnapshotHistoryGateConfig()
    calls: list[str] = []

    def gate_loader(**_: object) -> TeamDiagnosticsSnapshotHistoryGateReport:
        calls.append("gate_loader")
        return _gate_report()

    def digest_builder(
        source_reports: object,
        *,
        config: object,
        generated_at: datetime,
    ) -> _DigestReport:
        calls.append("digest_builder")
        return _DigestReport()

    base_kwargs = {
        "gate_loader": gate_loader,
        "digest_builder": digest_builder,
        "digest_config": digest_config,
        "history_config": history_config,
        "gate_config": gate_config,
        "generated_at": GENERATED_AT,
    }

    with pytest.raises(ValueError, match="team_ids"):
        module.load_team_memory_readiness_digest_report(team_ids=(), **base_kwargs)
    with pytest.raises(ValueError, match="team_ids"):
        module.load_team_memory_readiness_digest_report(
            team_ids=(TEAM_IDS[0], TEAM_IDS[0]),
            **base_kwargs,
        )
    with pytest.raises(ValueError, match="team_ids"):
        module.load_team_memory_readiness_digest_report(
            team_ids=(TEAM_IDS[0], " " + TEAM_IDS[1]),
            **base_kwargs,
        )
    with pytest.raises(ValueError, match="team_ids"):
        module.load_team_memory_readiness_digest_report(
            team_ids=(TEAM_IDS[0], 7),
            **base_kwargs,
        )
    with pytest.raises(ValueError, match="known team|team_ids"):
        module.load_team_memory_readiness_digest_report(
            team_ids=(TEAM_IDS[0], "unknown_team"),
            **base_kwargs,
        )

    assert calls == []


def test_rejects_non_callable_loader_builder_and_non_exact_configs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _module_under_test(monkeypatch)
    digest_config_type = _digest_config_type(monkeypatch)
    digest_config = digest_config_type()
    history_config = TeamDiagnosticsSnapshotHistoryConfig()
    gate_config = TeamDiagnosticsSnapshotHistoryGateConfig()
    calls: list[str] = []

    class DigestConfigSubclass(digest_config_type):
        pass

    class HistoryConfigSubclass(TeamDiagnosticsSnapshotHistoryConfig):
        pass

    class GateConfigSubclass(TeamDiagnosticsSnapshotHistoryGateConfig):
        pass

    def gate_loader(**_: object) -> TeamDiagnosticsSnapshotHistoryGateReport:
        calls.append("gate_loader")
        return _gate_report()

    def digest_builder(
        source_reports: object,
        *,
        config: object,
        generated_at: datetime,
    ) -> _DigestReport:
        calls.append("digest_builder")
        return _DigestReport()

    base_kwargs = {
        "team_ids": (TEAM_IDS[0],),
        "gate_loader": gate_loader,
        "digest_builder": digest_builder,
        "digest_config": digest_config,
        "history_config": history_config,
        "gate_config": gate_config,
        "generated_at": GENERATED_AT,
    }

    with pytest.raises(ValueError, match="gate_loader"):
        module.load_team_memory_readiness_digest_report(
            **{**base_kwargs, "gate_loader": object()},
        )
    with pytest.raises(ValueError, match="digest_builder"):
        module.load_team_memory_readiness_digest_report(
            **{**base_kwargs, "digest_builder": object()},
        )
    with pytest.raises(ValueError, match="TeamMemoryReadinessDigestConfig"):
        module.load_team_memory_readiness_digest_report(
            **{
                **base_kwargs,
                "digest_config": object.__new__(DigestConfigSubclass),
            },
        )
    with pytest.raises(ValueError, match="TeamDiagnosticsSnapshotHistoryConfig"):
        module.load_team_memory_readiness_digest_report(
            **{
                **base_kwargs,
                "history_config": object.__new__(HistoryConfigSubclass),
            },
        )
    with pytest.raises(ValueError, match="TeamDiagnosticsSnapshotHistoryGateConfig"):
        module.load_team_memory_readiness_digest_report(
            **{
                **base_kwargs,
                "gate_config": object.__new__(GateConfigSubclass),
            },
        )

    assert calls == []


@pytest.mark.parametrize("flag_name", ["paper_only", "report_only", "readonly"])
def test_requires_returned_digest_report_hard_flags(
    monkeypatch: pytest.MonkeyPatch,
    flag_name: str,
) -> None:
    module = _module_under_test(monkeypatch)
    digest_config = _digest_config_type(monkeypatch)()

    def gate_loader(**kwargs: object) -> TeamDiagnosticsSnapshotHistoryGateReport:
        team_id = kwargs["team_id"]
        assert type(team_id) is str
        return _gate_report()

    def digest_builder(
        source_reports: object,
        *,
        config: object,
        generated_at: datetime,
    ) -> Any:
        return _DigestReport(**{flag_name: False})

    with pytest.raises(ValueError, match=flag_name):
        module.load_team_memory_readiness_digest_report(
            team_ids=(TEAM_IDS[0],),
            gate_loader=gate_loader,
            digest_builder=digest_builder,
            digest_config=digest_config,
            history_config=TeamDiagnosticsSnapshotHistoryConfig(),
            gate_config=TeamDiagnosticsSnapshotHistoryGateConfig(),
            generated_at=GENERATED_AT,
        )


@pytest.mark.parametrize("flag_name", ["paper_only", "report_only", "readonly"])
def test_rejects_returned_digest_report_missing_hard_flags(
    monkeypatch: pytest.MonkeyPatch,
    flag_name: str,
) -> None:
    module = _module_under_test(monkeypatch)
    digest_config = _digest_config_type(monkeypatch)()

    def gate_loader(**kwargs: object) -> TeamDiagnosticsSnapshotHistoryGateReport:
        team_id = kwargs["team_id"]
        assert type(team_id) is str
        return _gate_report()

    def digest_builder(
        source_reports: object,
        *,
        config: object,
        generated_at: datetime,
    ) -> Any:
        values = {
            "digest_status": "pass",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
        del values[flag_name]
        return types.SimpleNamespace(**values)

    with pytest.raises(ValueError, match=flag_name):
        module.load_team_memory_readiness_digest_report(
            team_ids=(TEAM_IDS[0],),
            gate_loader=gate_loader,
            digest_builder=digest_builder,
            digest_config=digest_config,
            history_config=TeamDiagnosticsSnapshotHistoryConfig(),
            gate_config=TeamDiagnosticsSnapshotHistoryGateConfig(),
            generated_at=GENERATED_AT,
        )


def test_module_has_no_db_env_cli_store_lifecycle_or_write_surface(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _module_under_test(monkeypatch)
    module_path = Path(module.__file__)
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    dynamic_import_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
            is_import_module = (
                isinstance(function, ast.Name)
                and function.id == "import_module"
                or isinstance(function, ast.Attribute)
                and function.attr == "import_module"
            )
            if (
                is_import_module
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and type(node.args[0].value) is str
            ):
                dynamic_import_modules.append(node.args[0].value)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    banned_module_fragments = (
        "psycopg",
        "_env",
        "cli",
        "store",
    )
    banned_call_or_attribute_names = {
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "getenv",
        "insert",
        "open",
        "persist",
        "rollback",
        "write",
    }

    assert all(
        fragment not in module_name
        for module_name in imported_modules + dynamic_import_modules
        for fragment in banned_module_fragments
    )
    assert not (set(call_names) & banned_call_or_attribute_names)
    assert not (set(attribute_names) & banned_call_or_attribute_names)
