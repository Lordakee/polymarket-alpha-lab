from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.team_diagnostics_snapshot_history_gate import (
    DEFAULT_TEAM_DIAGNOSTICS_SNAPSHOT_HISTORY_GATE_CONFIG_VERSION,
    TeamDiagnosticsSnapshotHistoryGateReasonCodeCount,
    TeamDiagnosticsSnapshotHistoryGateReport,
)
from polymarket_alpha_lab.team_memory_readiness_digest import (
    DEFAULT_TEAM_MEMORY_READINESS_DIGEST_CONFIG_VERSION,
    TeamMemoryReadinessDigestConfig,
    TeamMemoryReadinessDigestReasonCodeCount,
    TeamMemoryReadinessDigestReport,
    TeamMemoryReadinessDigestSource,
    TeamMemoryReadinessDigestSourceStatus,
    build_team_memory_readiness_digest_report,
)


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)

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


def _source(
    team_id: str,
    gate_status: str,
    *,
    source_config_version: str = "source-history-v0",
    latest_snapshot_age_seconds: int | None = 60,
    source_snapshot_count: int = 3,
    source_required_snapshot_count: int = 3,
    source_status: str = "ready",
) -> TeamMemoryReadinessDigestSource:
    return TeamMemoryReadinessDigestSource(
        team_id=team_id,
        gate_report=_gate_report(
            gate_status,
            source_config_version=source_config_version,
            latest_snapshot_age_seconds=latest_snapshot_age_seconds,
            source_snapshot_count=source_snapshot_count,
            source_required_snapshot_count=source_required_snapshot_count,
            source_status=source_status,
        ),
    )


def _gate_report(
    gate_status: str,
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


def test_exports_expected_contract() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.team_memory_readiness_digest"
    )

    assert DEFAULT_TEAM_MEMORY_READINESS_DIGEST_CONFIG_VERSION == (
        "team-memory-readiness-digest-v0"
    )
    assert module.__all__ == (
        "DEFAULT_TEAM_MEMORY_READINESS_DIGEST_CONFIG_VERSION",
        "TeamMemoryReadinessDigestConfig",
        "TeamMemoryReadinessDigestSource",
        "TeamMemoryReadinessDigestSourceStatus",
        "TeamMemoryReadinessDigestReasonCodeCount",
        "TeamMemoryReadinessDigestReport",
        "build_team_memory_readiness_digest_report",
    )


