import pytest
from dataclasses import FrozenInstanceError

from polymarket_alpha_lab.proposal_evidence_comparison_artifact_registry import (
    PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS,
    REPORT_ONLY_FORBIDDEN_SURFACES,
    ProposalEvidenceComparisonArtifactDefinition,
    get_proposal_evidence_comparison_artifact,
    list_proposal_evidence_comparison_artifacts,
)


EXPECTED_ARTIFACT_IDS = (
    "proposal_evidence_comparison",
    "proposal_evidence_comparison_history",
    "proposal_evidence_comparison_history_batch_health",
    "proposal_evidence_comparison_history_batch_health_trend",
    "proposal_evidence_comparison_history_batch_health_trend_batch",
    "proposal_evidence_comparison_history_batch_health_trend_batch_health",
    "proposal_evidence_comparison_history_batch_health_trend_batch_health_trend",
)

EXPECTED_FORBIDDEN_SURFACES = (
    "account_action",
    "account_automation",
    "api_client",
    "approval_workflow",
    "browser_automation",
    "credential_workflow",
    "external_loader",
    "financial_advice",
    "jsonl_reader",
    "live_execution",
    "order_placement",
    "ranking",
    "recommendation",
    "scraping",
    "settlement_review",
    "trading",
    "websocket_client",
)

EXPECTED_ARTIFACT_METADATA = (
    (
        "proposal_evidence_comparison",
        "polymarket_alpha_lab.proposal_evidence_comparison",
        "TradeProposalEvidenceComparisonReport",
        "build_trade_proposal_evidence_comparison_report",
        "PaperForecastEvidenceReport+TradeProposalReviewDossierBatchReport",
        False,
    ),
    (
        "proposal_evidence_comparison_history",
        "polymarket_alpha_lab.proposal_evidence_comparison_history",
        "TradeProposalEvidenceComparisonHistoryReport",
        "build_trade_proposal_evidence_comparison_history_report",
        "TradeProposalEvidenceComparisonReport",
        True,
    ),
    (
        "proposal_evidence_comparison_history_batch_health",
        "polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health",
        "TradeProposalEvidenceComparisonHistoryBatchHealthReport",
        "build_trade_proposal_evidence_comparison_history_batch_health_report",
        "TradeProposalEvidenceComparisonHistoryReport",
        True,
    ),
    (
        "proposal_evidence_comparison_history_batch_health_trend",
        "polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport",
        "build_trade_proposal_evidence_comparison_history_batch_health_trend_report",
        "TradeProposalEvidenceComparisonHistoryBatchHealthReport",
        True,
    ),
    (
        "proposal_evidence_comparison_history_batch_health_trend_batch",
        "polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport",
        "build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport",
        True,
    ),
    (
        "proposal_evidence_comparison_history_batch_health_trend_batch_health",
        "polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport",
        "build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport",
        True,
    ),
    (
        "proposal_evidence_comparison_history_batch_health_trend_batch_health_trend",
        "polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health_trend",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendReport",
        "build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport",
        True,
    ),
)


def test_registry_lists_known_proposal_evidence_comparison_artifacts_in_order():
    artifacts = list_proposal_evidence_comparison_artifacts()

    assert artifacts is PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS
    assert tuple(artifact.artifact_id for artifact in artifacts) == EXPECTED_ARTIFACT_IDS
    assert tuple(sorted(EXPECTED_ARTIFACT_IDS)) == EXPECTED_ARTIFACT_IDS


def test_registry_definitions_are_report_only_and_supplied_input_only():
    assert REPORT_ONLY_FORBIDDEN_SURFACES == EXPECTED_FORBIDDEN_SURFACES
    for artifact in PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS:
        assert artifact.level == "level_2"
        assert artifact.module_name.startswith("polymarket_alpha_lab.")
        assert artifact.report_class_name.startswith("TradeProposal")
        assert artifact.builder_name.startswith("build_trade_")
        assert artifact.upstream_report_class_name
        assert artifact.report_only is True
        assert artifact.supplied_input_only is True
        assert artifact.forbidden_surfaces == REPORT_ONLY_FORBIDDEN_SURFACES
        assert "api_client" in artifact.forbidden_surfaces
        assert "browser_automation" in artifact.forbidden_surfaces
        assert "financial_advice" in artifact.forbidden_surfaces
        assert "order_placement" in artifact.forbidden_surfaces


def test_registry_definitions_match_exact_static_metadata():
    observed = tuple(
        (
            artifact.artifact_id,
            artifact.module_name,
            artifact.report_class_name,
            artifact.builder_name,
            artifact.upstream_report_class_name,
            artifact.append_only_log,
        )
        for artifact in PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS
    )

    assert observed == EXPECTED_ARTIFACT_METADATA


def test_registry_definitions_are_frozen_metadata():
    artifact = PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS[0]

    with pytest.raises(FrozenInstanceError):
        artifact.artifact_id = "mutated"


def test_registry_lookup_returns_exact_artifact_and_rejects_unknown_ids():
    artifact = get_proposal_evidence_comparison_artifact(
        "proposal_evidence_comparison_history_batch_health_trend_batch_health_trend",
    )

    assert artifact.report_class_name == (
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendReport"
    )
    assert artifact.upstream_report_class_name == (
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport"
    )
    assert artifact.append_only_log is True

    with pytest.raises(ValueError, match="artifact_id"):
        get_proposal_evidence_comparison_artifact("")
    with pytest.raises(ValueError, match="known proposal evidence comparison artifact"):
        get_proposal_evidence_comparison_artifact("unknown")


def test_registry_dataclass_rejects_mutated_or_loader_like_boundaries():
    base = PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS[0]

    with pytest.raises(ValueError, match="module_name"):
        ProposalEvidenceComparisonArtifactDefinition(
            artifact_id=base.artifact_id,
            level=base.level,
            module_name="requests",
            report_class_name=base.report_class_name,
            builder_name=base.builder_name,
            upstream_report_class_name=base.upstream_report_class_name,
            report_only=True,
            supplied_input_only=True,
            append_only_log=base.append_only_log,
        )
    with pytest.raises(ValueError, match="report_only"):
        ProposalEvidenceComparisonArtifactDefinition(
            artifact_id=base.artifact_id,
            level=base.level,
            module_name=base.module_name,
            report_class_name=base.report_class_name,
            builder_name=base.builder_name,
            upstream_report_class_name=base.upstream_report_class_name,
            report_only=False,
            supplied_input_only=True,
            append_only_log=base.append_only_log,
        )
    with pytest.raises(ValueError, match="supplied_input_only"):
        ProposalEvidenceComparisonArtifactDefinition(
            artifact_id=base.artifact_id,
            level=base.level,
            module_name=base.module_name,
            report_class_name=base.report_class_name,
            builder_name=base.builder_name,
            upstream_report_class_name=base.upstream_report_class_name,
            report_only=True,
            supplied_input_only=False,
            append_only_log=base.append_only_log,
        )
    with pytest.raises(ValueError, match="forbidden_surfaces"):
        ProposalEvidenceComparisonArtifactDefinition(
            artifact_id=base.artifact_id,
            level=base.level,
            module_name=base.module_name,
            report_class_name=base.report_class_name,
            builder_name=base.builder_name,
            upstream_report_class_name=base.upstream_report_class_name,
            report_only=True,
            supplied_input_only=True,
            append_only_log=base.append_only_log,
            forbidden_surfaces=("api_client",),
        )
