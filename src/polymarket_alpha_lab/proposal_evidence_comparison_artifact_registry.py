from __future__ import annotations

from dataclasses import dataclass

__all__ = (
    "PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS",
    "REPORT_ONLY_FORBIDDEN_SURFACES",
    "ProposalEvidenceComparisonArtifactDefinition",
    "get_proposal_evidence_comparison_artifact",
    "list_proposal_evidence_comparison_artifacts",
)

REPORT_ONLY_FORBIDDEN_SURFACES = (
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


@dataclass(frozen=True)
class ProposalEvidenceComparisonArtifactDefinition:
    artifact_id: str
    level: str
    module_name: str
    report_class_name: str
    builder_name: str
    upstream_report_class_name: str
    report_only: bool
    supplied_input_only: bool
    append_only_log: bool
    forbidden_surfaces: tuple[str, ...] = REPORT_ONLY_FORBIDDEN_SURFACES

    def __post_init__(self) -> None:
        _require_identifier("artifact_id", self.artifact_id)
        _require_identifier("level", self.level)
        _require_module_name(self.module_name)
        _require_identifier("report_class_name", self.report_class_name)
        _require_identifier("builder_name", self.builder_name)
        _require_identifier("upstream_report_class_name", self.upstream_report_class_name)
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.supplied_input_only is not True:
            raise ValueError("supplied_input_only must be True")
        if type(self.append_only_log) is not bool:
            raise ValueError("append_only_log must be a bool")
        if type(self.forbidden_surfaces) is not tuple:
            raise ValueError("forbidden_surfaces must be a tuple")
        if self.forbidden_surfaces != REPORT_ONLY_FORBIDDEN_SURFACES:
            raise ValueError("forbidden_surfaces must match report-only boundary set")


def _require_identifier(field_name: str, value: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_module_name(value: str) -> None:
    _require_identifier("module_name", value)
    if not value.startswith("polymarket_alpha_lab."):
        raise ValueError("module_name must be a polymarket_alpha_lab module")


PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS = (
    ProposalEvidenceComparisonArtifactDefinition(
        artifact_id="proposal_evidence_comparison",
        level="level_2",
        module_name="polymarket_alpha_lab.proposal_evidence_comparison",
        report_class_name="TradeProposalEvidenceComparisonReport",
        builder_name="build_trade_proposal_evidence_comparison_report",
        upstream_report_class_name="PaperForecastEvidenceReport+TradeProposalReviewDossierBatchReport",
        report_only=True,
        supplied_input_only=True,
        append_only_log=False,
    ),
    ProposalEvidenceComparisonArtifactDefinition(
        artifact_id="proposal_evidence_comparison_history",
        level="level_2",
        module_name="polymarket_alpha_lab.proposal_evidence_comparison_history",
        report_class_name="TradeProposalEvidenceComparisonHistoryReport",
        builder_name="build_trade_proposal_evidence_comparison_history_report",
        upstream_report_class_name="TradeProposalEvidenceComparisonReport",
        report_only=True,
        supplied_input_only=True,
        append_only_log=True,
    ),
    ProposalEvidenceComparisonArtifactDefinition(
        artifact_id="proposal_evidence_comparison_history_batch_health",
        level="level_2",
        module_name="polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health",
        report_class_name="TradeProposalEvidenceComparisonHistoryBatchHealthReport",
        builder_name="build_trade_proposal_evidence_comparison_history_batch_health_report",
        upstream_report_class_name="TradeProposalEvidenceComparisonHistoryReport",
        report_only=True,
        supplied_input_only=True,
        append_only_log=True,
    ),
    ProposalEvidenceComparisonArtifactDefinition(
        artifact_id="proposal_evidence_comparison_history_batch_health_trend",
        level="level_2",
        module_name="polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend",
        report_class_name="TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport",
        builder_name="build_trade_proposal_evidence_comparison_history_batch_health_trend_report",
        upstream_report_class_name="TradeProposalEvidenceComparisonHistoryBatchHealthReport",
        report_only=True,
        supplied_input_only=True,
        append_only_log=True,
    ),
    ProposalEvidenceComparisonArtifactDefinition(
        artifact_id="proposal_evidence_comparison_history_batch_health_trend_batch",
        level="level_2",
        module_name=(
            "polymarket_alpha_lab."
            "proposal_evidence_comparison_history_batch_health_trend_batch"
        ),
        report_class_name="TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport",
        builder_name="build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report",
        upstream_report_class_name="TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport",
        report_only=True,
        supplied_input_only=True,
        append_only_log=True,
    ),
    ProposalEvidenceComparisonArtifactDefinition(
        artifact_id="proposal_evidence_comparison_history_batch_health_trend_batch_health",
        level="level_2",
        module_name=(
            "polymarket_alpha_lab."
            "proposal_evidence_comparison_history_batch_health_trend_batch_health"
        ),
        report_class_name="TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport",
        builder_name="build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report",
        upstream_report_class_name="TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport",
        report_only=True,
        supplied_input_only=True,
        append_only_log=True,
    ),
    ProposalEvidenceComparisonArtifactDefinition(
        artifact_id=(
            "proposal_evidence_comparison_history_batch_health_trend_batch_health_trend"
        ),
        level="level_2",
        module_name=(
            "polymarket_alpha_lab."
            "proposal_evidence_comparison_history_batch_health_trend_batch_health_trend"
        ),
        report_class_name=(
            "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendReport"
        ),
        builder_name=(
            "build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report"
        ),
        upstream_report_class_name=(
            "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport"
        ),
        report_only=True,
        supplied_input_only=True,
        append_only_log=True,
    ),
)


def list_proposal_evidence_comparison_artifacts() -> tuple[
    ProposalEvidenceComparisonArtifactDefinition,
    ...,
]:
    return PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS


def get_proposal_evidence_comparison_artifact(
    artifact_id: str,
) -> ProposalEvidenceComparisonArtifactDefinition:
    _require_identifier("artifact_id", artifact_id)
    for artifact in PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS:
        if artifact.artifact_id == artifact_id:
            return artifact
    raise ValueError("artifact_id must identify a known proposal evidence comparison artifact")