def test_all_pass_sources_produce_pass_digest() -> None:
    report = build_team_memory_readiness_digest_report(
        (
            _source("politics", "pass"),
            _source("crypto_btc", "pass", source_config_version="history-v1"),
        ),
        config=TeamMemoryReadinessDigestConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.digest_status == "pass"
    assert report.recommended_next_step == "allow_team_memory_readiness_use"
    assert report.team_count == 2
    assert report.pass_count == 2
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.reason_codes == ("team_memory_readiness_digest_passed",)
    assert report.reason_code_counts == (
        TeamMemoryReadinessDigestReasonCodeCount(
            reason_code="team_memory_readiness_digest_passed",
            count=1,
        ),
    )
    assert report.source_config_versions == (
        ("crypto_btc", "history-v1"),
        ("politics", "source-history-v0"),
    )
    assert report.source_statuses == (
        TeamMemoryReadinessDigestSourceStatus(
            team_id="politics",
            gate_status="pass",
            recommended_next_step="allow_team_diagnostics_snapshot_history_memory_use",
            source_config_version="source-history-v0",
            latest_snapshot_age_seconds=60,
            source_snapshot_count=3,
            source_required_snapshot_count=3,
            source_status="ready",
        ),
        TeamMemoryReadinessDigestSourceStatus(
            team_id="crypto_btc",
            gate_status="pass",
            recommended_next_step="allow_team_diagnostics_snapshot_history_memory_use",
            source_config_version="history-v1",
            latest_snapshot_age_seconds=60,
            source_snapshot_count=3,
            source_required_snapshot_count=3,
            source_status="ready",
        ),
    )


def test_any_watch_source_produces_watch_digest() -> None:
    report = build_team_memory_readiness_digest_report(
        (
            _source("politics", "pass"),
            _source("crypto_eth", "watch"),
        ),
        config=TeamMemoryReadinessDigestConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.digest_status == "watch"
    assert report.recommended_next_step == "throttle_team_memory_readiness_use"
    assert report.team_count == 2
    assert report.pass_count == 1
    assert report.watch_count == 1
    assert report.blocked_count == 0
    assert report.reason_codes == (
        "team_memory_readiness_digest_watch_sources_present",
    )
    assert report.reason_code_counts == (
        TeamMemoryReadinessDigestReasonCodeCount(
            reason_code="team_memory_readiness_digest_watch_sources_present",
            count=1,
        ),
    )


def test_any_blocked_source_produces_blocked_digest() -> None:
    report = build_team_memory_readiness_digest_report(
        (
            _source("politics", "watch"),
            _source("macro_rates", "blocked"),
        ),
        config=TeamMemoryReadinessDigestConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == "block_team_memory_readiness_use"
    assert report.team_count == 2
    assert report.pass_count == 0
    assert report.watch_count == 1
    assert report.blocked_count == 1
    assert report.reason_codes == (
        "team_memory_readiness_digest_blocked_sources_present",
    )
    assert report.reason_code_counts == (
        TeamMemoryReadinessDigestReasonCodeCount(
            reason_code="team_memory_readiness_digest_blocked_sources_present",
            count=1,
        ),
    )


def test_empty_sources_block_digest() -> None:
    report = build_team_memory_readiness_digest_report(
        (),
        config=TeamMemoryReadinessDigestConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == "block_team_memory_readiness_use"
    assert report.team_count == 0
    assert report.pass_count == 0
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.source_statuses == ()
    assert report.source_config_versions == ()
    assert report.reason_codes == ("team_memory_readiness_digest_empty_sources",)
    assert report.reason_code_counts == (
        TeamMemoryReadinessDigestReasonCodeCount(
            reason_code="team_memory_readiness_digest_empty_sources",
            count=1,
        ),
    )


def test_duplicate_team_id_rejects() -> None:
    with pytest.raises(ValueError, match="team_id"):
        build_team_memory_readiness_digest_report(
            (
                _source("politics", "pass"),
                _source("politics", "watch"),
            ),
            config=TeamMemoryReadinessDigestConfig(),
            generated_at=GENERATED_AT,
        )


def test_distinct_sources_may_share_gate_config_version() -> None:
    report = build_team_memory_readiness_digest_report(
        (
            _source("politics", "pass"),
            _source("crypto_btc", "pass"),
        ),
        config=TeamMemoryReadinessDigestConfig(),
        generated_at=GENERATED_AT,
    )

    assert tuple(source.team_id for source in report.source_statuses) == (
        "politics",
        "crypto_btc",
    )
    assert report.team_count == 2
    assert report.pass_count == 2


def test_exact_config_and_source_type_validation() -> None:
    class ConfigSubclass(TeamMemoryReadinessDigestConfig):
        pass

    class SourceSubclass(TeamMemoryReadinessDigestSource):
        pass

    class GateReportSubclass(TeamDiagnosticsSnapshotHistoryGateReport):
        pass

    with pytest.raises(ValueError, match="config"):
        build_team_memory_readiness_digest_report(
            (_source("politics", "pass"),),
            config=ConfigSubclass(),
            generated_at=GENERATED_AT,
        )

    source_report = _gate_report("pass")
    subclass_report = GateReportSubclass(**source_report.__dict__)

    with pytest.raises(ValueError, match="source"):
        build_team_memory_readiness_digest_report(
            (
                SourceSubclass(
                    team_id="politics",
                    gate_report=source_report,
                ),
            ),
            config=TeamMemoryReadinessDigestConfig(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="gate_report"):
        TeamMemoryReadinessDigestSource(
            team_id="politics",
            gate_report=subclass_report,
        )

    with pytest.raises(ValueError, match="team_id"):
        TeamMemoryReadinessDigestSource(
            team_id="unknown_team",
            gate_report=source_report,
        )


def test_direct_report_constructor_consistency() -> None:
    source_status = TeamMemoryReadinessDigestSourceStatus(
        team_id="politics",
        gate_status="pass",
        recommended_next_step="allow",
        source_config_version="source-history-v0",
        latest_snapshot_age_seconds=None,
        source_snapshot_count=3,
        source_required_snapshot_count=3,
        source_status="ready",
    )
    reason_count = TeamMemoryReadinessDigestReasonCodeCount(
        reason_code="team_memory_readiness_digest_passed",
        count=1,
    )
    kwargs = dict(
        generated_at=GENERATED_AT,
        config_version=DEFAULT_TEAM_MEMORY_READINESS_DIGEST_CONFIG_VERSION,
        digest_status="pass",
        recommended_next_step="allow_team_memory_readiness_use",
        team_count=1,
        pass_count=1,
        watch_count=0,
        blocked_count=0,
        source_statuses=(source_status,),
        source_config_versions=(("politics", "source-history-v0"),),
        reason_code_counts=(reason_count,),
        reason_codes=("team_memory_readiness_digest_passed",),
    )

    assert TeamMemoryReadinessDigestReport(**kwargs).digest_status == "pass"

    with pytest.raises(ValueError, match="team_count"):
        TeamMemoryReadinessDigestReport(**{**kwargs, "team_count": 2})

    with pytest.raises(ValueError, match="pass_count"):
        TeamMemoryReadinessDigestReport(**{**kwargs, "pass_count": 0})

    with pytest.raises(ValueError, match="digest_status"):
        TeamMemoryReadinessDigestReport(**{**kwargs, "digest_status": "watch"})

    with pytest.raises(ValueError, match="recommended_next_step"):
        TeamMemoryReadinessDigestReport(
            **{**kwargs, "recommended_next_step": "block_team_memory_readiness_use"}
        )

    with pytest.raises(ValueError, match="source_config_versions"):
        TeamMemoryReadinessDigestReport(
            **{
                **kwargs,
                "source_config_versions": (("politics", "different-v0"),),
            }
        )

    with pytest.raises(ValueError, match="reason_codes"):
        TeamMemoryReadinessDigestReport(
            **{
                **kwargs,
                "reason_codes": (
                    "team_memory_readiness_digest_watch_sources_present",
                ),
            }
        )

    with pytest.raises(ValueError, match="reason_code_counts"):
        TeamMemoryReadinessDigestReport(
            **{
                **kwargs,
                "reason_code_counts": (
                    TeamMemoryReadinessDigestReasonCodeCount(
                        reason_code="team_memory_readiness_digest_passed",
                        count=2,
                    ),
                ),
            }
        )


def test_hard_flags_on_config_source_report_reason_counts_and_source_statuses() -> None:
    config = TeamMemoryReadinessDigestConfig()
    source_status = TeamMemoryReadinessDigestSourceStatus(
        team_id="politics",
        gate_status="pass",
        recommended_next_step="allow",
        source_config_version="source-history-v0",
        latest_snapshot_age_seconds=None,
        source_snapshot_count=3,
        source_required_snapshot_count=3,
        source_status="ready",
    )
    reason_count = TeamMemoryReadinessDigestReasonCodeCount(
        reason_code="team_memory_readiness_digest_passed",
        count=1,
    )
    report = build_team_memory_readiness_digest_report(
        (_source("politics", "pass"),),
        config=config,
        generated_at=GENERATED_AT,
    )

    source = TeamMemoryReadinessDigestSource(
        team_id="politics",
        gate_report=_gate_report("pass"),
    )

    for value in (config, source, source_status, reason_count, report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True

    with pytest.raises(ValueError, match="paper_only"):
        TeamMemoryReadinessDigestConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        TeamMemoryReadinessDigestSourceStatus(
            team_id="politics",
            gate_status="pass",
            recommended_next_step="allow",
            source_config_version="source-history-v0",
            latest_snapshot_age_seconds=None,
            source_snapshot_count=3,
            source_required_snapshot_count=3,
            source_status="ready",
            report_only=False,
        )

    with pytest.raises(ValueError, match="readonly"):
        TeamMemoryReadinessDigestReasonCodeCount(
            reason_code="team_memory_readiness_digest_passed",
            count=1,
            readonly=False,
        )

    with pytest.raises(ValueError, match="paper_only"):
        TeamMemoryReadinessDigestSource(
            team_id="politics",
            gate_report=_gate_report("pass"),
            paper_only=False,
        )

    invalid_source_status = TeamMemoryReadinessDigestSourceStatus(
        team_id="politics",
        gate_status="pass",
        recommended_next_step="allow",
        source_config_version="source-history-v0",
        latest_snapshot_age_seconds=None,
        source_snapshot_count=3,
        source_required_snapshot_count=3,
        source_status="ready",
    )
    object.__setattr__(invalid_source_status, "paper_only", False)
    with pytest.raises(ValueError, match="source_status"):
        TeamMemoryReadinessDigestReport(
            generated_at=GENERATED_AT,
            config_version=DEFAULT_TEAM_MEMORY_READINESS_DIGEST_CONFIG_VERSION,
            digest_status="pass",
            recommended_next_step="allow_team_memory_readiness_use",
            team_count=1,
            pass_count=1,
            watch_count=0,
            blocked_count=0,
            source_statuses=(
                invalid_source_status,
            ),
            source_config_versions=(("politics", "source-history-v0"),),
            reason_code_counts=(
                TeamMemoryReadinessDigestReasonCodeCount(
                    reason_code="team_memory_readiness_digest_passed",
                    count=1,
                ),
            ),
            reason_codes=("team_memory_readiness_digest_passed",),
        )


def test_digest_dataclasses_are_frozen() -> None:
    values = (
        TeamMemoryReadinessDigestConfig(),
        TeamMemoryReadinessDigestSourceStatus(
            team_id="politics",
            gate_status="pass",
            recommended_next_step="allow",
            source_config_version="source-history-v0",
            latest_snapshot_age_seconds=None,
            source_snapshot_count=3,
            source_required_snapshot_count=3,
            source_status="ready",
        ),
        TeamMemoryReadinessDigestReasonCodeCount(
            reason_code="team_memory_readiness_digest_passed",
            count=1,
        ),
        build_team_memory_readiness_digest_report(
            (_source("politics", "pass"),),
            config=TeamMemoryReadinessDigestConfig(),
            generated_at=GENERATED_AT,
        ),
    )

    for value in values:
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False


def test_no_float_literals_or_db_env_cli_psycopg_imports() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.team_memory_readiness_digest"
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    assert not any(isinstance(node, ast.Constant) and isinstance(node.value, float) for node in ast.walk(tree))

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_fragments = ("db", "env", "cli", "psycopg")
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_fragments
    )
