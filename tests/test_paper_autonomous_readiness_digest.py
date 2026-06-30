from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from importlib import import_module
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)
SOURCE_TZ = timezone(timedelta(hours=-4))


@dataclass(frozen=True)
class SourceReport:
    generated_at: datetime
    config_version: str
    status: str | None = None
    readiness_status: str | None = None
    gate_status: str | None = None
    health_status: str | None = None
    recommended_next_step: str = "review_source"
    reason_codes: tuple[str, ...] = ("source_passed",)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def _api():
    return import_module("polymarket_alpha_lab.paper_autonomous_readiness_digest")


def _source_report(
    *,
    status: str = "pass",
    field_name: str = "readiness_status",
    generated_at: datetime = GENERATED_AT,
    config_version: str = "source-v0",
    recommended_next_step: str = "review_source",
    reason_codes: tuple[str, ...] = ("source_passed",),
) -> SourceReport:
    kwargs = {
        "generated_at": generated_at,
        "config_version": config_version,
        field_name: status,
        "recommended_next_step": recommended_next_step,
        "reason_codes": reason_codes,
    }
    return SourceReport(**kwargs)


def _readiness_report(
    *,
    readiness_status: str = "pass",
    generated_at: datetime = GENERATED_AT,
    config_version: str = "readiness-gate-v0",
    recommended_next_step: str = "allow_paper_autonomous_readiness_review",
    reason_codes: tuple[str, ...] = ("paper_autonomous_readiness_gate_passed",),
) -> SourceReport:
    return _source_report(
        status=readiness_status,
        field_name="readiness_status",
        generated_at=generated_at,
        config_version=config_version,
        recommended_next_step=recommended_next_step,
        reason_codes=reason_codes,
    )


def test_readiness_digest_default_config_and_all_exports() -> None:
    api = _api()

    config = api.PaperAutonomousReadinessDigestConfig()

    assert config.config_version == "paper-autonomous-readiness-digest-v0"
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True
    assert api.__all__ == (
        "DEFAULT_PAPER_AUTONOMOUS_READINESS_DIGEST_CONFIG_VERSION",
        "PaperAutonomousReadinessDigestConfig",
        "PaperAutonomousReadinessDigestEvidence",
        "PaperAutonomousReadinessDigestReasonCodeCount",
        "PaperAutonomousReadinessDigestReport",
        "build_paper_autonomous_readiness_digest_report",
    )


def test_readiness_digest_passes_with_latest_readiness_only_and_normalizes_time() -> None:
    api = _api()
    generated_at = datetime(2026, 6, 25, 8, 0, tzinfo=SOURCE_TZ)
    readiness_report = _readiness_report(generated_at=generated_at)

    report = api.build_paper_autonomous_readiness_digest_report(
        readiness_report,
        config=api.PaperAutonomousReadinessDigestConfig(),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "paper-autonomous-readiness-digest-v0"
    assert report.digest_status == "pass"
    assert report.recommended_next_review_action == (
        "continue_operator_review_of_paper_autonomous_readiness_digest"
    )
    assert report.evidence == (
        api.PaperAutonomousReadinessDigestEvidence(
            source_name="readiness_gate",
            status="pass",
            recommended_next_step="allow_paper_autonomous_readiness_review",
            generated_at=GENERATED_AT,
            config_version="readiness-gate-v0",
            reason_codes=("paper_autonomous_readiness_gate_passed",),
            required=True,
        ),
    )
    assert report.source_config_versions == (
        ("readiness_gate", "readiness-gate-v0"),
    )
    assert report.reason_codes == (
        "paper_autonomous_readiness_digest_passed",
        "readiness_gate_pass",
    )
    assert report.reason_code_counts == (
        api.PaperAutonomousReadinessDigestReasonCodeCount(
            "paper_autonomous_readiness_digest_passed",
            1,
        ),
        api.PaperAutonomousReadinessDigestReasonCodeCount(
            "readiness_gate_pass",
            1,
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_readiness_digest_composes_optional_evidence_in_canonical_order() -> None:
    api = _api()

    report = api.build_paper_autonomous_readiness_digest_report(
        _readiness_report(
            readiness_status="watch",
            recommended_next_step="throttle_paper_autonomous_readiness_review",
            reason_codes=("readiness_watch_reason",),
        ),
        screening_report=_source_report(
            status="pass",
            field_name="health_status",
            config_version="screening-health-v0",
            recommended_next_step="review_screening_health",
            reason_codes=("screening_passed",),
        ),
        transition_report=_source_report(
            status="blocked",
            field_name="status",
            generated_at=GENERATED_AT - timedelta(minutes=7),
            config_version="transition-v0",
            recommended_next_step="review_transition_block",
            reason_codes=("transition_blocked",),
        ),
        allocation_report=_source_report(
            status="watch",
            field_name="gate_status",
            generated_at=GENERATED_AT - timedelta(minutes=5),
            config_version="allocation-gate-v0",
            recommended_next_step="review_allocation_watch",
            reason_codes=("allocation_watch",),
        ),
        agreement_trend_gate_report=_source_report(
            status="watch",
            field_name="gate_status",
            generated_at=GENERATED_AT - timedelta(minutes=3),
            config_version="agreement-trend-gate-v0",
            recommended_next_step="review_agreement_trend_gate_watch",
            reason_codes=("agreement_trend_gate_watch",),
        ),
        selection_summary_trend_gate_report=_source_report(
            status="pass",
            field_name="gate_status",
            generated_at=GENERATED_AT - timedelta(minutes=2),
            config_version="selection-summary-trend-gate-v0",
            recommended_next_step=(
                "allow_probability_selection_summary_history_trend_review"
            ),
            reason_codes=("selection_summary_trend_gate_passed",),
        ),
        ledger_report=_source_report(
            status="pass",
            field_name="gate_status",
            generated_at=GENERATED_AT - timedelta(minutes=10),
            config_version="ledger-gate-v0",
            recommended_next_step="review_ledger_pass",
            reason_codes=("ledger_passed",),
        ),
        config=api.PaperAutonomousReadinessDigestConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_review_action == (
        "review_blocked_paper_autonomous_readiness_evidence"
    )
    assert tuple(row.source_name for row in report.evidence) == (
        "readiness_gate",
        "screening",
        "transition",
        "allocation",
        "agreement_trend_gate",
        "selection_summary_trend_gate",
        "ledger",
    )
    assert tuple(row.status for row in report.evidence) == (
        "watch",
        "pass",
        "blocked",
        "watch",
        "watch",
        "pass",
        "pass",
    )
    assert report.source_config_versions == (
        ("readiness_gate", "readiness-gate-v0"),
        ("screening", "screening-health-v0"),
        ("transition", "transition-v0"),
        ("allocation", "allocation-gate-v0"),
        ("agreement_trend_gate", "agreement-trend-gate-v0"),
        ("selection_summary_trend_gate", "selection-summary-trend-gate-v0"),
        ("ledger", "ledger-gate-v0"),
    )
    assert report.reason_codes == (
        "agreement_trend_gate_watch",
        "allocation_watch",
        "ledger_pass",
        "readiness_gate_watch",
        "screening_pass",
        "selection_summary_trend_gate_pass",
        "transition_blocked",
    )
    assert report.reason_code_counts == (
        api.PaperAutonomousReadinessDigestReasonCodeCount(
            "agreement_trend_gate_watch",
            1,
        ),
        api.PaperAutonomousReadinessDigestReasonCodeCount("allocation_watch", 1),
        api.PaperAutonomousReadinessDigestReasonCodeCount("ledger_pass", 1),
        api.PaperAutonomousReadinessDigestReasonCodeCount("readiness_gate_watch", 1),
        api.PaperAutonomousReadinessDigestReasonCodeCount("screening_pass", 1),
        api.PaperAutonomousReadinessDigestReasonCodeCount(
            "selection_summary_trend_gate_pass",
            1,
        ),
        api.PaperAutonomousReadinessDigestReasonCodeCount("transition_blocked", 1),
    )


def test_readiness_digest_accepts_selection_summary_trend_gate_evidence() -> None:
    api = _api()

    report = api.build_paper_autonomous_readiness_digest_report(
        _readiness_report(),
        agreement_trend_gate_report=_source_report(
            status="pass",
            field_name="gate_status",
            config_version="agreement-trend-gate-v0",
            reason_codes=("agreement_trend_gate_passed",),
        ),
        selection_summary_trend_gate_report=_source_report(
            status="blocked",
            field_name="gate_status",
            config_version="selection-summary-trend-gate-v0",
            recommended_next_step=(
                "block_probability_selection_summary_history_trend_review"
            ),
            reason_codes=(
                "deteriorating_paper_probability_selection_summary_history_trend",
            ),
        ),
        config=api.PaperAutonomousReadinessDigestConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.digest_status == "blocked"
    assert tuple(row.source_name for row in report.evidence) == (
        "readiness_gate",
        "agreement_trend_gate",
        "selection_summary_trend_gate",
    )
    assert "selection_summary_trend_gate_blocked" in report.reason_codes


def test_readiness_digest_watches_when_any_evidence_watches_without_blockers() -> None:
    api = _api()

    report = api.build_paper_autonomous_readiness_digest_report(
        _readiness_report(),
        agreement_trend_gate_report=_source_report(
            status="watch",
            field_name="gate_status",
            config_version="agreement-trend-gate-v0",
            recommended_next_step="review_agreement_trend_gate_watch",
            reason_codes=("agreement_trend_gate_watch",),
        ),
        allocation_report=_source_report(
            status="watch",
            field_name="gate_status",
            recommended_next_step="review_allocation_watch",
            reason_codes=("allocation_watch",),
        ),
        config=api.PaperAutonomousReadinessDigestConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.digest_status == "watch"
    assert report.recommended_next_review_action == (
        "review_watch_paper_autonomous_readiness_evidence"
    )
    assert report.reason_codes == (
        "agreement_trend_gate_watch",
        "allocation_watch",
        "readiness_gate_pass",
    )


def test_readiness_digest_rejects_missing_readiness_report_and_bad_evidence() -> None:
    api = _api()

    with pytest.raises(ValueError, match="readiness_report is required"):
        api.build_paper_autonomous_readiness_digest_report(
            None,
            config=api.PaperAutonomousReadinessDigestConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="transition_report must expose status"):
        api.build_paper_autonomous_readiness_digest_report(
            _readiness_report(),
            transition_report=SourceReport(
                generated_at=GENERATED_AT,
                config_version="transition-v0",
                recommended_next_step="review_transition",
                reason_codes=("transition_checked",),
            ),
            config=api.PaperAutonomousReadinessDigestConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="allocation_report must be report_only"):
        api.build_paper_autonomous_readiness_digest_report(
            _readiness_report(),
            allocation_report=replace(
                _source_report(status="pass", field_name="gate_status"),
                report_only=False,
            ),
            config=api.PaperAutonomousReadinessDigestConfig(),
            generated_at=GENERATED_AT,
        )


def test_readiness_digest_dataclasses_are_frozen_and_validate_hard_flags() -> None:
    api = _api()
    config = api.PaperAutonomousReadinessDigestConfig()
    evidence = api.PaperAutonomousReadinessDigestEvidence(
        source_name="readiness_gate",
        status="pass",
        recommended_next_step="allow_paper_autonomous_readiness_review",
        generated_at=GENERATED_AT,
        config_version="readiness-gate-v0",
        reason_codes=("paper_autonomous_readiness_gate_passed",),
        required=True,
    )
    reason_count = api.PaperAutonomousReadinessDigestReasonCodeCount(
        "readiness_gate_pass",
        1,
    )
    report = api.build_paper_autonomous_readiness_digest_report(
        _readiness_report(),
        config=config,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        evidence.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        reason_count.report_count = 2  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.digest_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config .*paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="evidence .*report_only"):
        replace(evidence, report_only=False)
    with pytest.raises(ValueError, match="reason code count .*readonly"):
        replace(reason_count, readonly=False)
    with pytest.raises(ValueError, match="digest report .*paper_only"):
        replace(report, paper_only=False)


def test_readiness_digest_rejects_subclassed_dataclasses_and_unsorted_inputs() -> None:
    api = _api()

    with pytest.raises(TypeError, match="does not support subclassing"):

        class ConfigSubclass(api.PaperAutonomousReadinessDigestConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class ReportSubclass(api.PaperAutonomousReadinessDigestReport):
            pass

    with pytest.raises(ValueError, match="reason_codes must be sorted"):
        api.PaperAutonomousReadinessDigestEvidence(
            source_name="readiness_gate",
            status="pass",
            recommended_next_step="allow_paper_autonomous_readiness_review",
            generated_at=GENERATED_AT,
            config_version="readiness-gate-v0",
            reason_codes=("z_reason", "a_reason"),
            required=True,
        )
    with pytest.raises(ValueError, match="evidence must contain readiness_gate first"):
        api.PaperAutonomousReadinessDigestReport(
            generated_at=GENERATED_AT,
            config_version="paper-autonomous-readiness-digest-v0",
            digest_status="pass",
            recommended_next_review_action=(
                "continue_operator_review_of_paper_autonomous_readiness_digest"
            ),
            evidence=(
                api.PaperAutonomousReadinessDigestEvidence(
                    source_name="allocation",
                    status="pass",
                    recommended_next_step="review_allocation",
                    generated_at=GENERATED_AT,
                    config_version="allocation-v0",
                    reason_codes=("allocation_passed",),
                    required=False,
                ),
            ),
            source_config_versions=(("allocation", "allocation-v0"),),
            reason_code_counts=(
                api.PaperAutonomousReadinessDigestReasonCodeCount("allocation_pass", 1),
            ),
            reason_codes=("allocation_pass",),
        )


def test_readiness_digest_source_code_has_no_unsafe_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "paper_autonomous_readiness_digest.py"
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = {
        "auth",
        "account",
        "cancel",
        "environ",
        "live",
        "order",
        "psycopg",
        "sign",
        "submit",
        "supabase",
        "trade",
        "wallet",
    }
    module_docstring = ast.get_docstring(tree)

    values: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            values.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            values.append(node.module or "")
            values.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.Name):
            values.append(node.id)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                values.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                values.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            values.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value != module_docstring:
                values.append(node.value)

    for value in values:
        lowered = value.lower()
        for word in forbidden:
            assert word not in lowered, f"{value!r} contains {word!r}"
