"""Command-line interface for read-only market scans and strategy cycles."""

from __future__ import annotations

import argparse
from collections import Counter
import re
import shlex
import sys
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable
from urllib.parse import urlsplit

from polymarket_alpha_lab.api import PolymarketPublicClient
from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventCostAssumptions,
    PaperCostAwareEventStrategyConfig,
    polymarket_default_cost_assumptions,
)
from polymarket_alpha_lab.cost_aware_snapshot_builder import (
    PaperCostAwareSnapshotConfig,
)
from polymarket_alpha_lab.forecast_provider import PaperForecastConfig
from polymarket_alpha_lab.forecast_evidence import PaperForecastEvidenceLog
from polymarket_alpha_lab.llm_forecast import PaperLLMForecastConfig
from polymarket_alpha_lab.llm_research_transport import GLMChatTransport
from polymarket_alpha_lab.journal import PaperTradeJournal
from polymarket_alpha_lab.local_observability_trends import (
    LocalObservabilityTrendsConfig,
    LocalObservabilityTrendsReport,
    run_local_observability_trends,
)
from polymarket_alpha_lab.local_observability_trends_db_history import (
    LocalObservabilityTrendsDbHistoryConfig,
    LocalObservabilityTrendsDbHistoryReport,
    build_local_observability_trends_db_history_report,
)
from polymarket_alpha_lab.nav_risk_trend import PaperNavRiskTrendReport
from polymarket_alpha_lab.outcome_freshness import OutcomeFreshnessReport
from polymarket_alpha_lab.outcome_tracker import (
    OutcomeTrackingConfig,
    OutcomeTrackingLog,
    OutcomeTrackingReport,
    check_outcomes,
)
from polymarket_alpha_lab.outcome_tracking_psycopg import (
    insert_outcome_tracking_report_with_psycopg,
)
from polymarket_alpha_lab.paper_execution import PaperExecutionConfig
from polymarket_alpha_lab.paper_nav_snapshot_psycopg import (
    insert_paper_nav_snapshot_with_psycopg,
)
from polymarket_alpha_lab.paper_portfolio_nav import mark_paper_portfolio_nav
from polymarket_alpha_lab.paper_research_packet import (
    DEFAULT_PAPER_RESEARCH_PACKET_CONFIG_VERSION,
    DEFAULT_PAPER_RESEARCH_PACKET_MAX_PACKET_ROWS,
    DEFAULT_PAPER_RESEARCH_PACKET_MIN_SCORE,
    PaperResearchPacketConfig,
)
from polymarket_alpha_lab.paper_research_packet_db_history import (
    DEFAULT_PAPER_RESEARCH_PACKET_DB_HISTORY_CONFIG_VERSION,
    PaperResearchPacketDbHistoryConfig,
)
from polymarket_alpha_lab.paper_research_packet_quality_history import (
    DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_HISTORY_CONFIG_VERSION,
    PaperResearchPacketQualityHistoryConfig,
)
from polymarket_alpha_lab.paper_research_packet_operator_flow_db_history import (
    PaperResearchPacketOperatorFlowDbHistoryConfig,
    PaperResearchPacketOperatorFlowDbHistoryReport,
)
from polymarket_alpha_lab.paper_research_packet_operator_flow import (
    PaperResearchPacketOperatorFlowConfig,
    PaperResearchPacketOperatorFlowReport,
    build_paper_research_packet_operator_flow_report,
)
from polymarket_alpha_lab.paper_trade_journal_psycopg import (
    insert_paper_trade_record_with_psycopg,
)
from polymarket_alpha_lab.paper_trade_cost_audit import (
    PaperTradeCostAuditConfig,
    PaperTradeCostAuditReport,
    build_paper_trade_cost_audit_report,
)
from polymarket_alpha_lab.paper_trade_cost_trend import (
    PaperTradeCostTrendReport,
)
from polymarket_alpha_lab.paper_trade_cost_audit_psycopg import (
    insert_paper_trade_cost_audit_report_with_psycopg,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_psycopg_read import (
    MAX_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_READ_LIMIT,
)
from polymarket_alpha_lab.pipeline import MarketScanConfig, run_market_scan
from polymarket_alpha_lab.positions import PaperNavLog, PaperNavSnapshot
from polymarket_alpha_lab.paper_recommendation_cycle_snapshot_psycopg import (
    insert_paper_recommendation_cycle_snapshot_with_psycopg,
    load_paper_recommendation_cycle_snapshots_with_psycopg,
)
from polymarket_alpha_lab.paper_strategy_cycle_report_psycopg import (
    insert_paper_strategy_cycle_report_with_psycopg,
    load_paper_strategy_cycle_reports_with_psycopg,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_psycopg import (
    insert_paper_action_gated_strategy_recommendation_queue_report_with_psycopg,
)
from polymarket_alpha_lab.paper_recommendation_cycle_snapshot_trend import (
    build_paper_recommendation_cycle_snapshot_trend_report,
)
from polymarket_alpha_lab.paper_strategy_cycle_report_history import (
    PaperStrategyCycleReportHistoryConfig,
    PaperStrategyCycleReportHistoryReport,
    build_paper_strategy_cycle_report_history_report,
)
from polymarket_alpha_lab.paper_recommendation_cycle_review import (
    PaperRecommendationCycleReviewConfig,
    build_paper_recommendation_cycle_review_report,
)
from polymarket_alpha_lab.paper_recommendation_reason_trend import (
    PaperRecommendationReasonTrendConfig,
    PaperRecommendationReasonTrendReport,
    PaperRecommendationTransitionTrendRow,
    build_paper_recommendation_reason_trend_report,
)
from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateConfig,
    build_paper_recommendation_cycle_action_gate_report,
)
from polymarket_alpha_lab.performance_summary import (
    PerformanceSummary,
    PerformanceSummaryConfig,
    build_performance_summary,
)
from polymarket_alpha_lab.project_screening import PaperProjectScreeningConfig
from polymarket_alpha_lab.runner import RunLoopSummary, run_strategy_loop
from polymarket_alpha_lab.strategy_cycle import (
    PaperStrategyCycleConfig,
    PaperStrategyCycleLog,
    PaperStrategyCycleReport,
    run_strategy_cycle,
)
from polymarket_alpha_lab.strategy_audit_history import (
    PaperStrategyRiskAuditHistoryConfig,
    PaperStrategyRiskAuditHistoryReport,
    build_paper_strategy_risk_audit_history_report,
)
from polymarket_alpha_lab.strategy_recommendation_history import (
    PaperStrategyRecommendationHistoryReport,
    build_paper_strategy_recommendation_history_report,
)
from polymarket_alpha_lab.strategy_recommendation_bundle import (
    PaperStrategyRecommendationBundleReport,
)
from polymarket_alpha_lab.strategy_recommendation_log import (
    read_paper_strategy_recommendation_bundle_log,
)
from polymarket_alpha_lab.strategy_risk_audit import (
    PaperStrategyRiskAuditConfig,
    PaperStrategyRiskAuditReport,
    build_paper_strategy_risk_audit_report,
)
from polymarket_alpha_lab.strategy_risk_audit_psycopg import (
    insert_strategy_risk_audit_report_with_psycopg,
)
from polymarket_alpha_lab.strategy_risk_audit_log import PaperStrategyRiskAuditLog
from polymarket_alpha_lab.strategy_cycle_snapshot_source import (
    build_strategy_cycle_snapshot_source_report,
)
from polymarket_alpha_lab.strategy_cycle_action_gated_queue_source import (
    build_strategy_cycle_action_gated_queue_source_report,
)
from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_config import (
    from_action_gated_strategy_recommendation_queue_db_env,
)
from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_decision_support_config import (
    from_action_gated_strategy_recommendation_queue_decision_support_db_env,
)
from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_decision_support_trend_config import (
    from_action_gated_strategy_recommendation_queue_decision_support_trend_db_env,
)
from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_history_config import (
    from_action_gated_strategy_recommendation_queue_history_db_env,
)
from polymarket_alpha_lab.supabase_cycle_snapshot_config import (
    from_cycle_snapshot_db_env,
)
from polymarket_alpha_lab.supabase_outcome_tracking_config import (
    from_outcome_tracking_db_env,
)
from polymarket_alpha_lab.supabase_paper_nav_snapshot_config import (
    from_paper_nav_snapshot_db_env,
)
from polymarket_alpha_lab.supabase_paper_autonomous_screening_decision_support_gate_config import (
    from_paper_autonomous_screening_decision_support_gate_db_env,
)
from polymarket_alpha_lab.supabase_paper_execution_pipeline_config import (
    from_paper_execution_pipeline_db_env,
)
from polymarket_alpha_lab.supabase_paper_broker_config import (
    from_paper_broker_db_env,
)
from polymarket_alpha_lab.supabase_paper_autonomous_investment_ledger_config import (
    from_paper_autonomous_investment_ledger_db_env,
)
from polymarket_alpha_lab.supabase_paper_autonomous_investment_ledger_db_history_health_config import (
    from_paper_autonomous_investment_ledger_db_history_health_db_env,
)
from polymarket_alpha_lab.supabase_paper_autonomous_readiness_gate_config import (
    from_paper_autonomous_readiness_gate_db_env,
)
from polymarket_alpha_lab.supabase_paper_autonomous_readiness_digest_config import (
    from_paper_autonomous_readiness_digest_db_env,
)
from polymarket_alpha_lab.supabase_paper_autonomous_allocation_proposal_config import (
    from_paper_autonomous_allocation_proposal_db_env,
)
from polymarket_alpha_lab.supabase_paper_autonomous_allocation_proposal_db_history_health_config import (
    from_paper_autonomous_allocation_proposal_db_history_health_db_env,
)
from polymarket_alpha_lab.supabase_paper_research_packet_config import (
    from_paper_research_packet_db_env,
)
from polymarket_alpha_lab.supabase_paper_research_packet_quality_config import (
    from_paper_research_packet_quality_db_env,
)
from polymarket_alpha_lab.supabase_paper_research_packet_operator_flow_config import (
    from_paper_research_packet_operator_flow_db_env,
)
from polymarket_alpha_lab.supabase_paper_project_screening_rank_stability_config import (
    from_paper_project_screening_rank_stability_db_env,
)
from polymarket_alpha_lab.supabase_paper_trade_cost_audit_config import (
    from_paper_trade_cost_audit_db_env,
)
from polymarket_alpha_lab.supabase_paper_trade_journal_config import (
    from_paper_trade_journal_db_env,
)
from polymarket_alpha_lab.supabase_paper_strategy_cycle_report_config import (
    PAPER_STRATEGY_CYCLE_REPORT_DB_DSN_ENV_VAR,
    from_paper_strategy_cycle_report_db_env,
)
from polymarket_alpha_lab.supabase_probability_selection_summary_config import (
    PAPER_PROBABILITY_SELECTION_SUMMARY_DB_DSN_ENV_VAR,
    from_paper_probability_selection_summary_db_env,
)
from polymarket_alpha_lab.supabase_probability_selection_scorer_agreement_config import (
    PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR,
    from_probability_selection_scorer_agreement_db_env,
)
from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn
from polymarket_alpha_lab.supabase_paper_probability_selection_summary_history_config import (
    from_paper_probability_selection_summary_history_db_env,
)
from polymarket_alpha_lab.supabase_autonomous_market_scorer_config import (
    AUTONOMOUS_MARKET_SCORER_DB_DSN_ENV_VAR,
    from_autonomous_market_scorer_db_env,
)
from polymarket_alpha_lab.supabase_strategy_candidate_research_queue_config import (
    from_strategy_candidate_research_queue_db_env,
)
from polymarket_alpha_lab.supabase_strategy_candidate_research_queue_history_config import (
    from_strategy_candidate_research_queue_history_db_env,
)
from polymarket_alpha_lab.supabase_strategy_risk_audit_config import (
    from_strategy_risk_audit_db_env,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.nav_risk_metrics import PaperNavRiskMetricsReport
    from polymarket_alpha_lab.paper_probability_side_edge import (
        PaperProbabilitySideEdgeReport,
    )
    from polymarket_alpha_lab.strategy_evidence import (
        PaperStrategyEvidenceSnapshotReport,
    )


Runner = Callable[..., object]
CycleRunner = Callable[..., PaperStrategyCycleReport]
ClientFactory = Callable[[], Any]
NavRunner = Callable[..., PaperNavSnapshot]
HistoryRunner = Callable[..., PerformanceSummary]
LoopRunner = Callable[..., RunLoopSummary]
OutcomeRunner = Callable[..., OutcomeTrackingReport]
OutcomeTrackingDbSink = Callable[..., object]
PaperTradeRecordDbSink = Callable[..., object]
PaperNavSnapshotDbSink = Callable[..., object]
PaperTradeCostAuditDbSink = Callable[..., object]
StrategyRiskAuditDbSink = Callable[..., object]
PaperStrategyCycleReportDbSink = Callable[..., object]
StrategyCycleReportDbHistoryRunner = Callable[..., object]
StrategyCycleHistoryGateRunner = Callable[..., object]
StrategyCycleHistoryGateDbSink = Callable[..., object]
NavRiskRunner = Callable[..., "PaperNavRiskMetricsReport"]
StrategyAuditRunner = Callable[..., PaperStrategyRiskAuditReport]
StrategyAuditHistoryRunner = Callable[..., PaperStrategyRiskAuditHistoryReport]
StrategyAuditDbHistoryRunner = Callable[..., PaperStrategyRiskAuditHistoryReport]
StrategyRecommendationHistoryRunner = Callable[
    ...,
    PaperStrategyRecommendationHistoryReport,
]
CostAuditRunner = Callable[..., PaperTradeCostAuditReport]
CostAuditDbTrendRunner = Callable[..., PaperTradeCostTrendReport]
OutcomeTrackingDbHistoryRunner = Callable[..., OutcomeFreshnessReport]
NavSnapshotDbTrendRunner = Callable[..., PaperNavRiskTrendReport]
StrategyEvidenceRunner = Callable[..., "PaperStrategyEvidenceSnapshotReport"]
ObservabilityTrendsRunner = Callable[..., LocalObservabilityTrendsReport]
LocalObservabilityTrendsDbHistoryRunner = Callable[
    ...,
    LocalObservabilityTrendsDbHistoryReport,
]
LocalObservabilityTrendsDbSink = Callable[..., object]
CycleSnapshotSource = Callable[..., object]
CycleSnapshotDbSink = Callable[..., object]
ActionGatedQueueSource = Callable[..., object]
ActionGatedQueueDbSink = Callable[..., object]
ActionGatedQueueLoader = Callable[..., object]
ActionGatedQueuePriorityBuilder = Callable[..., object]
ActionGatedQueueRiskBuilder = Callable[..., object]
ActionGatedQueueHistoryBuilder = Callable[..., object]
ActionGatedQueueHistoryDbSink = Callable[..., object]
ActionGatedQueueHistoryDbHistoryRunner = Callable[..., object]
CycleSnapshotDbTrendRunner = Callable[..., object]
CycleSnapshotDbReviewRunner = Callable[..., object]
CycleSnapshotDbActionGateRunner = Callable[..., object]
ActionGatedQueueDecisionSupportTrendRunner = Callable[..., object]
ActionGatedQueueDecisionSupportTrendDbHistoryRunner = Callable[..., object]
StrategyCandidateResearchQueueLoader = Callable[..., object]
StrategyCandidateResearchQueueHistoryBuilder = Callable[..., object]
StrategyCandidateResearchQueueHistoryDbSink = Callable[..., object]
PaperResearchPacketBuilder = Callable[..., object]
PaperResearchPacketDbSink = Callable[..., object]
PaperResearchPacketDbHistoryRunner = Callable[..., object]
PaperResearchPacketQualityRunner = Callable[..., object]
PaperResearchPacketQualityDbHistoryRunner = Callable[..., object]
PaperResearchPacketOperatorFlowDbHistoryRunner = Callable[
    ...,
    PaperResearchPacketOperatorFlowDbHistoryReport,
]
PaperResearchPacketOperatorFlowDbHistoryGateRunner = Callable[..., object]
PaperAutonomousScreeningDecisionSupportGateRunner = Callable[..., object]
PaperAutonomousScreeningDecisionSupportGateDbSink = Callable[..., object]
PaperAutonomousAllocationProposalRunner = Callable[..., object]
PaperAutonomousAllocationProposalDbHistoryRunner = Callable[..., object]
PaperAutonomousAllocationProposalDbHistoryGateRunner = Callable[..., object]
PaperAutonomousAllocationProposalDbHistoryHealthRunner = Callable[..., object]
PaperAutonomousAllocationProposalDbHistoryMetricsRunner = Callable[..., object]
PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationRunner = Callable[..., object]
PaperAutonomousAllocationProposalDbHistoryHealthDbSink = Callable[..., object]
PaperAutonomousAllocationProposalDbHistoryHealthTrendRunner = Callable[..., object]
PaperAutonomousAllocationProposalDbHistoryHealthTrendGateRunner = Callable[
    ...,
    object,
]
PaperAutonomousAllocationProposalDbSink = Callable[..., object]
PaperExecutionPipelineRunner = Callable[..., object]
PaperExecutionPipelinePersister = Callable[..., object]
PaperAutonomousInvestmentLedgerRunner = Callable[..., object]
PaperAutonomousInvestmentLedgerDbSink = Callable[..., object]
PaperAutonomousInvestmentLedgerDbHistoryRunner = Callable[..., object]
PaperAutonomousInvestmentLedgerDbHistoryHealthRunner = Callable[..., object]
PaperAutonomousInvestmentLedgerDbHistoryHealthTrendRunner = Callable[..., object]
PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateRunner = Callable[
    ...,
    object,
]
PaperAutonomousReadinessDigestRunner = Callable[..., object]
PaperAutonomousReadinessDigestDbSink = Callable[..., object]
PaperResearchPacketOperatorFlowDbSink = Callable[..., object]
PaperProbabilityRecommendationQueueDbSink = Callable[..., object]
PaperRecommendationRiskBudgetDbSink = Callable[..., object]
PaperRecommendationReasonTrendDbSink = Callable[..., object]
PaperProbabilitySelectionSummaryHistoryRunner = Callable[..., object]
PaperProbabilitySelectionSummaryHistoryDbSink = Callable[..., object]
PaperProbabilitySelectionSummaryHistoryTrendRunner = Callable[..., object]
AutonomousMarketScorerHistoryRunner = Callable[..., object]
ProbabilitySelectionScorerAgreementRunner = Callable[..., object]
ProbabilitySelectionScorerAgreementDbSink = Callable[..., object]
ProbabilitySelectionScorerAgreementTrendRunner = Callable[..., object]
ProbabilitySelectionScorerAgreementTrendGateRunner = Callable[..., object]
MAX_PAPER_AUTONOMOUS_READINESS_DIGEST_READ_LIMIT = 500
_MISSING = object()
STRATEGY_CYCLE_HISTORY_GATE_DB_DSN_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_STRATEGY_CYCLE_HISTORY_GATE_DB_DSN"
)


@dataclass(frozen=True)
class _PaperRecommendationReasonTrendAdapterRow:
    market_slug: str
    side: str
    action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class _PaperRecommendationReasonTrendAdapterReport:
    generated_at: datetime
    rows: tuple[_PaperRecommendationReasonTrendAdapterRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class _PaperAutonomousScreeningDecisionSupportGateConfig:
    config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def _redact_db_dsn(text: str, *, dsn: str) -> str:
    return text.replace(dsn, "<redacted-dsn>")


def _redact_db_dsn_host(text: str, *, dsn: str) -> str:
    hosts: set[str] = set()
    if _is_simple_keyword_dsn(dsn):
        try:
            tokens = shlex.split(dsn)
        except ValueError:
            tokens = ()
        for token in tokens:
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            if key.lower() == "host" and value and not value.startswith("/"):
                hosts.add(value)
    else:
        try:
            parsed = urlsplit(dsn)
        except ValueError:
            parsed = None
        if parsed is not None and parsed.hostname:
            hosts.add(parsed.hostname)
    message = text
    for host in hosts:
        message = message.replace(host, "<redacted-host>")
    return message


def _redact_db_table_name(text: str, *, table_name: str) -> str:
    return text.replace(table_name, "<redacted-table>")


def _redact_db_table_name_and_tail(text: str, *, table_name: str) -> str:
    message = _redact_db_table_name(text, table_name=table_name)
    if "." not in table_name:
        return message
    schema, tail = table_name.split(".", 1)
    message = message.replace(schema, "<redacted-table>")
    return _redact_db_table_name(message, table_name=tail)


def _redact_paper_research_packet_sensitive_fields(text: str) -> str:
    message = _redact_keyed_sensitive_fields(
        text,
        field_names=("payload_json", "payload"),
        replacement="<redacted-payload>",
    )
    message = _redact_keyed_sensitive_fields(
        message,
        field_names=("score_rows_json", "score_rows"),
        replacement="<redacted-score-rows>",
    )
    message = _redact_keyed_sensitive_fields(
        message,
        field_names=("condition_id", "conditionId"),
        replacement="<redacted-market-detail>",
    )
    message = _redact_keyed_sensitive_fields(
        message,
        field_names=(
            "reason_codes_json",
            "reason_codes",
            "reason_code",
            "reasonCodes",
            "reasonCode",
        ),
        replacement="<redacted-reason-codes>",
    )
    message = _redact_keyed_sensitive_fields(
        message,
        field_names=("question",),
        replacement="<redacted-question>",
    )
    message = _redact_keyed_sensitive_fields(
        message,
        field_names=("market_slug",),
        replacement="<redacted-market-slug>",
    )
    message = _redact_keyed_sensitive_fields(
        message,
        field_names=("side",),
        replacement="<redacted-side>",
    )
    message = _redact_keyed_sensitive_fields(
        message,
        field_names=("action",),
        replacement="<redacted-action>",
    )
    message = _redact_keyed_sensitive_fields(
        message,
        field_names=("recommendation_score",),
        replacement="<redacted-recommendation-score>",
    )
    message = _redact_keyed_sensitive_fields(
        message,
        field_names=("allocation_rows_json", "allocation_rows"),
        replacement="<redacted-allocation-rows>",
    )
    message = _redact_keyed_sensitive_fields(
        message,
        field_names=("account", "account_id"),
        replacement="<redacted-account>",
    )
    message = _redact_keyed_sensitive_fields(
        message,
        field_names=("wallet", "wallet_address"),
        replacement="<redacted-wallet>",
    )
    message = _redact_keyed_sensitive_fields(
        message,
        field_names=(
            "order",
            "order_id",
            "order_identifier",
            "order_payload",
            "order_request",
        ),
        replacement="<redacted-order>",
    )
    message = _redact_keyed_sensitive_fields(
        message,
        field_names=(
            "market_question",
            "market_details",
            "details",
            "description",
            "title",
        ),
        replacement="<redacted-market-detail>",
    )
    message = _redact_keyed_sensitive_fields(
        message,
        field_names=(
            "secret",
            "secret_key",
            "client_secret",
            "password",
            "token",
            "access_token",
            "refresh_token",
            "auth",
            "auth_token",
            "bearer_token",
            "jwt_token",
            "api_key",
            "private_key",
            "authorization",
            "credential",
        ),
        replacement="<redacted-secret>",
    )
    message = re.sub(
        r"\breport_sha256=[A-Fa-f0-9]{64}\b",
        "report_sha256=<redacted-sha256>",
        message,
    )
    return re.sub(r"\b[A-Fa-f0-9]{64}\b", "<redacted-sha256>", message)


def _redact_keyed_sensitive_fields(
    text: str,
    *,
    field_names: tuple[str, ...],
    replacement: str,
) -> str:
    message = text
    for field_name in field_names:
        message = _redact_sensitive_equals_field(
            message,
            field_name=field_name,
            replacement=replacement,
        )
        message = _redact_sensitive_colon_field(
            message,
            field_name=field_name,
            replacement=replacement,
        )
        message = _redact_sensitive_json_field(
            message,
            field_name=field_name,
            replacement=replacement,
        )
        message = _redact_sensitive_python_repr_field(
            message,
            field_name=field_name,
            replacement=replacement,
        )
    return message


def _redact_sensitive_equals_field(
    text: str,
    *,
    field_name: str,
    replacement: str,
) -> str:
    pattern = re.compile(rf"\b{re.escape(field_name)}=", re.IGNORECASE)
    return _redact_sensitive_field_matches(
        text,
        pattern=pattern,
        replacement=f"{field_name}={replacement}",
    )


def _redact_sensitive_colon_field(
    text: str,
    *,
    field_name: str,
    replacement: str,
) -> str:
    pattern = re.compile(rf"\b{re.escape(field_name)}:\s*", re.IGNORECASE)
    return _redact_sensitive_field_matches(
        text,
        pattern=pattern,
        replacement=f"{field_name}: {replacement}",
    )


def _redact_sensitive_json_field(
    text: str,
    *,
    field_name: str,
    replacement: str,
) -> str:
    pattern = re.compile(rf'"{re.escape(field_name)}"\s*:\s*', re.IGNORECASE)
    return _redact_sensitive_field_matches(
        text,
        pattern=pattern,
        replacement=f'"{field_name}": "{replacement}"',
    )


def _redact_sensitive_python_repr_field(
    text: str,
    *,
    field_name: str,
    replacement: str,
) -> str:
    pattern = re.compile(rf"'{re.escape(field_name)}'\s*:\s*", re.IGNORECASE)
    return _redact_sensitive_field_matches(
        text,
        pattern=pattern,
        replacement=f"'{field_name}': '{replacement}'",
    )


def _redact_sensitive_field_matches(
    text: str,
    *,
    pattern: re.Pattern[str],
    replacement: str,
) -> str:
    parts: list[str] = []
    cursor = 0
    while True:
        match = pattern.search(text, cursor)
        if match is None:
            parts.append(text[cursor:])
            break
        parts.append(text[cursor : match.start()])
        value_end = _sensitive_field_value_end(text, match.end())
        parts.append(replacement)
        cursor = value_end
    return "".join(parts)


def _sensitive_field_value_end(text: str, start: int) -> int:
    json_value_end = _json_like_value_end(text, start)
    if json_value_end is not None:
        field_start = _next_key_value_field_start(text, json_value_end)
        if field_start is None:
            return len(text)
        return field_start
    quoted_value_end = _quoted_value_end(text, start)
    if quoted_value_end is not None:
        field_start = _next_key_value_field_start(text, quoted_value_end)
        if field_start is None:
            return quoted_value_end
        return field_start
    field_start = _next_key_value_field_start(text, start)
    if field_start is None:
        return len(text)
    return field_start


def _quoted_value_end(text: str, start: int) -> int | None:
    index = start
    while index < len(text) and text[index].isspace():
        index += 1
    if index >= len(text) or text[index] not in {'"', "'"}:
        return None

    quote = text[index]
    escaped = False
    for position in range(index + 1, len(text)):
        char = text[position]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == quote:
            return position + 1
    return len(text)


def _json_like_value_end(text: str, start: int) -> int | None:
    index = start
    while index < len(text) and text[index].isspace():
        index += 1
    if index >= len(text) or text[index] not in "{[":
        return None

    closing_by_opening = {"{": "}", "[": "]"}
    stack = [text[index]]
    quote: str | None = None
    escaped = False
    for position in range(index + 1, len(text)):
        char = text[position]
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue

        if char in {'"', "'"}:
            quote = char
            continue
        if char in closing_by_opening:
            stack.append(char)
            continue
        if char in ("}", "]"):
            if not stack or closing_by_opening[stack[-1]] != char:
                return None
            stack.pop()
            if not stack:
                return position + 1
    return None


def _next_key_value_field_start(text: str, start: int) -> int | None:
    index = start
    while True:
        match = re.search(
            r'(?:\s+(?:"[A-Za-z_][A-Za-z0-9_]*"\s*:|'
            r"[A-Za-z_][A-Za-z0-9_]*(?:=|:))|"
            r",\s*'[A-Za-z_][A-Za-z0-9_]+'\s*:)",
            text[index:],
        )
        if match is None:
            return None
        candidate = index + match.start()
        key_start = _key_start_after_field_separator(text, candidate)
        if _is_false_key_value_in_question(text, candidate):
            index = key_start
            continue
        return candidate


def _key_start_after_field_separator(text: str, candidate: int) -> int:
    key_start = candidate
    while key_start < len(text) and (
        text[key_start].isspace() or text[key_start] == ","
    ):
        key_start += 1
    return key_start


def _is_false_key_value_in_question(text: str, candidate: int) -> bool:
    key_start = _key_start_after_field_separator(text, candidate)
    if key_start < len(text) and text[key_start] in {'"', "'"}:
        return False
    key_end = key_start
    while key_end < len(text) and (
        text[key_end].isalnum() or text[key_end] == "_"
    ):
        key_end += 1
    key = text[key_start:key_end]
    if key in {"payload_json", "payload", "question"}:
        return False
    separator_index = key_end
    value_start = separator_index + 1
    if separator_index >= len(text) or text[separator_index] != "=":
        return False
    value_end = value_start
    while value_end < len(text) and not text[value_end].isspace():
        value_end += 1
    next_word_start = value_end
    while next_word_start < len(text) and text[next_word_start].isspace():
        next_word_start += 1
    if next_word_start >= len(text):
        return False
    next_word_end = next_word_start
    while next_word_end < len(text) and not text[next_word_end].isspace():
        next_word_end += 1
    next_word = text[next_word_start:next_word_end]
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(?:=|:).*", next_word):
        return False
    return text[next_word_start].isalpha()


def _redacted_paper_research_packet_db_history_error(
    exc: Exception,
    *,
    dsn: str,
    table_name: str,
) -> RuntimeError:
    message = _redact_db_dsn(str(exc), dsn=dsn)
    message = _redact_db_table_name_and_tail(message, table_name=table_name)
    message = _redact_paper_research_packet_sensitive_fields(message)
    if not message.strip():
        message = exc.__class__.__name__
    return RuntimeError(message)


def _redacted_paper_readiness_digest_error(
    exc: Exception,
    *,
    readiness_dsn: str,
    readiness_table_name: str,
    agreement_dsn: str | None = None,
    agreement_table_name: str | None = None,
    digest_dsn: str | None = None,
    digest_table_name: str | None = None,
) -> RuntimeError:
    message = str(exc)
    for dsn_value in (readiness_dsn, agreement_dsn, digest_dsn):
        if dsn_value is not None:
            message = _redact_db_dsn(message, dsn=dsn_value)
    for dsn_value in (readiness_dsn, agreement_dsn, digest_dsn):
        if dsn_value is not None:
            message = _redact_db_dsn_host(message, dsn=dsn_value)
    message = _redact_db_table_name_and_tail(
        message,
        table_name=readiness_table_name,
    )
    if agreement_table_name is not None:
        message = _redact_db_table_name_and_tail(
            message,
            table_name=agreement_table_name,
        )
    if digest_table_name is not None:
        message = _redact_db_table_name_and_tail(
            message,
            table_name=digest_table_name,
        )
    message = _redact_paper_research_packet_sensitive_fields(message)
    if not message.strip():
        message = exc.__class__.__name__
    return RuntimeError(message)


def _redacted_paper_research_packet_quality_error(
    exc: Exception,
    *,
    source_dsn: str,
    source_table_name: str,
    quality_dsn: str | None = None,
    quality_table_name: str | None = None,
) -> RuntimeError:
    message = _redact_db_dsn(str(exc), dsn=source_dsn)
    message = _redact_db_table_name_and_tail(
        message,
        table_name=source_table_name,
    )
    if quality_dsn is not None:
        message = _redact_db_dsn(message, dsn=quality_dsn)
    if quality_table_name is not None:
        message = _redact_db_table_name_and_tail(
            message,
            table_name=quality_table_name,
        )
    message = _redact_paper_research_packet_sensitive_fields(message)
    if not message.strip():
        message = exc.__class__.__name__
    return RuntimeError(message)


def _redacted_paper_autonomous_allocation_proposal_db_history_health_persistence_error(
    exc: Exception,
    *,
    source_dsn: str,
    source_table_name: str,
    health_dsn: str,
    health_table_name: str,
) -> RuntimeError:
    message = str(exc)
    for dsn in (source_dsn, health_dsn):
        message = _redact_db_dsn(message, dsn=dsn)
    for table_name in (source_table_name, health_table_name):
        message = _redact_db_table_name_and_tail(message, table_name=table_name)
    message = _redact_paper_research_packet_sensitive_fields(message)
    if not message.strip():
        message = exc.__class__.__name__
    return RuntimeError(message)


def _redacted_paper_research_packet_operator_flow_error(
    exc: Exception,
    *,
    source_dsn: str | None,
    source_table_name: str | None,
    packet_dsn: str | None,
    packet_table_name: str | None,
    quality_dsn: str | None,
    quality_table_name: str | None,
    operator_flow_dsn: str | None,
    operator_flow_table_name: str | None,
) -> RuntimeError:
    message = str(exc)
    for dsn in (source_dsn, packet_dsn, quality_dsn, operator_flow_dsn):
        if dsn is not None:
            message = _redact_db_dsn(message, dsn=dsn)
    for table_name in (
        source_table_name,
        packet_table_name,
        quality_table_name,
        operator_flow_table_name,
    ):
        if table_name is not None:
            message = _redact_db_table_name_and_tail(message, table_name=table_name)
    message = _redact_paper_research_packet_sensitive_fields(message)
    if not message.strip():
        message = exc.__class__.__name__
    return RuntimeError(message)


def _redacted_paper_probability_selection_summary_history_error(
    exc: Exception,
    *,
    dsn: str,
    table_name: str,
) -> RuntimeError:
    message = _redact_db_dsn(str(exc), dsn=dsn)
    message = _redact_db_table_name_and_tail(message, table_name=table_name)
    message = _redact_paper_research_packet_sensitive_fields(message)
    if not message.strip():
        message = exc.__class__.__name__
    return RuntimeError(message)


def _redacted_paper_probability_selection_summary_history_trend_error(
    exc: Exception,
    *,
    dsn: str,
    table_name: str,
) -> RuntimeError:
    message = _redact_db_dsn(str(exc), dsn=dsn)
    message = _redact_db_table_name_and_tail(message, table_name=table_name)
    message = _redact_paper_research_packet_sensitive_fields(message)
    if not message.strip():
        message = exc.__class__.__name__
    return RuntimeError(message)


def _redacted_autonomous_market_scorer_history_error(
    exc: Exception,
    *,
    dsn: str,
    table_name: str,
) -> RuntimeError:
    message = _redact_db_dsn(str(exc), dsn=dsn)
    message = _redact_db_table_name_and_tail(message, table_name=table_name)
    message = _redact_paper_research_packet_sensitive_fields(message)
    if not message.strip():
        message = exc.__class__.__name__
    return RuntimeError(message)


def _redacted_probability_selection_scorer_agreement_error(
    exc: Exception,
    *,
    selection_summary_dsn: str,
    selection_summary_table_name: str,
    scorer_dsn: str,
    scorer_table_name: str,
    agreement_dsn: str | None = None,
    agreement_table_name: str | None = None,
) -> RuntimeError:
    message = str(exc)
    for dsn_value in (selection_summary_dsn, scorer_dsn, agreement_dsn):
        if dsn_value is not None:
            message = _redact_db_dsn(message, dsn=dsn_value)
    for storage_name in (
        selection_summary_table_name,
        scorer_table_name,
        agreement_table_name,
    ):
        if storage_name is not None:
            message = _redact_db_table_name_and_tail(message, table_name=storage_name)
    message = _redact_paper_research_packet_sensitive_fields(message)
    if not message.strip():
        message = exc.__class__.__name__
    return RuntimeError(message)


def _redacted_probability_selection_scorer_agreement_trend_error(
    exc: Exception,
    *,
    dsn: str,
    table_name: str,
) -> RuntimeError:
    message = _redact_db_dsn(str(exc), dsn=dsn)
    message = _redact_db_dsn_host(message, dsn=dsn)
    message = _redact_db_table_name_and_tail(message, table_name=table_name)
    message = _redact_paper_research_packet_sensitive_fields(message)
    if not message.strip():
        message = exc.__class__.__name__
    return RuntimeError(message)


def _redacted_paper_probability_selection_summary_history_persistence_error(
    exc: Exception,
    *,
    source_dsn: str,
    source_table_name: str,
    history_dsn: str,
    history_table_name: str,
) -> RuntimeError:
    message = str(exc)
    for dsn in (source_dsn, history_dsn):
        message = _redact_db_dsn(message, dsn=dsn)
    for table_name in (source_table_name, history_table_name):
        message = _redact_db_table_name_and_tail(message, table_name=table_name)
    message = _redact_paper_research_packet_sensitive_fields(message)
    if not message.strip():
        message = exc.__class__.__name__
    return RuntimeError(message)


def _redacted_paper_autonomous_screening_gate_error(
    exc: Exception,
    *,
    rank_stability_dsn: str | None,
    rank_stability_table_name: str | None,
    operator_flow_dsn: str,
    operator_flow_table_name: str,
    action_queue_dsn: str | None = None,
    action_queue_table_name: str | None = None,
) -> RuntimeError:
    message = str(exc)
    for dsn in (rank_stability_dsn, operator_flow_dsn, action_queue_dsn):
        if dsn is not None:
            message = _redact_db_dsn(message, dsn=dsn)
    for table_name in (
        rank_stability_table_name,
        operator_flow_table_name,
        action_queue_table_name,
    ):
        if table_name is not None:
            message = _redact_db_table_name_and_tail(message, table_name=table_name)
    message = _redact_paper_research_packet_sensitive_fields(message)
    if not message.strip():
        message = exc.__class__.__name__
    return RuntimeError(message)


def _redacted_paper_autonomous_allocation_proposal_error(
    exc: Exception,
    *,
    screening_gate_dsn: str | None,
    screening_gate_table_name: str | None,
    action_gated_queue_decision_support_dsn: str | None,
    action_gated_queue_decision_support_table_name: str | None,
    source_queue_dsn: str | None,
    source_queue_table_name: str | None,
) -> RuntimeError:
    message = str(exc)
    for dsn in (
        screening_gate_dsn,
        action_gated_queue_decision_support_dsn,
        source_queue_dsn,
    ):
        if dsn is not None:
            message = _redact_db_dsn(message, dsn=dsn)
    for table_name in (
        screening_gate_table_name,
        action_gated_queue_decision_support_table_name,
        source_queue_table_name,
    ):
        if table_name is not None:
            message = _redact_db_table_name_and_tail(message, table_name=table_name)
    message = _redact_paper_research_packet_sensitive_fields(message)
    if not message.strip():
        message = exc.__class__.__name__
    return RuntimeError(message)


def _redacted_paper_autonomous_investment_ledger_error(
    exc: Exception,
    *,
    broker_dsn: str,
    broker_table_name: str,
    ledger_dsn: str | None = None,
    ledger_table_name: str | None = None,
) -> RuntimeError:
    message = str(exc)
    for dsn in (broker_dsn, ledger_dsn):
        if dsn is not None:
            message = _redact_db_dsn(message, dsn=dsn)
    for table_name in (broker_table_name, ledger_table_name):
        if table_name is not None:
            message = _redact_db_table_name_and_tail(message, table_name=table_name)
    message = _redact_paper_research_packet_sensitive_fields(message)
    if not message.strip():
        message = exc.__class__.__name__
    return RuntimeError(message)


def _require_paper_autonomous_allocation_proposal_limit(
    limit: object,
    *,
    command_name: str = "paper-autonomous-allocation-proposal",
) -> None:
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError(f"{command_name} limit must be positive")
    if limit > MAX_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_READ_LIMIT:
        raise ValueError(
            f"{command_name} limit must be less than or equal to "
            f"{MAX_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_READ_LIMIT}",
        )


def _require_paper_autonomous_readiness_digest_limit(limit: object) -> None:
    command_name = "paper-autonomous-readiness-digest"
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError(f"{command_name} limit must be positive")
    if limit > MAX_PAPER_AUTONOMOUS_READINESS_DIGEST_READ_LIMIT:
        raise ValueError(
            f"{command_name} limit must be less than or equal to "
            f"{MAX_PAPER_AUTONOMOUS_READINESS_DIGEST_READ_LIMIT}",
        )


def _require_probability_selection_scorer_agreement_limit(limit: object) -> None:
    command_name = "probability-selection-scorer-agreement"
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError(f"{command_name} limit must be positive")


def _is_simple_keyword_dsn(value: str) -> bool:
    return "=" in value and "://" not in value


def _raise_redacted_db_sink_error(
    exc: Exception,
    *,
    dsn: str,
    table_name: str | None = None,
) -> None:
    message = _redact_db_dsn(str(exc), dsn=dsn)
    if table_name:
        message = _redact_db_table_name(message, table_name=table_name)
    if not message.strip():
        message = exc.__class__.__name__
    raise RuntimeError(message) from None


def _raise_redacted_db_read_error(exc: Exception, *, dsn: str) -> None:
    message = _redact_db_dsn(str(exc), dsn=dsn)
    if not message.strip():
        message = exc.__class__.__name__
    raise RuntimeError(message) from None


def _raise_redacted_strategy_cycle_report_db_history_error(
    exc: Exception,
    *,
    dsn: str,
    table_name: str,
) -> None:
    message = _redact_db_dsn(str(exc), dsn=dsn)
    message = _redact_db_table_name_and_tail(message, table_name=table_name)
    if not message.strip():
        message = exc.__class__.__name__
    raise RuntimeError(message) from None


def _raise_redacted_strategy_cycle_history_gate_error(
    exc: Exception,
    *,
    source_dsn: str,
    source_table_name: str,
    gate_dsn: str | None = None,
    gate_table_name: str | None = None,
) -> None:
    message = str(exc)
    for dsn in (source_dsn, gate_dsn):
        if dsn is not None:
            message = _redact_db_dsn(message, dsn=dsn)
    for table_name in (source_table_name, gate_table_name):
        if table_name is not None:
            message = _redact_db_table_name_and_tail(message, table_name=table_name)
    if not message.strip():
        message = exc.__class__.__name__
    raise RuntimeError(message) from None


def _raise_redacted_multi_db_sink_error(
    exc: Exception,
    *,
    dsns: tuple[str | None, ...],
) -> None:
    message = str(exc)
    for dsn in dsns:
        if dsn is not None:
            message = _redact_db_dsn(message, dsn=dsn)
    if not message.strip():
        message = exc.__class__.__name__
    raise RuntimeError(message) from None


def _cli_decimal(value: str) -> Decimal:
    try:
        decimal = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise argparse.ArgumentTypeError("must be a decimal value") from exc
    if not decimal.is_finite():
        raise argparse.ArgumentTypeError("must be a finite decimal value")
    return decimal


def _apply_json_config(args: argparse.Namespace) -> None:
    """Override argparse defaults from a JSON config file (--config flag).

    Reads the JSON file referenced by ``args.config`` and sets any missing
    attributes on ``args`` from the config. Explicit CLI flags always win
    over config values (CLI is checked first via ``hasattr`` + sentinel).
    """
    if not getattr(args, "config", None):
        return
    import json
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    key_map = {
        "forecast_provider": "forecast_provider",
        "llm_api_token": "llm_api_token",
        "max_markets_per_cycle": "max_markets",
        "scan_limit": "limit",
        "prefilter_by_score": "prefilter",
        "paper_execute": "paper_execute",
        "paper_journal": "paper_journal",
        "nav_log": "nav_log",
        "cycle_log": "cycle_log",
        "outcome_log": "outcome_log",
        "archive_root": "archive_root",
        "repeat_interval_seconds": "repeat_interval",
        "max_iterations": "max_iterations",
        "starting_cash": "starting_cash",
        "market_search": "market_search",
        "strategy_audit_preflight": "strategy_audit_preflight",
        "strategy_audit_log": "strategy_audit_log",
    }
    for json_key, arg_key in key_map.items():
        if json_key not in cfg:
            continue
        val = cfg[json_key]
        current = getattr(args, arg_key, None)
        if current is not None and arg_key != "prefilter":
            continue
        if arg_key == "starting_cash" and val is not None:
            val = Decimal(str(val))
        if arg_key in (
            "paper_journal",
            "nav_log",
            "cycle_log",
            "outcome_log",
            "strategy_audit_log",
            "archive_root",
        ) and val is not None:
            val = Path(val)
        setattr(args, arg_key, val)


def main(
    argv: list[str] | None = None,
    *,
    runner: Runner = run_market_scan,
    cycle_runner: CycleRunner = run_strategy_cycle,
    nav_runner: NavRunner = mark_paper_portfolio_nav,
    client_factory: ClientFactory = PolymarketPublicClient,
    history_runner: HistoryRunner | None = None,
    nav_risk_runner: NavRiskRunner | None = None,
    loop_runner: LoopRunner = run_strategy_loop,
    outcome_runner: OutcomeRunner = check_outcomes,
    outcome_tracking_db_sink: OutcomeTrackingDbSink = (
        insert_outcome_tracking_report_with_psycopg
    ),
    paper_trade_record_db_sink: PaperTradeRecordDbSink = (
        insert_paper_trade_record_with_psycopg
    ),
    paper_strategy_cycle_report_db_sink: PaperStrategyCycleReportDbSink = (
        insert_paper_strategy_cycle_report_with_psycopg
    ),
    strategy_cycle_report_db_history_runner: (
        StrategyCycleReportDbHistoryRunner | None
    ) = None,
    strategy_cycle_history_gate_runner: StrategyCycleHistoryGateRunner | None = None,
    strategy_cycle_history_gate_db_sink: StrategyCycleHistoryGateDbSink | None = None,
    paper_nav_snapshot_db_sink: PaperNavSnapshotDbSink = (
        insert_paper_nav_snapshot_with_psycopg
    ),
    paper_trade_cost_audit_db_sink: PaperTradeCostAuditDbSink = (
        insert_paper_trade_cost_audit_report_with_psycopg
    ),
    strategy_risk_audit_db_sink: StrategyRiskAuditDbSink = (
        insert_strategy_risk_audit_report_with_psycopg
    ),
    strategy_audit_runner: StrategyAuditRunner | None = None,
    strategy_audit_history_runner: StrategyAuditHistoryRunner | None = None,
    strategy_audit_db_history_runner: StrategyAuditDbHistoryRunner | None = None,
    strategy_recommendation_history_runner: (
        StrategyRecommendationHistoryRunner | None
    ) = None,
    cost_audit_runner: CostAuditRunner | None = None,
    cost_audit_db_trend_runner: CostAuditDbTrendRunner | None = None,
    outcome_tracking_db_history_runner: OutcomeTrackingDbHistoryRunner | None = None,
    nav_snapshot_db_trend_runner: NavSnapshotDbTrendRunner | None = None,
    strategy_evidence_runner: StrategyEvidenceRunner | None = None,
    observability_trends_runner: ObservabilityTrendsRunner = (
        run_local_observability_trends
    ),
    local_observability_trends_db_history_runner: (
        LocalObservabilityTrendsDbHistoryRunner | None
    ) = None,
    local_observability_trends_db_sink: LocalObservabilityTrendsDbSink | None = None,
    cycle_snapshot_source: CycleSnapshotSource | None = None,
    cycle_snapshot_db_sink: CycleSnapshotDbSink = (
        insert_paper_recommendation_cycle_snapshot_with_psycopg
    ),
    action_gated_queue_source: ActionGatedQueueSource | None = None,
    action_gated_queue_db_sink: ActionGatedQueueDbSink = (
        insert_paper_action_gated_strategy_recommendation_queue_report_with_psycopg
    ),
    action_gated_queue_history_db_sink: ActionGatedQueueHistoryDbSink | None = None,
    action_gated_queue_loader: ActionGatedQueueLoader | None = None,
    action_gated_queue_priority_builder: (
        ActionGatedQueuePriorityBuilder | None
    ) = None,
    action_gated_queue_risk_builder: ActionGatedQueueRiskBuilder | None = None,
    action_gated_queue_history_builder: (
        ActionGatedQueueHistoryBuilder | None
    ) = None,
    action_gated_queue_history_db_history_runner: (
        ActionGatedQueueHistoryDbHistoryRunner | None
    ) = None,
    cycle_snapshot_db_trend_runner: CycleSnapshotDbTrendRunner | None = None,
    cycle_snapshot_db_review_runner: CycleSnapshotDbReviewRunner | None = None,
    cycle_snapshot_db_action_gate_runner: CycleSnapshotDbActionGateRunner | None = None,
    action_gated_queue_decision_support_trend_runner: (
        ActionGatedQueueDecisionSupportTrendRunner | None
    ) = None,
    action_gated_queue_decision_support_trend_db_history_runner: (
        ActionGatedQueueDecisionSupportTrendDbHistoryRunner | None
    ) = None,
    strategy_candidate_research_queue_loader: (
        StrategyCandidateResearchQueueLoader | None
    ) = None,
    strategy_candidate_research_queue_history_builder: (
        StrategyCandidateResearchQueueHistoryBuilder | None
    ) = None,
    strategy_candidate_research_queue_history_db_sink: (
        StrategyCandidateResearchQueueHistoryDbSink | None
    ) = None,
    paper_research_packet_builder: PaperResearchPacketBuilder | None = None,
    paper_research_packet_db_sink: PaperResearchPacketDbSink | None = None,
    paper_research_packet_db_history_runner: (
        PaperResearchPacketDbHistoryRunner | None
    ) = None,
    paper_research_packet_quality_runner: PaperResearchPacketQualityRunner | None = None,
    paper_research_packet_quality_db_history_runner: (
        PaperResearchPacketQualityDbHistoryRunner | None
    ) = None,
    paper_research_packet_operator_flow_db_sink: (
        PaperResearchPacketOperatorFlowDbSink | None
    ) = None,
    paper_research_packet_operator_flow_db_history_runner: (
        PaperResearchPacketOperatorFlowDbHistoryRunner | None
    ) = None,
    paper_research_packet_operator_flow_db_history_gate_runner: (
        PaperResearchPacketOperatorFlowDbHistoryGateRunner | None
    ) = None,
    paper_autonomous_screening_decision_support_gate_runner: (
        PaperAutonomousScreeningDecisionSupportGateRunner | None
    ) = None,
    paper_autonomous_screening_decision_support_gate_db_sink: (
        PaperAutonomousScreeningDecisionSupportGateDbSink | None
    ) = None,
    paper_autonomous_allocation_proposal_runner: (
        PaperAutonomousAllocationProposalRunner | None
    ) = None,
    paper_autonomous_allocation_proposal_db_history_runner: (
        PaperAutonomousAllocationProposalDbHistoryRunner | None
    ) = None,
    paper_autonomous_allocation_proposal_db_history_gate_runner: (
        PaperAutonomousAllocationProposalDbHistoryGateRunner | None
    ) = None,
    paper_autonomous_allocation_proposal_db_history_health_runner: (
        PaperAutonomousAllocationProposalDbHistoryHealthRunner | None
    ) = None,
    paper_autonomous_allocation_proposal_db_history_metrics_runner: (
        PaperAutonomousAllocationProposalDbHistoryMetricsRunner | None
    ) = None,
    paper_autonomous_allocation_proposal_db_history_metrics_evaluation_runner: (
        PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationRunner | None
    ) = None,
    paper_autonomous_allocation_proposal_db_history_health_db_sink: (
        PaperAutonomousAllocationProposalDbHistoryHealthDbSink | None
    ) = None,
    paper_autonomous_allocation_proposal_db_history_health_trend_runner: (
        PaperAutonomousAllocationProposalDbHistoryHealthTrendRunner | None
    ) = None,
    paper_autonomous_allocation_proposal_db_history_health_trend_gate_runner: (
        PaperAutonomousAllocationProposalDbHistoryHealthTrendGateRunner | None
    ) = None,
    paper_autonomous_allocation_proposal_db_sink: (
        PaperAutonomousAllocationProposalDbSink | None
    ) = None,
    paper_execution_pipeline_runner: (
        PaperExecutionPipelineRunner | None
    ) = None,
    paper_execution_pipeline_persister: (
        PaperExecutionPipelinePersister | None
    ) = None,
    paper_autonomous_investment_ledger_runner: (
        PaperAutonomousInvestmentLedgerRunner | None
    ) = None,
    paper_autonomous_investment_ledger_db_sink: (
        PaperAutonomousInvestmentLedgerDbSink | None
    ) = None,
    paper_autonomous_investment_ledger_db_history_runner: (
        PaperAutonomousInvestmentLedgerDbHistoryRunner | None
    ) = None,
    paper_autonomous_investment_ledger_db_history_health_runner: (
        PaperAutonomousInvestmentLedgerDbHistoryHealthRunner | None
    ) = None,
    paper_autonomous_investment_ledger_db_history_health_trend_runner: (
        PaperAutonomousInvestmentLedgerDbHistoryHealthTrendRunner | None
    ) = None,
    paper_autonomous_investment_ledger_db_history_health_trend_gate_runner: (
        PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateRunner | None
    ) = None,
    paper_autonomous_readiness_digest_runner: (
        PaperAutonomousReadinessDigestRunner | None
    ) = None,
    paper_autonomous_readiness_digest_db_sink: (
        PaperAutonomousReadinessDigestDbSink | None
    ) = None,
    paper_probability_recommendation_queue_db_sink: (
        PaperProbabilityRecommendationQueueDbSink | None
    ) = None,
    paper_recommendation_risk_budget_db_sink: (
        PaperRecommendationRiskBudgetDbSink | None
    ) = None,
    paper_recommendation_reason_trend_db_sink: (
        PaperRecommendationReasonTrendDbSink | None
    ) = None,
    paper_probability_selection_summary_history_runner: (
        PaperProbabilitySelectionSummaryHistoryRunner | None
    ) = None,
    paper_probability_selection_summary_history_db_sink: (
        PaperProbabilitySelectionSummaryHistoryDbSink | None
    ) = None,
    paper_probability_selection_summary_history_trend_runner: (
        PaperProbabilitySelectionSummaryHistoryTrendRunner | None
    ) = None,
    autonomous_market_scorer_history_runner: (
        AutonomousMarketScorerHistoryRunner | None
    ) = None,
    probability_selection_scorer_agreement_runner: (
        ProbabilitySelectionScorerAgreementRunner | None
    ) = None,
    probability_selection_scorer_agreement_db_sink: (
        ProbabilitySelectionScorerAgreementDbSink | None
    ) = None,
    probability_selection_scorer_agreement_trend_runner: (
        ProbabilitySelectionScorerAgreementTrendRunner | None
    ) = None,
    probability_selection_scorer_agreement_trend_gate_runner: (
        ProbabilitySelectionScorerAgreementTrendGateRunner | None
    ) = None,
) -> int:
    parser = argparse.ArgumentParser(prog="polymarket-alpha-lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan")
    scan.add_argument("--limit", type=int, default=25)
    scan.add_argument("--archive-root", type=Path, default=Path("data/raw"))
    scan.add_argument("--output", type=Path, default=Path("artifacts/market-scores.json"))
    scan.add_argument("--no-books", action="store_true")

    cycle = subparsers.add_parser("strategy-cycle")
    cycle.add_argument("--limit", type=int, default=25)
    cycle.add_argument("--archive-root", type=Path, default=Path("data/raw"))
    cycle.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/strategy-cycle.jsonl"),
    )
    cycle.add_argument("--max-markets", type=int, default=50)
    cycle.add_argument("--search", default=None, dest="market_search")
    cycle.add_argument(
        "--prefilter",
        action=argparse.BooleanOptionalAction,
        default=True,
        dest="prefilter",
    )
    # Stage 8: --forecast-provider selects the per-market forecast model.
    # --llm-api-token is caller-supplied (never read from env/disk); it is
    # threaded into a GLMChatTransport only when the provider is "llm".
    cycle.add_argument(
        "--forecast-provider",
        choices=("naive", "book_imbalance", "llm"),
        default="naive",
        dest="forecast_provider",
    )
    cycle.add_argument(
        "--llm-api-token",
        default=None,
        dest="llm_api_token",
    )
    # Stage 4 (default-off): --paper-execute turns on the inline paper-execution
    # pass inside run_strategy_cycle; --paper-journal selects the JSONL sink.
    cycle.add_argument(
        "--paper-execute",
        action="store_true",
        dest="paper_execute",
    )
    cycle.add_argument(
        "--paper-journal",
        type=Path,
        default=Path("artifacts/paper-trades.jsonl"),
        dest="paper_journal",
    )

    nav = subparsers.add_parser("portfolio-nav")
    nav.add_argument(
        "--journal",
        type=Path,
        default=Path("artifacts/paper-trades.jsonl"),
        dest="journal",
    )
    nav.add_argument(
        "--starting-cash",
        type=Decimal,
        default=None,
        dest="starting_cash",
    )
    nav.add_argument(
        "--nav-log",
        type=Path,
        default=None,
        dest="nav_log",
    )

    nav_risk = subparsers.add_parser("nav-risk")
    nav_risk.add_argument(
        "--nav-log",
        type=Path,
        required=True,
        dest="nav_log",
    )
    nav_snapshot_db_trend = subparsers.add_parser("nav-snapshot-db-trend")
    nav_snapshot_db_trend.add_argument(
        "--limit",
        type=int,
        default=100,
    )

    cost_audit = subparsers.add_parser("cost-audit")
    cost_audit.add_argument(
        "--trade-log",
        type=Path,
        required=True,
        dest="trade_log",
    )
    cost_audit.add_argument(
        "--persist",
        action="store_true",
        default=False,
        dest="persist",
    )
    cost_audit_db_trend = subparsers.add_parser("cost-audit-db-trend")
    cost_audit_db_trend.add_argument(
        "--limit",
        type=int,
        default=100,
    )

    history = subparsers.add_parser("history")
    history.add_argument(
        "--cycle-log",
        type=Path,
        required=True,
        dest="cycle_log",
    )
    history.add_argument(
        "--trade-log",
        type=Path,
        required=True,
        dest="trade_log",
    )
    history.add_argument(
        "--nav-log",
        type=Path,
        required=True,
        dest="nav_log",
    )

    strategy_audit = subparsers.add_parser("strategy-audit")
    strategy_audit.add_argument(
        "--cycle-log",
        type=Path,
        required=True,
        dest="cycle_log",
    )
    strategy_audit.add_argument(
        "--trade-log",
        type=Path,
        required=True,
        dest="trade_log",
    )
    strategy_audit.add_argument(
        "--nav-log",
        type=Path,
        required=True,
        dest="nav_log",
    )
    strategy_audit.add_argument(
        "--outcome-log",
        type=Path,
        default=None,
        dest="outcome_log",
    )
    strategy_audit.add_argument(
        "--strategy-audit-log",
        type=Path,
        default=None,
        dest="strategy_audit_log",
    )
    strategy_audit.add_argument(
        "--persist",
        action="store_true",
        default=False,
        dest="persist",
    )

    strategy_audit_history = subparsers.add_parser("strategy-audit-history")
    strategy_audit_history.add_argument(
        "--strategy-audit-log",
        type=Path,
        required=True,
        dest="strategy_audit_log",
    )
    strategy_cycle_db_history = subparsers.add_parser("strategy-cycle-db-history")
    strategy_cycle_db_history.add_argument("--source-config-version", default=None)
    strategy_cycle_db_history.add_argument(
        "--limit",
        type=int,
        default=50,
    )
    strategy_cycle_history_gate = subparsers.add_parser(
        "strategy-cycle-history-gate",
        allow_abbrev=False,
    )
    strategy_cycle_history_gate.add_argument("--source-config-version", default=None)
    strategy_cycle_history_gate.add_argument(
        "--limit",
        type=int,
        default=50,
    )
    strategy_cycle_history_gate.add_argument(
        "--persist",
        action="store_true",
        default=False,
        dest="persist",
    )
    strategy_audit_db_history = subparsers.add_parser("strategy-audit-db-history")
    strategy_audit_db_history.add_argument(
        "--limit",
        type=int,
        default=100,
    )

    strategy_recommendation_history = subparsers.add_parser(
        "strategy-recommendation-history",
    )
    strategy_recommendation_history.add_argument(
        "--recommendation-log",
        type=Path,
        required=True,
        dest="recommendation_log",
    )
    paper_recommendation_reason_trend = subparsers.add_parser(
        "paper-recommendation-reason-trend",
    )
    paper_recommendation_reason_trend.add_argument(
        "--recommendation-log",
        type=Path,
        required=True,
        dest="recommendation_log",
    )
    paper_recommendation_reason_trend.add_argument(
        "--persist",
        action="store_true",
        default=False,
        dest="persist",
    )
    paper_probability_side_edge_report = subparsers.add_parser(
        "paper-probability-side-edge-report",
    )
    paper_probability_side_edge_report.add_argument(
        "--input",
        type=Path,
        required=True,
        dest="input_path",
    )
    paper_recommendation_queue_report = subparsers.add_parser(
        "paper-recommendation-queue-report",
    )
    paper_recommendation_queue_report.add_argument(
        "--input",
        type=Path,
        required=True,
        dest="input_path",
    )
    paper_recommendation_queue_report.add_argument(
        "--persist",
        action="store_true",
        default=False,
        dest="persist",
    )
    paper_recommendation_risk_budget_report = subparsers.add_parser(
        "paper-recommendation-risk-budget-report",
    )
    paper_recommendation_risk_budget_report.add_argument(
        "--input",
        type=Path,
        required=True,
        dest="input_path",
    )
    paper_recommendation_risk_budget_report.add_argument(
        "--nav-notional",
        type=_cli_decimal,
        default=None,
        dest="nav_notional",
    )
    paper_recommendation_risk_budget_report.add_argument(
        "--persist",
        action="store_true",
        default=False,
        dest="persist",
    )
    paper_probability_selection_summary_history = subparsers.add_parser(
        "paper-probability-selection-summary-history",
        allow_abbrev=False,
    )
    paper_probability_selection_summary_history.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )
    paper_probability_selection_summary_history.add_argument(
        "--persist",
        action="store_true",
        default=False,
        dest="persist",
    )
    paper_probability_selection_summary_history_trend = subparsers.add_parser(
        "paper-probability-selection-summary-history-trend",
        allow_abbrev=False,
    )
    paper_probability_selection_summary_history_trend.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )
    autonomous_market_scorer_history = subparsers.add_parser(
        "autonomous-market-scorer-history",
        allow_abbrev=False,
    )
    autonomous_market_scorer_history.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )
    probability_selection_scorer_agreement = subparsers.add_parser(
        "probability-selection-scorer-agreement",
        allow_abbrev=False,
        description=(
            "Build a read-only, report-only agreement report from local "
            "Supabase/Postgres probability selection and scorer snapshots."
        ),
        help="read-only report-only probability selection/scorer agreement",
    )
    probability_selection_scorer_agreement.add_argument(
        "--limit",
        type=int,
        default=1,
        dest="limit",
    )
    probability_selection_scorer_agreement_trend = subparsers.add_parser(
        "probability-selection-scorer-agreement-trend",
        allow_abbrev=False,
        description=(
            "Build a read-only, report-only trend report from local "
            "Supabase/Postgres probability selection/scorer agreement snapshots."
        ),
        help="read-only report-only probability selection/scorer agreement trend",
    )
    probability_selection_scorer_agreement_trend.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )
    probability_selection_scorer_agreement_trend_gate = subparsers.add_parser(
        "probability-selection-scorer-agreement-trend-gate",
        allow_abbrev=False,
        description=(
            "Build a read-only, report-only trend-gate report from local "
            "Supabase/Postgres probability selection/scorer agreement snapshots."
        ),
        help="read-only report-only probability selection/scorer agreement trend gate",
    )
    probability_selection_scorer_agreement_trend_gate.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )

    strategy_evidence = subparsers.add_parser("strategy-evidence")
    strategy_evidence.add_argument(
        "--cycle-log",
        type=Path,
        required=True,
        dest="cycle_log",
    )
    strategy_evidence.add_argument(
        "--trade-log",
        type=Path,
        required=True,
        dest="trade_log",
    )
    strategy_evidence.add_argument(
        "--nav-log",
        type=Path,
        required=True,
        dest="nav_log",
    )
    strategy_evidence.add_argument(
        "--outcome-log",
        type=Path,
        default=None,
        dest="outcome_log",
    )
    strategy_evidence.add_argument(
        "--strategy-audit-log",
        type=Path,
        default=None,
        dest="strategy_audit_log",
    )

    observability_trends = subparsers.add_parser("observability-trends")
    observability_trends.add_argument(
        "--cycle-log",
        type=Path,
        required=True,
        dest="cycle_log",
    )
    observability_trends.add_argument(
        "--trade-log",
        type=Path,
        required=True,
        dest="trade_log",
    )
    observability_trends.add_argument(
        "--nav-log",
        type=Path,
        required=True,
        dest="nav_log",
    )
    observability_trends.add_argument(
        "--outcome-log",
        type=Path,
        default=None,
        dest="outcome_log",
    )
    observability_trends.add_argument(
        "--strategy-audit-log",
        type=Path,
        default=None,
        dest="strategy_audit_log",
    )
    observability_trends.add_argument(
        "--outcome-stale-after-seconds",
        type=int,
        default=86_400,
        dest="outcome_stale_after_seconds",
    )
    observability_trends.add_argument(
        "--persist",
        action="store_true",
        default=False,
        dest="persist",
    )

    local_observability_trends_db_history = subparsers.add_parser(
        "local-observability-trends-db-history",
    )
    local_observability_trends_db_history.add_argument(
        "--limit",
        type=int,
        default=100,
    )

    cycle_snapshot_db_trend = subparsers.add_parser("cycle-snapshot-db-trend")
    cycle_snapshot_db_trend.add_argument(
        "--source-config-version",
        default=None,
        dest="source_config_version",
    )
    cycle_snapshot_db_trend.add_argument("--limit", type=int, default=50)

    cycle_snapshot_review = subparsers.add_parser(
        "paper-recommendation-cycle-review",
    )
    cycle_snapshot_review.add_argument(
        "--source-config-version",
        default=None,
        dest="source_config_version",
    )
    cycle_snapshot_review.add_argument("--limit", type=int, default=50)
    cycle_snapshot_review.add_argument(
        "--stale-after-hours",
        type=Decimal,
        default=Decimal("6.000000"),
        dest="stale_after_hours",
    )

    cycle_snapshot_action_gate = subparsers.add_parser(
        "paper-recommendation-cycle-action-gate",
    )
    cycle_snapshot_action_gate.add_argument(
        "--source-config-version",
        default=None,
        dest="source_config_version",
    )
    cycle_snapshot_action_gate.add_argument("--limit", type=int, default=50)
    cycle_snapshot_action_gate.add_argument(
        "--stale-after-hours",
        type=Decimal,
        default=Decimal("6.000000"),
        dest="stale_after_hours",
    )

    action_gated_queue_decision_support = subparsers.add_parser(
        "action-gated-queue-decision-support",
    )
    action_gated_queue_decision_support.add_argument(
        "--source-config-version",
        default=None,
        dest="source_config_version",
    )
    action_gated_queue_decision_support.add_argument(
        "--action-status",
        choices=("research_ready", "watch", "blocked"),
        default=None,
        dest="action_status",
    )
    action_gated_queue_decision_support.add_argument(
        "--limit",
        type=int,
        default=100,
    )
    action_gated_queue_decision_support.add_argument(
        "--max-total-ready-notional",
        type=Decimal,
        default=Decimal("1000.000000"),
        dest="max_total_ready_notional",
    )
    action_gated_queue_decision_support.add_argument(
        "--max-single-queue-ready-notional",
        type=Decimal,
        default=Decimal("250.000000"),
        dest="max_single_queue_ready_notional",
    )
    action_gated_queue_decision_support.add_argument(
        "--max-ready-candidate-count",
        type=int,
        default=25,
        dest="max_ready_candidate_count",
    )
    action_gated_queue_decision_support.add_argument(
        "--max-total-candidate-count",
        type=int,
        default=100,
        dest="max_total_candidate_count",
    )
    action_gated_queue_decision_support.add_argument(
        "--throttle-utilization-threshold",
        type=Decimal,
        default=Decimal("0.800000"),
        dest="throttle_utilization_threshold",
    )

    action_gated_queue_decision_support_trend = subparsers.add_parser(
        "action-gated-queue-decision-support-trend",
    )
    action_gated_queue_decision_support_trend.add_argument(
        "--source-limit",
        type=int,
        default=50,
        dest="source_limit",
    )
    action_gated_queue_decision_support_trend.add_argument(
        "--source-risk-status",
        choices=("pass", "watch", "blocked"),
        default=None,
        dest="source_risk_status",
    )
    action_gated_queue_decision_support_trend.add_argument(
        "--persist",
        action="store_true",
        default=False,
        dest="persist",
    )
    action_gated_queue_decision_support_trend_db_history = subparsers.add_parser(
        "action-gated-queue-decision-support-trend-db-history",
    )
    action_gated_queue_decision_support_trend_db_history.add_argument(
        "--limit",
        type=int,
        default=100,
    )
    action_gated_queue_decision_support_trend_db_history.add_argument(
        "--latest-risk-status",
        choices=("pass", "watch", "blocked"),
        default=None,
        dest="latest_risk_status",
    )

    action_gated_queue_history = subparsers.add_parser(
        "action-gated-queue-history",
    )
    action_gated_queue_history.add_argument(
        "--source-config-version",
        default=None,
        dest="source_config_version",
    )
    action_gated_queue_history.add_argument(
        "--action-status",
        choices=("research_ready", "watch", "blocked"),
        default=None,
        dest="action_status",
    )
    action_gated_queue_history.add_argument(
        "--limit",
        type=int,
        default=100,
    )
    action_gated_queue_history.add_argument(
        "--persist",
        action="store_true",
        default=False,
        dest="persist",
    )
    action_gated_queue_history_db_history = subparsers.add_parser(
        "action-gated-queue-history-db-history",
    )
    action_gated_queue_history_db_history.add_argument(
        "--limit",
        type=int,
        default=100,
        dest="limit",
    )
    action_gated_queue_history_db_history.add_argument(
        "--latest-action-status",
        choices=("research_ready", "watch", "blocked"),
        default=None,
        dest="latest_action_status",
    )

    strategy_candidate_research_queue_history = subparsers.add_parser(
        "strategy-candidate-research-queue-history",
    )
    strategy_candidate_research_queue_history.add_argument(
        "--source-config-version",
        default=None,
        dest="source_config_version",
    )
    strategy_candidate_research_queue_history.add_argument(
        "--action-status",
        choices=("research_ready", "watch", "blocked"),
        default=None,
        dest="action_status",
    )
    strategy_candidate_research_queue_history.add_argument(
        "--research-status",
        choices=("ready", "watch", "blocked"),
        default=None,
        dest="research_status",
    )
    strategy_candidate_research_queue_history.add_argument(
        "--limit",
        type=int,
        default=100,
    )
    strategy_candidate_research_queue_history.add_argument(
        "--persist",
        action="store_true",
        default=False,
        dest="persist",
    )
    paper_research_packet = subparsers.add_parser("paper-research-packet")
    paper_research_packet.add_argument(
        "--source-config-version",
        default=None,
        dest="source_config_version",
    )
    paper_research_packet.add_argument(
        "--action-status",
        choices=("research_ready", "watch", "blocked"),
        default=None,
        dest="action_status",
    )
    paper_research_packet.add_argument(
        "--research-status",
        choices=("ready", "watch", "blocked"),
        default=None,
        dest="research_status",
    )
    paper_research_packet.add_argument("--limit", type=int, default=100)
    paper_research_packet.add_argument(
        "--packet-config-version",
        default=DEFAULT_PAPER_RESEARCH_PACKET_CONFIG_VERSION,
        dest="packet_config_version",
    )
    paper_research_packet.add_argument(
        "--max-packet-rows",
        type=int,
        default=DEFAULT_PAPER_RESEARCH_PACKET_MAX_PACKET_ROWS,
        dest="max_packet_rows",
    )
    paper_research_packet.add_argument(
        "--min-score",
        type=_cli_decimal,
        default=DEFAULT_PAPER_RESEARCH_PACKET_MIN_SCORE,
        dest="min_score",
    )
    paper_research_packet.add_argument(
        "--persist",
        action="store_true",
        default=False,
        dest="persist",
    )
    paper_research_packet_db_history = subparsers.add_parser(
        "paper-research-packet-db-history",
    )
    paper_research_packet_db_history.add_argument(
        "--limit",
        type=int,
        default=100,
        dest="limit",
    )
    paper_research_packet_quality = subparsers.add_parser(
        "paper-research-packet-quality",
    )
    paper_research_packet_quality.add_argument(
        "--persist",
        action="store_true",
        default=False,
        dest="persist",
    )
    paper_research_packet_quality_db_history = subparsers.add_parser(
        "paper-research-packet-quality-db-history",
    )
    paper_research_packet_quality_db_history.add_argument(
        "--limit",
        type=int,
        default=100,
        dest="limit",
    )
    paper_research_packet_operator_flow_db_history = subparsers.add_parser(
        "paper-research-packet-operator-flow-db-history",
    )
    paper_research_packet_operator_flow_db_history.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )
    paper_research_packet_operator_flow_db_history_gate = subparsers.add_parser(
        "paper-research-packet-operator-flow-db-history-gate",
    )
    paper_research_packet_operator_flow_db_history_gate.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )
    paper_autonomous_screening_decision_support_gate = subparsers.add_parser(
        "paper-autonomous-screening-decision-support-gate",
    )
    paper_autonomous_screening_decision_support_gate.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )
    paper_autonomous_screening_decision_support_gate_persist = subparsers.add_parser(
        "paper-autonomous-screening-decision-support-gate-persist",
    )
    paper_autonomous_screening_decision_support_gate_persist.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )
    paper_autonomous_allocation_proposal = subparsers.add_parser(
        "paper-autonomous-allocation-proposal",
    )
    paper_autonomous_allocation_proposal.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )
    paper_autonomous_allocation_proposal_persist = subparsers.add_parser(
        "paper-autonomous-allocation-proposal-persist",
    )
    paper_autonomous_allocation_proposal_persist.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )
    paper_autonomous_allocation_proposal_db_history = subparsers.add_parser(
        "paper-autonomous-allocation-proposal-db-history",
    )
    paper_autonomous_allocation_proposal_db_history.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )
    paper_autonomous_allocation_proposal_db_history_gate = subparsers.add_parser(
        "paper-autonomous-allocation-proposal-db-history-gate",
    )
    paper_autonomous_allocation_proposal_db_history_gate.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )
    paper_autonomous_allocation_proposal_db_history_metrics = subparsers.add_parser(
        "paper-autonomous-allocation-proposal-db-history-metrics",
        allow_abbrev=False,
    )
    paper_autonomous_allocation_proposal_db_history_metrics.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )
    paper_autonomous_allocation_proposal_db_history_metrics_evaluation = subparsers.add_parser(
        "paper-autonomous-allocation-proposal-db-history-metrics-evaluation",
        allow_abbrev=False,
    )
    paper_autonomous_allocation_proposal_db_history_metrics_evaluation.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )
    paper_autonomous_allocation_proposal_db_history_health = subparsers.add_parser(
        "paper-autonomous-allocation-proposal-db-history-health",
        allow_abbrev=False,
    )
    paper_autonomous_allocation_proposal_db_history_health.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )
    paper_autonomous_allocation_proposal_db_history_health.add_argument(
        "--persist",
        action="store_true",
        default=False,
        dest="persist",
    )
    paper_autonomous_allocation_proposal_db_history_health_trend = subparsers.add_parser(
        "paper-autonomous-allocation-proposal-db-history-health-trend",
        allow_abbrev=False,
    )
    paper_autonomous_allocation_proposal_db_history_health_trend.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )
    paper_autonomous_allocation_proposal_db_history_health_trend_gate = (
        subparsers.add_parser(
            "paper-autonomous-allocation-proposal-db-history-health-trend-gate",
            allow_abbrev=False,
        )
    )
    paper_autonomous_allocation_proposal_db_history_health_trend_gate.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )
    paper_execution_pipeline = subparsers.add_parser(
        "paper-execution-pipeline",
        allow_abbrev=False,
    )
    paper_execution_pipeline.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )
    paper_execution_pipeline_persist = subparsers.add_parser(
        "paper-execution-pipeline-persist",
        allow_abbrev=False,
    )
    paper_execution_pipeline_persist.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )
    paper_execution_pipeline_db_history = subparsers.add_parser(
        "paper-execution-pipeline-db-history",
        allow_abbrev=False,
    )
    paper_execution_pipeline_db_history.add_argument(
        "--limit",
        type=int,
        default=100,
        dest="limit",
    )
    paper_autonomous_investment_ledger = subparsers.add_parser(
        "paper-autonomous-investment-ledger",
        allow_abbrev=False,
    )
    paper_autonomous_investment_ledger.add_argument(
        "--limit",
        type=int,
        default=100,
        dest="limit",
    )
    paper_autonomous_investment_ledger.add_argument(
        "--source-config-version",
        default=None,
        dest="source_config_version",
    )
    paper_autonomous_investment_ledger.add_argument(
        "--execution-status",
        choices=("paper_submitted", "paper_held", "paper_blocked"),
        default=None,
        dest="execution_status",
    )
    paper_autonomous_investment_ledger.add_argument(
        "--source-gate-status",
        choices=("pass", "watch", "blocked"),
        default=None,
        dest="source_gate_status",
    )
    paper_autonomous_investment_ledger.add_argument(
        "--max-latest-source-age-seconds",
        type=int,
        default=86_400,
        dest="max_latest_source_age_seconds",
    )
    paper_autonomous_investment_ledger.add_argument(
        "--persist",
        action="store_true",
        default=False,
        dest="persist",
    )
    paper_autonomous_investment_ledger_db_history = subparsers.add_parser(
        "paper-autonomous-investment-ledger-db-history",
        allow_abbrev=False,
    )
    paper_autonomous_investment_ledger_db_history.add_argument(
        "--limit",
        type=int,
        default=100,
        dest="limit",
    )
    paper_autonomous_investment_ledger_db_history.add_argument(
        "--config-version",
        default=None,
        dest="config_version",
    )
    paper_autonomous_investment_ledger_db_history.add_argument(
        "--ledger-status",
        choices=("pass", "watch", "blocked"),
        default=None,
        dest="ledger_status",
    )
    paper_autonomous_investment_ledger_db_history_health = subparsers.add_parser(
        "paper-autonomous-investment-ledger-db-history-health",
        allow_abbrev=False,
    )
    paper_autonomous_investment_ledger_db_history_health.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )
    paper_autonomous_investment_ledger_db_history_health_trend = (
        subparsers.add_parser(
            "paper-autonomous-investment-ledger-db-history-health-trend",
            allow_abbrev=False,
        )
    )
    paper_autonomous_investment_ledger_db_history_health_trend.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )
    paper_autonomous_investment_ledger_db_history_health_trend_gate = (
        subparsers.add_parser(
            "paper-autonomous-investment-ledger-db-history-health-trend-gate",
            allow_abbrev=False,
        )
    )
    paper_autonomous_investment_ledger_db_history_health_trend_gate.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )
    paper_autonomous_readiness_digest = subparsers.add_parser(
        "paper-autonomous-readiness-digest",
        allow_abbrev=False,
    )
    paper_autonomous_readiness_digest.add_argument(
        "--limit",
        type=int,
        default=25,
        dest="limit",
    )
    paper_autonomous_readiness_digest.add_argument(
        "--persist",
        action="store_true",
        default=False,
        dest="persist",
    )

    paper_research_packet_operator_flow = subparsers.add_parser(
        "paper-research-packet-operator-flow",
    )
    paper_research_packet_operator_flow.add_argument(
        "--source-config-version",
        default=None,
        dest="source_config_version",
    )
    paper_research_packet_operator_flow.add_argument(
        "--action-status",
        choices=("research_ready", "watch", "blocked"),
        default=None,
        dest="action_status",
    )
    paper_research_packet_operator_flow.add_argument(
        "--research-status",
        choices=("ready", "watch", "blocked"),
        default=None,
        dest="research_status",
    )
    paper_research_packet_operator_flow.add_argument(
        "--limit",
        type=int,
        default=100,
        dest="limit",
    )
    paper_research_packet_operator_flow.add_argument(
        "--packet-config-version",
        default=DEFAULT_PAPER_RESEARCH_PACKET_CONFIG_VERSION,
        dest="packet_config_version",
    )
    paper_research_packet_operator_flow.add_argument(
        "--max-packet-rows",
        type=int,
        default=DEFAULT_PAPER_RESEARCH_PACKET_MAX_PACKET_ROWS,
        dest="max_packet_rows",
    )
    paper_research_packet_operator_flow.add_argument(
        "--min-score",
        type=_cli_decimal,
        default=DEFAULT_PAPER_RESEARCH_PACKET_MIN_SCORE,
        dest="min_score",
    )
    paper_research_packet_operator_flow.add_argument(
        "--quality-history-limit",
        type=int,
        default=100,
        dest="quality_history_limit",
    )

    # Stage 17 market search: search Polymarket markets by keyword.
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument(
        "--query", required=True, dest="query",
    )
    search_parser.add_argument("--limit", type=int, default=25)
    search_parser.add_argument("--closed", action="store_true")

    # Stage 9 outcome tracker: re-list closed markets from Gamma and build a
    # forecast-evidence calibration report over resolved paper-trade legs.
    check_outcomes_parser = subparsers.add_parser("check-outcomes")
    check_outcomes_parser.add_argument(
        "--journal",
        type=Path,
        default=Path("artifacts/paper-trades.jsonl"),
        dest="journal",
    )
    check_outcomes_parser.add_argument(
        "--evidence-log",
        type=Path,
        default=None,
        dest="evidence_log",
    )
    check_outcomes_parser.add_argument(
        "--outcome-log",
        type=Path,
        default=None,
        dest="outcome_log",
    )
    outcome_tracking_db_history = subparsers.add_parser(
        "outcome-tracking-db-history",
    )
    outcome_tracking_db_history.add_argument(
        "--limit",
        type=int,
        default=100,
    )
    outcome_tracking_db_history.add_argument(
        "--stale-after-seconds",
        type=int,
        default=86_400,
        dest="stale_after_seconds",
    )

    # Stage 7 continuous run: chains strategy-cycle + paper-execute + portfolio-nav.
    run_loop = subparsers.add_parser("run")
    run_loop.add_argument("--limit", type=int, default=25)
    run_loop.add_argument("--archive-root", type=Path, default=Path("data/raw"))
    run_loop.add_argument("--max-markets", type=int, default=50)
    run_loop.add_argument(
        "--prefilter",
        action=argparse.BooleanOptionalAction,
        default=True,
        dest="prefilter",
    )
    run_loop.add_argument(
        "--forecast-provider",
        choices=("naive", "book_imbalance", "llm"),
        default="naive",
        dest="forecast_provider",
    )
    run_loop.add_argument(
        "--llm-api-token",
        default=None,
        dest="llm_api_token",
    )
    run_loop.add_argument(
        "--paper-execute",
        action="store_true",
        dest="paper_execute",
    )
    run_loop.add_argument(
        "--paper-journal",
        type=Path,
        default=Path("artifacts/paper-trades.jsonl"),
        dest="paper_journal",
    )
    run_loop.add_argument(
        "--starting-cash",
        type=Decimal,
        default=None,
        dest="starting_cash",
    )
    run_loop.add_argument(
        "--cycle-log",
        type=Path,
        default=Path("artifacts/strategy-cycle.jsonl"),
        dest="cycle_log",
    )
    run_loop.add_argument(
        "--nav-log",
        type=Path,
        default=None,
        dest="nav_log",
    )
    run_loop.add_argument(
        "--outcome-log",
        type=Path,
        default=None,
        dest="outcome_log",
    )
    run_loop.add_argument(
        "--strategy-audit-preflight",
        action=argparse.BooleanOptionalAction,
        default=None,
        dest="strategy_audit_preflight",
    )
    run_loop.add_argument(
        "--strategy-audit-log",
        type=Path,
        default=None,
        dest="strategy_audit_log",
    )
    run_loop.add_argument(
        "--repeat-interval",
        type=int,
        default=0,
        dest="repeat_interval",
    )
    run_loop.add_argument(
        "--max-iterations",
        type=int,
        default=1,
        dest="max_iterations",
    )
    run_loop.add_argument(
        "--config",
        type=Path,
        default=None,
        dest="config",
    )

    args = parser.parse_args(argv)
    _apply_json_config(args)
    if args.command == "run" and args.strategy_audit_preflight is None:
        args.strategy_audit_preflight = False

    if args.command == "scan":
        try:
            runner(
                client=client_factory(),
                config=MarketScanConfig(
                    limit=args.limit,
                    archive_root=args.archive_root,
                    output_path=args.output,
                    fetch_books=not args.no_books,
                ),
            )
            return 0
        except Exception as exc:
            print(f"scan failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "strategy-cycle":
        try:
            paper_strategy_cycle_report_db_config = (
                from_paper_strategy_cycle_report_db_env()
            )
            paper_trade_db_config = from_paper_trade_journal_db_env()
            strategy_cycle_report_sink = None
            if paper_strategy_cycle_report_db_config.enabled:
                dsn = paper_strategy_cycle_report_db_config.dsn
                if dsn is None:
                    raise ValueError(
                        "paper strategy cycle report DB persistence requires a DB DSN",
                    )

                def strategy_cycle_report_sink(
                    report: PaperStrategyCycleReport,
                    *,
                    db_dsn: str = dsn,
                    table_name: str = (
                        paper_strategy_cycle_report_db_config.table_name
                    ),
                ) -> object:
                    try:
                        return paper_strategy_cycle_report_db_sink(
                            dsn=db_dsn,
                            report=report,
                            table_name=table_name,
                        )
                    except Exception as exc:
                        _raise_redacted_db_sink_error(
                            exc,
                            dsn=db_dsn,
                            table_name=table_name,
                        )

            strategy_cycle_paper_trade_record_sink = None
            if paper_trade_db_config.enabled:
                dsn = paper_trade_db_config.dsn
                if dsn is None:
                    raise ValueError(
                        "paper trade journal DB persistence requires a DB DSN",
                    )

                def strategy_cycle_paper_trade_record_sink(
                    record: object,
                    *,
                    db_dsn: str = dsn,
                    table_name: str = paper_trade_db_config.table_name,
                ) -> object:
                    try:
                        return paper_trade_record_db_sink(
                            dsn=db_dsn,
                            record=record,
                            table_name=table_name,
                        )
                    except Exception as exc:
                        _raise_redacted_db_sink_error(exc, dsn=db_dsn)

            scan_config = MarketScanConfig(
                limit=args.limit,
                archive_root=args.archive_root,
                output_path=args.output,
                fetch_books=True,
            )
            cycle_config = _build_default_cycle_config(
                max_markets_per_cycle=args.max_markets,
                prefilter_by_score=args.prefilter,
                paper_execute=args.paper_execute,
                paper_journal=args.paper_journal,
                forecast_provider=args.forecast_provider,
                llm_api_token=args.llm_api_token,
            )
            if args.market_search is not None:
                cycle_config = replace(
                    cycle_config, market_search=args.market_search
                )
            cycle_runner_kwargs = {
                "client": client_factory(),
                "scan_config": scan_config,
                "cycle_config": cycle_config,
            }
            if strategy_cycle_paper_trade_record_sink is not None:
                cycle_runner_kwargs["paper_trade_record_sink"] = (
                    strategy_cycle_paper_trade_record_sink
                )
            report = cycle_runner(**cycle_runner_kwargs)
            PaperStrategyCycleLog(args.output).append(report)
            if strategy_cycle_report_sink is not None:
                strategy_cycle_report_sink(report)
            _print_strategy_cycle_summary(report)
            return 0
        except Exception as exc:
            print(f"strategy-cycle failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "portfolio-nav":
        try:
            paper_nav_db_config = from_paper_nav_snapshot_db_env()
            portfolio_nav_snapshot_sink = None
            if paper_nav_db_config.enabled:
                dsn = paper_nav_db_config.dsn
                if dsn is None:
                    raise ValueError(
                        "paper NAV snapshot DB persistence requires a DB DSN",
                    )

                def portfolio_nav_snapshot_sink(
                    snapshot: PaperNavSnapshot,
                    *,
                    db_dsn: str = dsn,
                    table_name: str = paper_nav_db_config.table_name,
                ) -> object:
                    try:
                        return paper_nav_snapshot_db_sink(
                            dsn=db_dsn,
                            snapshot=snapshot,
                            table_name=table_name,
                        )
                    except Exception as exc:
                        _raise_redacted_db_sink_error(exc, dsn=db_dsn)

            nav_runner_kwargs = {
                "journal_path": args.journal,
                "starting_cash": args.starting_cash,
                "client": client_factory(),
                "marked_at": datetime.now(UTC),
                "nav_log_path": args.nav_log,
            }
            if portfolio_nav_snapshot_sink is not None:
                nav_runner_kwargs["nav_snapshot_sink"] = portfolio_nav_snapshot_sink
            snapshot = nav_runner(**nav_runner_kwargs)
            _print_portfolio_nav_summary(snapshot)
            return 0
        except Exception as exc:
            print(f"portfolio-nav failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "nav-risk":
        try:
            report = _run_nav_risk(
                nav_log=args.nav_log,
                runner=nav_risk_runner,
            )
            _print_nav_risk_summary(report)
            return 0
        except Exception as exc:
            print(f"nav-risk failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "nav-snapshot-db-trend":
        try:
            if args.limit <= 0:
                raise ValueError("nav-snapshot-db-trend limit must be positive")
            paper_nav_db_config = from_paper_nav_snapshot_db_env()
            if not paper_nav_db_config.enabled:
                raise ValueError(
                    "nav-snapshot-db-trend requires paper NAV snapshot "
                    "DB to be enabled",
                )
            dsn = paper_nav_db_config.dsn
            if dsn is None:
                raise ValueError(
                    "nav-snapshot-db-trend requires a paper NAV snapshot "
                    "DB DSN",
                )
            try:
                report = _run_nav_snapshot_db_trend(
                    dsn=dsn,
                    table_name=paper_nav_db_config.table_name,
                    limit=args.limit,
                    runner=nav_snapshot_db_trend_runner,
                )
            except Exception as exc:
                _raise_redacted_db_read_error(exc, dsn=dsn)
            _print_nav_snapshot_db_trend_summary(report)
            return 0
        except Exception as exc:
            print(f"nav-snapshot-db-trend failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "cost-audit":
        try:
            cost_audit_report_sink = None
            if args.persist:
                paper_trade_cost_audit_db_config = from_paper_trade_cost_audit_db_env()
                if not paper_trade_cost_audit_db_config.enabled:
                    raise ValueError(
                        "cost-audit persistence requires paper trade cost audit "
                        "DB to be enabled",
                    )
                dsn = paper_trade_cost_audit_db_config.dsn
                if dsn is None:
                    raise ValueError(
                        "cost-audit persistence requires a paper trade cost "
                        "audit DB DSN",
                    )

                def cost_audit_report_sink(
                    report: PaperTradeCostAuditReport,
                    *,
                    db_dsn: str = dsn,
                    table_name: str = paper_trade_cost_audit_db_config.table_name,
                ) -> object:
                    try:
                        return paper_trade_cost_audit_db_sink(
                            dsn=db_dsn,
                            report=report,
                            table_name=table_name,
                        )
                    except Exception as exc:
                        _raise_redacted_db_sink_error(exc, dsn=db_dsn)

            report = _run_cost_audit(
                trade_log=args.trade_log,
                runner=cost_audit_runner,
            )
            if cost_audit_report_sink is not None:
                cost_audit_report_sink(report)
            _print_cost_audit_summary(report)
            return 0
        except Exception as exc:
            print(f"cost-audit failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "cost-audit-db-trend":
        try:
            if args.limit <= 0:
                raise ValueError("cost-audit-db-trend limit must be positive")
            paper_trade_cost_audit_db_config = from_paper_trade_cost_audit_db_env()
            if not paper_trade_cost_audit_db_config.enabled:
                raise ValueError(
                    "cost-audit-db-trend requires paper trade cost audit "
                    "DB to be enabled",
                )
            dsn = paper_trade_cost_audit_db_config.dsn
            if dsn is None:
                raise ValueError(
                    "cost-audit-db-trend requires a paper trade cost audit "
                    "DB DSN",
                )
            try:
                report = _run_cost_audit_db_trend(
                    dsn=dsn,
                    table_name=paper_trade_cost_audit_db_config.table_name,
                    limit=args.limit,
                    runner=cost_audit_db_trend_runner,
                )
            except Exception as exc:
                _raise_redacted_db_read_error(exc, dsn=dsn)
            _print_cost_audit_db_trend_summary(report)
            return 0
        except Exception as exc:
            print(f"cost-audit-db-trend failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "history":
        try:
            summary = _run_history(
                cycle_log=args.cycle_log,
                trade_log=args.trade_log,
                nav_log=args.nav_log,
                runner=history_runner,
            )
            _print_performance_summary(summary)
            return 0
        except Exception as exc:
            print(f"history failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "strategy-audit":
        try:
            strategy_audit_report_sink = None
            if args.persist:
                strategy_risk_audit_db_config = from_strategy_risk_audit_db_env()
                if not strategy_risk_audit_db_config.enabled:
                    raise ValueError(
                        "strategy-audit persistence requires strategy risk "
                        "audit DB to be enabled",
                    )
                dsn = strategy_risk_audit_db_config.dsn
                if dsn is None:
                    raise ValueError(
                        "strategy-audit persistence requires a strategy risk "
                        "audit DB DSN",
                    )

                def strategy_audit_report_sink(
                    report: PaperStrategyRiskAuditReport,
                    *,
                    db_dsn: str = dsn,
                    table_name: str = strategy_risk_audit_db_config.table_name,
                ) -> object:
                    try:
                        return strategy_risk_audit_db_sink(
                            dsn=db_dsn,
                            report=report,
                            table_name=table_name,
                        )
                    except Exception as exc:
                        _raise_redacted_db_sink_error(exc, dsn=db_dsn)

            report = _run_strategy_audit(
                cycle_log=args.cycle_log,
                trade_log=args.trade_log,
                nav_log=args.nav_log,
                outcome_log=args.outcome_log,
                runner=strategy_audit_runner,
            )
            if args.strategy_audit_log is not None:
                PaperStrategyRiskAuditLog(args.strategy_audit_log).append(report)
            persisted = False
            if strategy_audit_report_sink is not None:
                strategy_audit_report_sink(report)
                persisted = True
            _print_strategy_audit_summary(report, persisted=persisted)
            return 0
        except Exception as exc:
            print(f"strategy-audit failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "strategy-audit-history":
        try:
            report = _run_strategy_audit_history(
                strategy_audit_log=args.strategy_audit_log,
                runner=strategy_audit_history_runner,
            )
            _print_strategy_audit_history_summary(report)
            return 0
        except Exception as exc:
            print(f"strategy-audit-history failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "strategy-cycle-db-history":
        try:
            if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit <= 0:
                raise ValueError("strategy-cycle-db-history limit must be positive")
            paper_strategy_cycle_report_db_config = (
                from_paper_strategy_cycle_report_db_env()
            )
            if not paper_strategy_cycle_report_db_config.enabled:
                raise ValueError(
                    "strategy-cycle-db-history requires paper strategy cycle "
                    "report DB to be enabled",
                )
            dsn = paper_strategy_cycle_report_db_config.dsn
            if dsn is None:
                raise ValueError(
                    "strategy-cycle-db-history requires a paper strategy cycle "
                    "report DB DSN "
                    f"({PAPER_STRATEGY_CYCLE_REPORT_DB_DSN_ENV_VAR})",
                )
            try:
                report = _run_strategy_cycle_report_db_history(
                    dsn=dsn,
                    table_name=paper_strategy_cycle_report_db_config.table_name,
                    source_config_version=args.source_config_version,
                    limit=args.limit,
                    runner=strategy_cycle_report_db_history_runner,
                )
            except Exception as exc:
                _raise_redacted_strategy_cycle_report_db_history_error(
                    exc,
                    dsn=dsn,
                    table_name=paper_strategy_cycle_report_db_config.table_name,
                )
            _print_strategy_cycle_report_db_history_summary(report)
            return 0
        except Exception as exc:
            print(f"strategy-cycle-db-history failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "strategy-cycle-history-gate":
        try:
            if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit <= 0:
                raise ValueError("strategy-cycle-history-gate limit must be positive")
            paper_strategy_cycle_report_db_config = (
                from_paper_strategy_cycle_report_db_env()
            )
            if not paper_strategy_cycle_report_db_config.enabled:
                raise ValueError(
                    "strategy-cycle-history-gate requires paper strategy cycle "
                    "report DB to be enabled",
                )
            source_dsn = paper_strategy_cycle_report_db_config.dsn
            if source_dsn is None:
                raise ValueError(
                    "strategy-cycle-history-gate requires a paper strategy cycle "
                    "report DB DSN "
                    f"({PAPER_STRATEGY_CYCLE_REPORT_DB_DSN_ENV_VAR})",
                )
            source_table_name = paper_strategy_cycle_report_db_config.table_name
            try:
                report = _run_strategy_cycle_history_gate(
                    dsn=source_dsn,
                    table_name=source_table_name,
                    source_config_version=args.source_config_version,
                    limit=args.limit,
                    gate_runner=strategy_cycle_history_gate_runner,
                )
            except Exception as exc:
                _raise_redacted_strategy_cycle_history_gate_error(
                    exc,
                    source_dsn=source_dsn,
                    source_table_name=source_table_name,
                )

            persisted = False
            if args.persist:
                gate_db_config = (
                    _from_paper_strategy_cycle_report_history_gate_db_env()
                )
                if not gate_db_config.enabled:
                    raise ValueError(
                        "strategy-cycle-history-gate requires strategy cycle "
                        "history gate DB to be enabled",
                    )
                gate_dsn = gate_db_config.dsn
                if gate_dsn is None:
                    raise ValueError(
                        "strategy-cycle-history-gate requires strategy cycle "
                        "history gate DB DSN "
                        f"({STRATEGY_CYCLE_HISTORY_GATE_DB_DSN_ENV_VAR})",
                    )
                gate_table_name = gate_db_config.table_name
                gate_sink = (
                    strategy_cycle_history_gate_db_sink
                    or _insert_paper_strategy_cycle_report_history_gate_report_with_psycopg
                )
                try:
                    gate_sink(
                        dsn=gate_dsn,
                        report=report,
                        table_name=gate_table_name,
                    )
                except Exception as exc:
                    _raise_redacted_strategy_cycle_history_gate_error(
                        exc,
                        source_dsn=source_dsn,
                        source_table_name=source_table_name,
                        gate_dsn=gate_dsn,
                        gate_table_name=gate_table_name,
                    )
                persisted = True

            _print_strategy_cycle_history_gate_summary(report, persisted=persisted)
            return 0
        except Exception as exc:
            print(f"strategy-cycle-history-gate failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "strategy-audit-db-history":
        try:
            if args.limit <= 0:
                raise ValueError("strategy-audit-db-history limit must be positive")
            strategy_risk_audit_db_config = from_strategy_risk_audit_db_env()
            if not strategy_risk_audit_db_config.enabled:
                raise ValueError(
                    "strategy-audit-db-history requires strategy risk audit "
                    "DB to be enabled",
                )
            dsn = strategy_risk_audit_db_config.dsn
            if dsn is None:
                raise ValueError(
                    "strategy-audit-db-history requires a strategy risk audit "
                    "DB DSN",
                )
            try:
                report = _run_strategy_audit_db_history(
                    dsn=dsn,
                    table_name=strategy_risk_audit_db_config.table_name,
                    limit=args.limit,
                    runner=strategy_audit_db_history_runner,
                )
            except Exception as exc:
                _raise_redacted_db_read_error(exc, dsn=dsn)
            _print_strategy_audit_history_summary(
                report,
                prefix="strategy-audit-db-history",
            )
            return 0
        except Exception as exc:
            print(f"strategy-audit-db-history failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "strategy-recommendation-history":
        try:
            (
                report,
                latest_selected_count,
                latest_selected_notional,
                selection_score_metrics,
            ) = _run_strategy_recommendation_history(
                recommendation_log=args.recommendation_log,
                runner=strategy_recommendation_history_runner,
            )
            _print_strategy_recommendation_history_summary(
                report,
                latest_selected_count=latest_selected_count,
                latest_selected_notional=latest_selected_notional,
                selection_score_metrics=selection_score_metrics,
            )
            return 0
        except Exception as exc:
            print(f"strategy-recommendation-history failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "paper-recommendation-reason-trend":
        try:
            report, action_counts, reason_code_counts = (
                _run_paper_recommendation_reason_trend(
                    recommendation_log=args.recommendation_log,
                )
            )
            _print_paper_recommendation_reason_trend_summary(
                report,
                action_counts=action_counts,
                reason_code_counts=reason_code_counts,
            )
            if args.persist:
                from polymarket_alpha_lab.supabase_paper_recommendation_reason_trend_config import (
                    from_paper_recommendation_reason_trend_db_env,
                )

                reason_trend_db_config = from_paper_recommendation_reason_trend_db_env()
                if not reason_trend_db_config.enabled:
                    raise ValueError(
                        "paper-recommendation-reason-trend persistence requires "
                        "paper recommendation reason trend DB to be enabled",
                    )
                dsn = reason_trend_db_config.dsn
                if dsn is None:
                    raise ValueError(
                        "paper-recommendation-reason-trend persistence requires "
                        "a paper recommendation reason trend DB DSN",
                    )
                if paper_recommendation_reason_trend_db_sink is None:
                    from polymarket_alpha_lab.paper_recommendation_reason_trend_psycopg import (
                        insert_paper_recommendation_reason_trend_report_with_psycopg,
                    )

                    resolved_reason_trend_db_sink = (
                        insert_paper_recommendation_reason_trend_report_with_psycopg
                    )
                else:
                    resolved_reason_trend_db_sink = (
                        paper_recommendation_reason_trend_db_sink
                    )
                try:
                    resolved_reason_trend_db_sink(
                        dsn,
                        report,
                        table_name=reason_trend_db_config.table_name,
                    )
                except Exception as exc:
                    _raise_redacted_db_sink_error(
                        exc,
                        dsn=dsn,
                        table_name=reason_trend_db_config.table_name,
                    )
            return 0
        except Exception as exc:
            print(
                f"paper-recommendation-reason-trend failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-probability-side-edge-report":
        try:
            report, reason_code_counts = _run_paper_probability_side_edge_report(
                input_path=args.input_path,
            )
            _print_paper_probability_side_edge_report_summary(
                report,
                reason_code_counts=reason_code_counts,
            )
            return 0
        except Exception as exc:
            print(
                f"paper-probability-side-edge-report failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-recommendation-queue-report":
        try:
            report, reason_code_counts = _run_paper_recommendation_queue_report(
                input_path=args.input_path,
            )
            _print_paper_recommendation_queue_report_summary(
                report,
                reason_code_counts=reason_code_counts,
            )
            if args.persist:
                from polymarket_alpha_lab.supabase_paper_probability_recommendation_queue_config import (
                    from_paper_probability_recommendation_queue_db_env,
                )

                queue_db_config = from_paper_probability_recommendation_queue_db_env()
                if not queue_db_config.enabled:
                    raise ValueError(
                        "paper-recommendation-queue-report persistence requires "
                        "paper probability recommendation queue DB to be enabled",
                    )
                dsn = queue_db_config.dsn
                if dsn is None:
                    raise ValueError(
                        "paper-recommendation-queue-report persistence requires "
                        "a paper probability recommendation queue DB DSN",
                    )
                if paper_probability_recommendation_queue_db_sink is None:
                    from polymarket_alpha_lab.paper_probability_recommendation_queue_psycopg import (
                        insert_paper_probability_recommendation_queue_report_with_psycopg,
                    )

                    resolved_queue_db_sink = (
                        insert_paper_probability_recommendation_queue_report_with_psycopg
                    )
                else:
                    resolved_queue_db_sink = (
                        paper_probability_recommendation_queue_db_sink
                    )
                try:
                    resolved_queue_db_sink(
                        dsn,
                        report,
                        table_name=queue_db_config.table_name,
                    )
                except Exception as exc:
                    _raise_redacted_db_sink_error(
                        exc,
                        dsn=dsn,
                        table_name=queue_db_config.table_name,
                    )
            return 0
        except Exception as exc:
            print(
                f"paper-recommendation-queue-report failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-recommendation-risk-budget-report":
        try:
            report, zero_allocation_count = (
                _run_paper_recommendation_risk_budget_report(
                    input_path=args.input_path,
                    nav_notional=args.nav_notional,
                )
            )
            _print_paper_recommendation_risk_budget_report_summary(
                report,
                zero_allocation_count=zero_allocation_count,
            )
            if args.persist:
                from polymarket_alpha_lab.supabase_paper_recommendation_risk_budget_config import (
                    from_paper_recommendation_risk_budget_db_env,
                )

                risk_budget_db_config = from_paper_recommendation_risk_budget_db_env()
                if not risk_budget_db_config.enabled:
                    raise ValueError(
                        "paper-recommendation-risk-budget-report persistence "
                        "requires paper recommendation risk budget DB to be enabled",
                    )
                dsn = risk_budget_db_config.dsn
                if dsn is None:
                    raise ValueError(
                        "paper-recommendation-risk-budget-report persistence "
                        "requires a paper recommendation risk budget DB DSN",
                    )
                if paper_recommendation_risk_budget_db_sink is None:
                    from polymarket_alpha_lab.paper_recommendation_risk_budget_psycopg import (
                        insert_paper_recommendation_risk_budget_report_with_psycopg,
                    )

                    resolved_risk_budget_db_sink = (
                        insert_paper_recommendation_risk_budget_report_with_psycopg
                    )
                else:
                    resolved_risk_budget_db_sink = (
                        paper_recommendation_risk_budget_db_sink
                    )
                try:
                    resolved_risk_budget_db_sink(
                        dsn,
                        report,
                        table_name=risk_budget_db_config.table_name,
                    )
                except Exception as exc:
                    _raise_redacted_db_sink_error(
                        exc,
                        dsn=dsn,
                        table_name=risk_budget_db_config.table_name,
                    )
            return 0
        except Exception as exc:
            print(
                f"paper-recommendation-risk-budget-report failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-probability-selection-summary-history":
        try:
            if (
                isinstance(args.limit, bool)
                or type(args.limit) is not int
                or args.limit < 1
            ):
                raise ValueError(
                    "paper-probability-selection-summary-history limit must be positive",
                )
            source_db_config = from_paper_probability_selection_summary_db_env()
            if not source_db_config.enabled:
                raise ValueError(
                    "paper-probability-selection-summary-history requires "
                    "paper probability selection summary DB to be enabled",
                )
            dsn = source_db_config.dsn
            if dsn is None:
                raise ValueError(
                    "paper-probability-selection-summary-history requires "
                    "a paper probability selection summary DB DSN",
                )
            try:
                report = _run_paper_probability_selection_summary_history(
                    dsn=dsn,
                    table_name=source_db_config.table_name,
                    limit=args.limit,
                    runner=paper_probability_selection_summary_history_runner,
                )
            except Exception as exc:
                raise _redacted_paper_probability_selection_summary_history_error(
                    exc,
                    dsn=dsn,
                    table_name=source_db_config.table_name,
                ) from None
            _print_paper_probability_selection_summary_history_summary(report)
            if args.persist:
                history_db_config = (
                    from_paper_probability_selection_summary_history_db_env()
                )
                if not history_db_config.enabled:
                    raise ValueError(
                        "paper-probability-selection-summary-history persistence "
                        "requires history DB to be enabled",
                    )
                history_dsn = history_db_config.dsn
                if history_dsn is None:
                    raise ValueError(
                        "paper-probability-selection-summary-history persistence "
                        "requires a history DB DSN",
                    )
                if paper_probability_selection_summary_history_db_sink is None:
                    from polymarket_alpha_lab.paper_probability_selection_summary_history_psycopg import (
                        insert_paper_probability_selection_summary_history_report_with_psycopg,
                    )

                    resolved_history_db_sink = (
                        insert_paper_probability_selection_summary_history_report_with_psycopg
                    )
                else:
                    resolved_history_db_sink = (
                        paper_probability_selection_summary_history_db_sink
                    )
                try:
                    sink_result = resolved_history_db_sink(
                        dsn=history_dsn,
                        report=report,
                        table_name=history_db_config.table_name,
                    )
                except Exception as exc:
                    raise _redacted_paper_probability_selection_summary_history_persistence_error(
                        exc,
                        source_dsn=dsn,
                        source_table_name=source_db_config.table_name,
                        history_dsn=history_dsn,
                        history_table_name=history_db_config.table_name,
                    ) from None
                persisted = getattr(sink_result, "inserted", True)
                print(
                    "paper-probability-selection-summary-history: "
                    f"persisted={persisted}",
                )
            return 0
        except Exception as exc:
            print(
                f"paper-probability-selection-summary-history failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-probability-selection-summary-history-trend":
        try:
            if (
                isinstance(args.limit, bool)
                or type(args.limit) is not int
                or args.limit < 1
            ):
                raise ValueError(
                    "paper-probability-selection-summary-history-trend "
                    "limit must be positive",
                )
            history_db_config = (
                from_paper_probability_selection_summary_history_db_env()
            )
            if not history_db_config.enabled:
                raise ValueError(
                    "paper-probability-selection-summary-history-trend requires "
                    "paper probability selection summary history DB to be enabled",
                )
            dsn = history_db_config.dsn
            if dsn is None:
                raise ValueError(
                    "paper-probability-selection-summary-history-trend requires "
                    "a paper probability selection summary history DB DSN",
                )
            try:
                report = _run_paper_probability_selection_summary_history_trend(
                    dsn=dsn,
                    table_name=history_db_config.table_name,
                    limit=args.limit,
                    runner=paper_probability_selection_summary_history_trend_runner,
                )
            except Exception as exc:
                raise _redacted_paper_probability_selection_summary_history_trend_error(
                    exc,
                    dsn=dsn,
                    table_name=history_db_config.table_name,
                ) from None
            _print_paper_probability_selection_summary_history_trend_summary(report)
            return 0
        except Exception as exc:
            print(
                f"paper-probability-selection-summary-history-trend failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "autonomous-market-scorer-history":
        command_name = "autonomous-market-scorer-history"
        try:
            if (
                isinstance(args.limit, bool)
                or type(args.limit) is not int
                or args.limit < 1
            ):
                raise ValueError(f"{command_name} limit must be positive")
            scorer_db_config = from_autonomous_market_scorer_db_env()
            if not scorer_db_config.enabled:
                raise ValueError(
                    f"{command_name} requires autonomous market scorer DB "
                    "to be enabled",
                )
            dsn = scorer_db_config.dsn
            if dsn is None:
                raise ValueError(
                    f"{command_name} requires an autonomous market scorer DB DSN",
                )
            try:
                report = _run_autonomous_market_scorer_history(
                    dsn=dsn,
                    table_name=scorer_db_config.table_name,
                    limit=args.limit,
                    runner=autonomous_market_scorer_history_runner,
                )
            except Exception as exc:
                raise _redacted_autonomous_market_scorer_history_error(
                    exc,
                    dsn=dsn,
                    table_name=scorer_db_config.table_name,
                ) from None
            _print_autonomous_market_scorer_history_summary(report)
            return 0
        except Exception as exc:
            print(f"{command_name} failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "probability-selection-scorer-agreement":
        command_name = "probability-selection-scorer-agreement"
        try:
            _require_probability_selection_scorer_agreement_limit(args.limit)
            selection_summary_db_config = (
                from_paper_probability_selection_summary_db_env()
            )
            if not selection_summary_db_config.enabled:
                raise ValueError(
                    f"{command_name} requires paper probability selection summary "
                    "DB to be enabled",
                )
            scorer_db_config = from_autonomous_market_scorer_db_env()
            if not scorer_db_config.enabled:
                raise ValueError(
                    f"{command_name} requires autonomous market scorer DB "
                    "to be enabled",
                )
            agreement_db_config = from_probability_selection_scorer_agreement_db_env()
            selection_summary_dsn = selection_summary_db_config.dsn
            if selection_summary_dsn is None:
                raise ValueError(
                    f"{command_name} requires a paper probability selection "
                    "summary DB DSN",
                )
            scorer_dsn = scorer_db_config.dsn
            if scorer_dsn is None:
                raise ValueError(
                    f"{command_name} requires an autonomous market scorer DB DSN",
                )
            agreement_dsn = agreement_db_config.dsn
            validate_local_postgres_dsn(
                selection_summary_dsn,
                env_var_name=PAPER_PROBABILITY_SELECTION_SUMMARY_DB_DSN_ENV_VAR,
            )
            validate_local_postgres_dsn(
                scorer_dsn,
                env_var_name=AUTONOMOUS_MARKET_SCORER_DB_DSN_ENV_VAR,
            )
            if agreement_db_config.enabled:
                if agreement_dsn is None:
                    raise ValueError(
                        f"{command_name} requires a probability selection scorer "
                        "agreement DB DSN",
                    )
                validate_local_postgres_dsn(
                    agreement_dsn,
                    env_var_name=(
                        PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR
                    ),
                )
            try:
                report = _run_probability_selection_scorer_agreement(
                    selection_summary_dsn=selection_summary_dsn,
                    selection_summary_table_name=(
                        selection_summary_db_config.table_name
                    ),
                    scorer_dsn=scorer_dsn,
                    scorer_table_name=scorer_db_config.table_name,
                    limit=args.limit,
                    runner=probability_selection_scorer_agreement_runner,
                )
                if agreement_db_config.enabled:
                    sink = probability_selection_scorer_agreement_db_sink
                    if sink is None:
                        from polymarket_alpha_lab.probability_selection_scorer_agreement_psycopg import (
                            insert_probability_selection_scorer_agreement_report_with_psycopg,
                        )

                        sink = (
                            insert_probability_selection_scorer_agreement_report_with_psycopg
                        )
                    sink(
                        dsn=agreement_dsn,
                        report=report,
                        table_name=agreement_db_config.table_name,
                    )
            except Exception as exc:
                raise _redacted_probability_selection_scorer_agreement_error(
                    exc,
                    selection_summary_dsn=selection_summary_dsn,
                    selection_summary_table_name=(
                        selection_summary_db_config.table_name
                    ),
                    scorer_dsn=scorer_dsn,
                    scorer_table_name=scorer_db_config.table_name,
                    agreement_dsn=agreement_dsn,
                    agreement_table_name=agreement_db_config.table_name,
                ) from None
            _print_probability_selection_scorer_agreement_summary(report)
            return 0
        except Exception as exc:
            print(f"{command_name} failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "probability-selection-scorer-agreement-trend":
        command_name = "probability-selection-scorer-agreement-trend"
        try:
            if (
                isinstance(args.limit, bool)
                or type(args.limit) is not int
                or args.limit < 1
            ):
                raise ValueError(f"{command_name} limit must be positive")
            agreement_db_config = from_probability_selection_scorer_agreement_db_env()
            if not agreement_db_config.enabled:
                raise ValueError(
                    f"{command_name} requires probability selection scorer "
                    "agreement DB to be enabled",
                )
            dsn = agreement_db_config.dsn
            if dsn is None:
                raise ValueError(
                    f"{PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR} "
                    "must be set when DB is enabled",
                )
            validate_local_postgres_dsn(
                dsn,
                env_var_name=PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR,
            )
            try:
                report = _run_probability_selection_scorer_agreement_trend(
                    dsn=dsn,
                    table_name=agreement_db_config.table_name,
                    limit=args.limit,
                    runner=probability_selection_scorer_agreement_trend_runner,
                )
            except Exception as exc:
                raise _redacted_probability_selection_scorer_agreement_trend_error(
                    exc,
                    dsn=dsn,
                    table_name=agreement_db_config.table_name,
                ) from None
            _print_probability_selection_scorer_agreement_trend_summary(report)
            return 0
        except Exception as exc:
            print(f"{command_name} failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "probability-selection-scorer-agreement-trend-gate":
        command_name = "probability-selection-scorer-agreement-trend-gate"
        try:
            if (
                isinstance(args.limit, bool)
                or type(args.limit) is not int
                or args.limit < 1
            ):
                raise ValueError(f"{command_name} limit must be positive")
            agreement_db_config = from_probability_selection_scorer_agreement_db_env()
            if not agreement_db_config.enabled:
                raise ValueError(
                    f"{command_name} requires probability selection scorer "
                    "agreement DB to be enabled",
                )
            dsn = agreement_db_config.dsn
            if dsn is None:
                raise ValueError(
                    f"{PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR} "
                    "must be set when DB is enabled",
                )
            validate_local_postgres_dsn(
                dsn,
                env_var_name=PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR,
            )
            try:
                report = _run_probability_selection_scorer_agreement_trend_gate(
                    dsn=dsn,
                    table_name=agreement_db_config.table_name,
                    limit=args.limit,
                    runner=probability_selection_scorer_agreement_trend_gate_runner,
                )
            except Exception as exc:
                raise _redacted_probability_selection_scorer_agreement_trend_error(
                    exc,
                    dsn=dsn,
                    table_name=agreement_db_config.table_name,
                ) from None
            _print_probability_selection_scorer_agreement_trend_gate_summary(report)
            return 0
        except Exception as exc:
            print(f"{command_name} failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "strategy-evidence":
        try:
            report = _run_strategy_evidence(
                cycle_log=args.cycle_log,
                trade_log=args.trade_log,
                nav_log=args.nav_log,
                outcome_log=args.outcome_log,
                strategy_audit_log=args.strategy_audit_log,
                runner=strategy_evidence_runner,
            )
            _print_strategy_evidence_summary(report)
            return 0
        except Exception as exc:
            print(f"strategy-evidence failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "observability-trends":
        try:
            observability_trends_db_config = None
            if args.persist:
                from polymarket_alpha_lab.supabase_local_observability_trends_config import (
                    from_local_observability_trends_db_env,
                )

                observability_trends_db_config = (
                    from_local_observability_trends_db_env()
                )
                if not observability_trends_db_config.enabled:
                    raise ValueError(
                        "observability-trends persistence requires local "
                        "observability trends DB to be enabled",
                    )
                if observability_trends_db_config.dsn is None:
                    raise ValueError(
                        "observability-trends persistence requires a local "
                        "observability trends DB DSN",
                    )
            report = observability_trends_runner(
                cycle_log=args.cycle_log,
                trade_log=args.trade_log,
                nav_log=args.nav_log,
                outcome_log=args.outcome_log,
                strategy_audit_log=args.strategy_audit_log,
                config=LocalObservabilityTrendsConfig(
                    config_version="local-observability-trends-v0",
                    outcome_stale_after_seconds=args.outcome_stale_after_seconds,
                ),
                generated_at=datetime.now(UTC),
            )
            persisted = False
            if observability_trends_db_config is not None:
                dsn = observability_trends_db_config.dsn
                if dsn is None:
                    raise ValueError(
                        "observability-trends persistence requires a local "
                        "observability trends DB DSN",
                    )
                if local_observability_trends_db_sink is None:
                    from polymarket_alpha_lab.local_observability_trends_psycopg import (
                        insert_local_observability_trends_report_with_psycopg,
                    )

                    resolved_db_sink = (
                        insert_local_observability_trends_report_with_psycopg
                    )
                else:
                    resolved_db_sink = local_observability_trends_db_sink
                try:
                    resolved_db_sink(
                        dsn=dsn,
                        report=report,
                        table_name=observability_trends_db_config.table_name,
                    )
                except Exception as exc:
                    _raise_redacted_db_sink_error(exc, dsn=dsn)
                persisted = True
            _print_observability_trends_summary(report, persisted=persisted)
            return 0
        except Exception as exc:
            print(f"observability-trends failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "local-observability-trends-db-history":
        try:
            from polymarket_alpha_lab.supabase_local_observability_trends_config import (
                from_local_observability_trends_db_env,
            )

            if args.limit <= 0:
                raise ValueError(
                    "local-observability-trends-db-history limit must be positive",
                )
            observability_trends_db_config = (
                from_local_observability_trends_db_env()
            )
            if not observability_trends_db_config.enabled:
                raise ValueError(
                    "local-observability-trends-db-history requires local "
                    "observability trends DB to be enabled",
                )
            dsn = observability_trends_db_config.dsn
            if dsn is None:
                raise ValueError(
                    "local-observability-trends-db-history requires a local "
                    "observability trends DB DSN",
                )
            try:
                report = _run_local_observability_trends_db_history(
                    dsn=dsn,
                    table_name=observability_trends_db_config.table_name,
                    limit=args.limit,
                    runner=local_observability_trends_db_history_runner,
                )
            except Exception as exc:
                _raise_redacted_db_read_error(exc, dsn=dsn)
            _print_local_observability_trends_db_history_summary(report)
            return 0
        except Exception as exc:
            print(
                f"local-observability-trends-db-history failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "cycle-snapshot-db-trend":
        try:
            report = _run_cycle_snapshot_db_trend(
                source_config_version=args.source_config_version,
                limit=args.limit,
                runner=cycle_snapshot_db_trend_runner,
            )
            _print_cycle_snapshot_db_trend_summary(report)
            return 0
        except Exception as exc:
            print(f"cycle-snapshot-db-trend failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "paper-recommendation-cycle-review":
        try:
            report = _run_cycle_snapshot_db_review(
                source_config_version=args.source_config_version,
                limit=args.limit,
                stale_after_hours=args.stale_after_hours,
                runner=cycle_snapshot_db_review_runner,
            )
            _print_cycle_snapshot_db_review_summary(report)
            return 0
        except Exception as exc:
            print(
                f"paper-recommendation-cycle-review failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-recommendation-cycle-action-gate":
        try:
            report = _run_cycle_snapshot_db_action_gate(
                source_config_version=args.source_config_version,
                limit=args.limit,
                stale_after_hours=args.stale_after_hours,
                runner=cycle_snapshot_db_action_gate_runner,
            )
            _print_cycle_snapshot_db_action_gate_summary(report)
            return 0
        except Exception as exc:
            print(
                f"paper-recommendation-cycle-action-gate failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "action-gated-queue-decision-support":
        try:
            priority_report, risk_report = _run_action_gated_queue_decision_support(
                source_config_version=args.source_config_version,
                action_status=args.action_status,
                limit=args.limit,
                max_total_ready_notional=args.max_total_ready_notional,
                max_single_queue_ready_notional=(
                    args.max_single_queue_ready_notional
                ),
                max_ready_candidate_count=args.max_ready_candidate_count,
                max_total_candidate_count=args.max_total_candidate_count,
                throttle_utilization_threshold=(
                    args.throttle_utilization_threshold
                ),
                loader=action_gated_queue_loader,
                priority_builder=action_gated_queue_priority_builder,
                risk_builder=action_gated_queue_risk_builder,
            )
            _print_action_gated_queue_decision_support_summary(
                priority_report,
                risk_report,
            )
            return 0
        except Exception as exc:
            print(
                f"action-gated-queue-decision-support failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "action-gated-queue-decision-support-trend":
        try:
            report, persisted = _run_action_gated_queue_decision_support_trend(
                source_limit=args.source_limit,
                source_risk_status=args.source_risk_status,
                persist=args.persist,
                runner=action_gated_queue_decision_support_trend_runner,
            )
            _print_action_gated_queue_decision_support_trend_summary(
                report,
                persisted=persisted,
            )
            return 0
        except Exception as exc:
            print(
                f"action-gated-queue-decision-support-trend failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "action-gated-queue-decision-support-trend-db-history":
        try:
            if args.limit <= 0:
                raise ValueError(
                    "action-gated-queue-decision-support-trend-db-history "
                    "limit must be positive",
                )
            trend_db_config = (
                from_action_gated_strategy_recommendation_queue_decision_support_trend_db_env()
            )
            if not trend_db_config.enabled:
                raise ValueError(
                    "action-gated-queue-decision-support-trend-db-history "
                    "requires action-gated queue decision-support trend DB "
                    "to be enabled",
                )
            dsn = trend_db_config.dsn
            if dsn is None:
                raise ValueError(
                    "action-gated-queue-decision-support-trend-db-history "
                    "requires an action-gated queue decision-support trend DB DSN",
                )
            try:
                report = _run_action_gated_queue_decision_support_trend_db_history(
                    dsn=dsn,
                    reports_table_name=trend_db_config.reports_table_name,
                    sources_table_name=trend_db_config.sources_table_name,
                    latest_risk_status=args.latest_risk_status,
                    limit=args.limit,
                    runner=(
                        action_gated_queue_decision_support_trend_db_history_runner
                    ),
                )
            except Exception as exc:
                _raise_redacted_db_read_error(exc, dsn=dsn)
            _print_action_gated_queue_decision_support_trend_db_history_summary(
                report,
            )
            return 0
        except Exception as exc:
            print(
                "action-gated-queue-decision-support-trend-db-history "
                f"failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "action-gated-queue-history":
        try:
            report, persisted = _run_action_gated_queue_history(
                source_config_version=args.source_config_version,
                action_status=args.action_status,
                limit=args.limit,
                persist=args.persist,
                loader=action_gated_queue_loader,
                history_builder=action_gated_queue_history_builder,
                history_db_sink=action_gated_queue_history_db_sink,
            )
            _print_action_gated_queue_history_summary(report, persisted=persisted)
            return 0
        except Exception as exc:
            print(
                f"action-gated-queue-history failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "action-gated-queue-history-db-history":
        try:
            if args.limit <= 0:
                raise ValueError(
                    "action-gated-queue-history-db-history limit must be positive",
                )
            history_db_config = (
                from_action_gated_strategy_recommendation_queue_history_db_env()
            )
            if not history_db_config.enabled:
                raise ValueError(
                    "action-gated-queue-history-db-history requires "
                    "action-gated queue history DB to be enabled",
                )
            dsn = history_db_config.dsn
            if dsn is None:
                raise ValueError(
                    "action-gated-queue-history-db-history requires "
                    "an action-gated queue history DB DSN",
                )
            try:
                report = _run_action_gated_queue_history_db_history(
                    dsn=dsn,
                    table_name=history_db_config.table_name,
                    latest_action_status=args.latest_action_status,
                    limit=args.limit,
                    runner=action_gated_queue_history_db_history_runner,
                )
            except Exception as exc:
                _raise_redacted_db_read_error(exc, dsn=dsn)
            _print_action_gated_queue_history_db_history_summary(report)
            return 0
        except Exception as exc:
            print(
                f"action-gated-queue-history-db-history failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "strategy-candidate-research-queue-history":
        try:
            report, persisted = _run_strategy_candidate_research_queue_history(
                source_config_version=args.source_config_version,
                action_status=args.action_status,
                research_status=args.research_status,
                limit=args.limit,
                persist=args.persist,
                loader=strategy_candidate_research_queue_loader,
                history_builder=strategy_candidate_research_queue_history_builder,
                history_db_sink=strategy_candidate_research_queue_history_db_sink,
            )
            _print_strategy_candidate_research_queue_history_summary(
                report,
                persisted=persisted,
            )
            return 0
        except Exception as exc:
            print(
                f"strategy-candidate-research-queue-history failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-research-packet":
        try:
            report, persisted = _run_paper_research_packet(
                source_config_version=args.source_config_version,
                action_status=args.action_status,
                research_status=args.research_status,
                limit=args.limit,
                packet_config_version=args.packet_config_version,
                max_packet_rows=args.max_packet_rows,
                min_score=args.min_score,
                persist=args.persist,
                loader=strategy_candidate_research_queue_loader,
                packet_builder=paper_research_packet_builder,
                packet_db_sink=paper_research_packet_db_sink,
            )
            _print_paper_research_packet_summary(report, persisted=persisted)
            return 0
        except Exception as exc:
            print(
                f"paper-research-packet failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-research-packet-db-history":
        try:
            if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit < 1:
                raise ValueError(
                    "paper-research-packet-db-history limit must be positive",
                )
            packet_db_config = from_paper_research_packet_db_env()
            if not packet_db_config.enabled:
                raise ValueError(
                    "paper-research-packet-db-history requires "
                    "paper research packet DB to be enabled",
                )
            dsn = packet_db_config.dsn
            if dsn is None:
                raise ValueError(
                    "paper-research-packet-db-history requires "
                    "a paper research packet DB DSN",
                )
            try:
                report = _run_paper_research_packet_db_history(
                    dsn=dsn,
                    table_name=packet_db_config.table_name,
                    limit=args.limit,
                    runner=paper_research_packet_db_history_runner,
                )
            except Exception as exc:
                raise _redacted_paper_research_packet_db_history_error(
                    exc,
                    dsn=dsn,
                    table_name=packet_db_config.table_name,
                ) from None
            _print_paper_research_packet_db_history_summary(report)
            return 0
        except Exception as exc:
            print(
                f"paper-research-packet-db-history failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-research-packet-quality":
        try:
            packet_db_config = from_paper_research_packet_db_env()
            quality_db_config = (
                from_paper_research_packet_quality_db_env()
                if args.persist
                else None
            )
            if not packet_db_config.enabled:
                raise ValueError(
                    "paper-research-packet-quality requires "
                    "paper research packet DB to be enabled",
                )
            dsn = packet_db_config.dsn
            if dsn is None:
                raise ValueError(
                    "paper-research-packet-quality requires "
                    "a paper research packet DB DSN",
                )
            try:
                report = _run_paper_research_packet_quality(
                    dsn=dsn,
                    table_name=packet_db_config.table_name,
                    persist=args.persist,
                    quality_db_config=quality_db_config,
                    runner=paper_research_packet_quality_runner,
                )
            except Exception as exc:
                raise _redacted_paper_research_packet_quality_error(
                    exc,
                    source_dsn=dsn,
                    source_table_name=packet_db_config.table_name,
                    quality_dsn=(
                        quality_db_config.dsn
                        if quality_db_config is not None
                        else None
                    ),
                    quality_table_name=(
                        quality_db_config.table_name
                        if quality_db_config is not None
                        else None
                    ),
                ) from None
            _print_paper_research_packet_quality_summary(
                report,
                persisted=args.persist,
            )
            return 0
        except Exception as exc:
            print(
                f"paper-research-packet-quality failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-research-packet-quality-db-history":
        try:
            if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit < 1:
                raise ValueError(
                    "paper-research-packet-quality-db-history limit must be positive",
                )
            quality_db_config = from_paper_research_packet_quality_db_env()
            if not quality_db_config.enabled:
                raise ValueError(
                    "paper-research-packet-quality-db-history requires "
                    "paper research packet quality DB to be enabled",
                )
            dsn = quality_db_config.dsn
            if dsn is None:
                raise ValueError(
                    "paper-research-packet-quality-db-history requires "
                    "a paper research packet quality DB DSN",
                )
            try:
                report = _run_paper_research_packet_quality_db_history(
                    dsn=dsn,
                    table_name=quality_db_config.table_name,
                    limit=args.limit,
                    runner=paper_research_packet_quality_db_history_runner,
                )
            except Exception as exc:
                raise _redacted_paper_research_packet_db_history_error(
                    exc,
                    dsn=dsn,
                    table_name=quality_db_config.table_name,
                ) from None
            _print_paper_research_packet_quality_db_history_summary(report)
            return 0
        except Exception as exc:
            print(
                f"paper-research-packet-quality-db-history failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-research-packet-operator-flow-db-history":
        try:
            if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit < 1:
                raise ValueError(
                    "paper-research-packet-operator-flow-db-history limit "
                    "must be positive",
                )
            operator_flow_db_config = from_paper_research_packet_operator_flow_db_env()
            if not operator_flow_db_config.enabled:
                raise ValueError(
                    "paper-research-packet-operator-flow-db-history requires "
                    "paper research packet operator-flow DB to be enabled",
                )
            dsn = operator_flow_db_config.dsn
            if dsn is None:
                raise ValueError(
                    "paper-research-packet-operator-flow-db-history requires "
                    "a paper research packet operator-flow DB DSN",
                )
            try:
                report = _run_paper_research_packet_operator_flow_db_history(
                    dsn=dsn,
                    table_name=operator_flow_db_config.table_name,
                    limit=args.limit,
                    runner=paper_research_packet_operator_flow_db_history_runner,
                )
            except Exception as exc:
                raise _redacted_paper_research_packet_db_history_error(
                    exc,
                    dsn=dsn,
                    table_name=operator_flow_db_config.table_name,
                ) from None
            _print_paper_research_packet_operator_flow_db_history_summary(report)
            return 0
        except Exception as exc:
            print(
                f"paper-research-packet-operator-flow-db-history failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-research-packet-operator-flow-db-history-gate":
        try:
            if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit < 1:
                raise ValueError(
                    "paper-research-packet-operator-flow-db-history-gate limit "
                    "must be positive",
                )
            operator_flow_db_config = from_paper_research_packet_operator_flow_db_env()
            if not operator_flow_db_config.enabled:
                raise ValueError(
                    "paper-research-packet-operator-flow-db-history-gate requires "
                    "paper research packet operator-flow DB to be enabled",
                )
            dsn = operator_flow_db_config.dsn
            if dsn is None:
                raise ValueError(
                    "paper-research-packet-operator-flow-db-history-gate requires "
                    "a paper research packet operator-flow DB DSN",
                )
            try:
                report = _run_paper_research_packet_operator_flow_db_history_gate(
                    dsn=dsn,
                    table_name=operator_flow_db_config.table_name,
                    limit=args.limit,
                    runner=paper_research_packet_operator_flow_db_history_gate_runner,
                )
            except Exception as exc:
                raise _redacted_paper_research_packet_db_history_error(
                    exc,
                    dsn=dsn,
                    table_name=operator_flow_db_config.table_name,
                ) from None
            _print_paper_research_packet_operator_flow_db_history_gate_summary(report)
            return 0
        except Exception as exc:
            print(
                f"paper-research-packet-operator-flow-db-history-gate failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command in (
        "paper-autonomous-screening-decision-support-gate",
        "paper-autonomous-screening-decision-support-gate-persist",
    ):
        command_name = args.command
        persist_gate_report = (
            command_name
            == "paper-autonomous-screening-decision-support-gate-persist"
        )
        try:
            if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit < 1:
                raise ValueError(
                    f"{command_name} limit must be positive",
                )
            operator_flow_db_config = from_paper_research_packet_operator_flow_db_env()
            if not operator_flow_db_config.enabled:
                raise ValueError(
                    f"{command_name} requires "
                    "paper research packet operator-flow DB to be enabled",
                )
            operator_flow_dsn = operator_flow_db_config.dsn
            if operator_flow_dsn is None:
                raise ValueError(
                    f"{command_name} requires "
                    "a paper research packet operator-flow DB DSN",
                )
            action_queue_db_config = (
                from_action_gated_strategy_recommendation_queue_decision_support_db_env()
            )
            if not action_queue_db_config.enabled:
                raise ValueError(
                    f"{command_name} requires "
                    "action-gated queue decision-support DB to be enabled",
                )
            action_queue_dsn = action_queue_db_config.dsn
            if action_queue_dsn is None:
                raise ValueError(
                    f"{command_name} requires "
                    "an action-gated queue decision-support DB DSN",
                )
            rank_stability_db_config = (
                from_paper_project_screening_rank_stability_db_env()
            )
            rank_stability_dsn = None
            rank_stability_table_name = None
            if rank_stability_db_config.enabled:
                rank_stability_dsn = rank_stability_db_config.dsn
                if rank_stability_dsn is None:
                    raise ValueError(
                        f"{command_name} requires "
                        "a paper project screening rank stability DB DSN when "
                        "rank-stability DB is enabled",
                    )
                rank_stability_table_name = rank_stability_db_config.table_name
            screening_gate_dsn = None
            screening_gate_table_name = None
            if persist_gate_report:
                screening_gate_db_config = (
                    from_paper_autonomous_screening_decision_support_gate_db_env()
                )
                if not screening_gate_db_config.enabled:
                    raise ValueError(
                        f"{command_name} requires autonomous screening gate DB "
                        "to be enabled",
                    )
                screening_gate_dsn = screening_gate_db_config.dsn
                if screening_gate_dsn is None:
                    raise ValueError(
                        f"{command_name} requires an autonomous screening gate DB DSN",
                    )
                screening_gate_table_name = screening_gate_db_config.table_name
                if screening_gate_table_name is None:
                    raise ValueError(
                        f"{command_name} requires an autonomous screening gate "
                        "DB table",
                    )
            try:
                report = _run_paper_autonomous_screening_decision_support_gate(
                    rank_stability_dsn=rank_stability_dsn,
                    rank_stability_table_name=rank_stability_table_name,
                    operator_flow_dsn=operator_flow_dsn,
                    operator_flow_table_name=operator_flow_db_config.table_name,
                    action_queue_dsn=action_queue_dsn,
                    action_queue_table_name=action_queue_db_config.table_name,
                    limit=args.limit,
                    runner=(
                        paper_autonomous_screening_decision_support_gate_runner
                    ),
                )
            except Exception as exc:
                raise _redacted_paper_autonomous_screening_gate_error(
                    exc,
                    rank_stability_dsn=rank_stability_dsn,
                    rank_stability_table_name=rank_stability_table_name,
                    operator_flow_dsn=operator_flow_dsn,
                    operator_flow_table_name=operator_flow_db_config.table_name,
                    action_queue_dsn=action_queue_dsn,
                    action_queue_table_name=action_queue_db_config.table_name,
                ) from None
            _print_paper_autonomous_screening_decision_support_gate_summary(report)
            if persist_gate_report:
                if screening_gate_dsn is None or screening_gate_table_name is None:
                    raise RuntimeError(
                        f"{command_name} output DB config was not validated "
                        "before persistence",
                    )
                try:
                    if paper_autonomous_screening_decision_support_gate_db_sink is None:
                        from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_psycopg import (
                            insert_paper_autonomous_screening_decision_support_gate_report_with_psycopg,
                        )

                        paper_autonomous_screening_decision_support_gate_db_sink = (
                            insert_paper_autonomous_screening_decision_support_gate_report_with_psycopg
                        )
                    sink_result = paper_autonomous_screening_decision_support_gate_db_sink(
                        dsn=screening_gate_dsn,
                        report=report,
                        table_name=screening_gate_table_name,
                    )
                except Exception as exc:
                    message = _redact_db_dsn(str(exc), dsn=screening_gate_dsn)
                    message = _redact_db_table_name_and_tail(
                        message,
                        table_name=screening_gate_table_name,
                    )
                    message = _redact_paper_research_packet_sensitive_fields(message)
                    if not message.strip():
                        message = exc.__class__.__name__
                    raise RuntimeError(message) from None
                inserted = getattr(sink_result, "inserted", True)
                print(f"{command_name}: persisted={inserted}")
            return 0
        except Exception as exc:
            print(
                f"{command_name} failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-autonomous-allocation-proposal-db-history":
        command_name = "paper-autonomous-allocation-proposal-db-history"
        try:
            if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit < 1:
                raise ValueError(f"{command_name} limit must be positive")
            allocation_proposal_db_config = (
                from_paper_autonomous_allocation_proposal_db_env()
            )
            if not allocation_proposal_db_config.enabled:
                raise ValueError(
                    f"{command_name} requires autonomous allocation proposal DB "
                    "to be enabled",
                )
            dsn = allocation_proposal_db_config.dsn
            if dsn is None:
                raise ValueError(
                    f"{command_name} requires an autonomous allocation proposal DB DSN",
                )
            try:
                report = _run_paper_autonomous_allocation_proposal_db_history(
                    dsn=dsn,
                    table_name=allocation_proposal_db_config.table_name,
                    limit=args.limit,
                    runner=paper_autonomous_allocation_proposal_db_history_runner,
                )
            except Exception as exc:
                raise _redacted_paper_research_packet_db_history_error(
                    exc,
                    dsn=dsn,
                    table_name=allocation_proposal_db_config.table_name,
                ) from None
            _print_paper_autonomous_allocation_proposal_db_history_summary(report)
            return 0
        except Exception as exc:
            print(
                f"{command_name} failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-autonomous-allocation-proposal-db-history-gate":
        command_name = "paper-autonomous-allocation-proposal-db-history-gate"
        try:
            if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit < 1:
                raise ValueError(f"{command_name} limit must be positive")
            allocation_proposal_db_config = (
                from_paper_autonomous_allocation_proposal_db_env()
            )
            if not allocation_proposal_db_config.enabled:
                raise ValueError(
                    f"{command_name} requires autonomous allocation proposal DB "
                    "to be enabled",
                )
            dsn = allocation_proposal_db_config.dsn
            if dsn is None:
                raise ValueError(
                    f"{command_name} requires an autonomous allocation proposal DB DSN",
                )
            try:
                report = _run_paper_autonomous_allocation_proposal_db_history_gate(
                    dsn=dsn,
                    table_name=allocation_proposal_db_config.table_name,
                    limit=args.limit,
                    runner=paper_autonomous_allocation_proposal_db_history_gate_runner,
                )
            except Exception as exc:
                raise _redacted_paper_research_packet_db_history_error(
                    exc,
                    dsn=dsn,
                    table_name=allocation_proposal_db_config.table_name,
                ) from None
            _print_paper_autonomous_allocation_proposal_db_history_gate_summary(report)
            return 0
        except Exception as exc:
            print(
                f"{command_name} failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-autonomous-allocation-proposal-db-history-metrics-evaluation":
        command_name = "paper-autonomous-allocation-proposal-db-history-metrics-evaluation"
        try:
            if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit < 1:
                raise ValueError(f"{command_name} limit must be positive")
            allocation_proposal_db_config = (
                from_paper_autonomous_allocation_proposal_db_env()
            )
            if not allocation_proposal_db_config.enabled:
                raise ValueError(
                    f"{command_name} requires autonomous allocation proposal DB "
                    "to be enabled",
                )
            dsn = allocation_proposal_db_config.dsn
            if dsn is None:
                raise ValueError(
                    f"{command_name} requires an autonomous allocation proposal DB DSN",
                )
            try:
                report = _run_paper_autonomous_allocation_proposal_db_history_metrics_evaluation(
                    dsn=dsn,
                    table_name=allocation_proposal_db_config.table_name,
                    limit=args.limit,
                    runner=paper_autonomous_allocation_proposal_db_history_metrics_evaluation_runner,
                )
            except Exception as exc:
                raise _redacted_paper_research_packet_db_history_error(
                    exc,
                    dsn=dsn,
                    table_name=allocation_proposal_db_config.table_name,
                ) from None
            _print_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_summary(
                report,
            )
            return 0
        except Exception as exc:
            print(
                f"error: {command_name}: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-autonomous-allocation-proposal-db-history-metrics":
        command_name = "paper-autonomous-allocation-proposal-db-history-metrics"
        try:
            if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit < 1:
                raise ValueError(f"{command_name} limit must be positive")
            allocation_proposal_db_config = (
                from_paper_autonomous_allocation_proposal_db_env()
            )
            if not allocation_proposal_db_config.enabled:
                raise ValueError(
                    f"{command_name} requires autonomous allocation proposal DB "
                    "to be enabled",
                )
            dsn = allocation_proposal_db_config.dsn
            if dsn is None:
                raise ValueError(
                    f"{command_name} requires an autonomous allocation proposal DB DSN",
                )
            try:
                report = _run_paper_autonomous_allocation_proposal_db_history_metrics(
                    dsn=dsn,
                    table_name=allocation_proposal_db_config.table_name,
                    limit=args.limit,
                    runner=paper_autonomous_allocation_proposal_db_history_metrics_runner,
                )
            except Exception as exc:
                raise _redacted_paper_research_packet_db_history_error(
                    exc,
                    dsn=dsn,
                    table_name=allocation_proposal_db_config.table_name,
                ) from None
            _print_paper_autonomous_allocation_proposal_db_history_metrics_summary(
                report,
            )
            return 0
        except Exception as exc:
            print(
                f"{command_name} failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-autonomous-allocation-proposal-db-history-health":
        command_name = "paper-autonomous-allocation-proposal-db-history-health"
        try:
            if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit < 1:
                raise ValueError(f"{command_name} limit must be positive")
            allocation_proposal_db_config = (
                from_paper_autonomous_allocation_proposal_db_env()
            )
            if not allocation_proposal_db_config.enabled:
                raise ValueError(
                    f"{command_name} requires autonomous allocation proposal DB "
                    "to be enabled",
                )
            dsn = allocation_proposal_db_config.dsn
            if dsn is None:
                raise ValueError(
                    f"{command_name} requires an autonomous allocation proposal DB DSN",
                )
            health_db_config = None
            health_dsn = None
            if args.persist:
                health_db_config = (
                    from_paper_autonomous_allocation_proposal_db_history_health_db_env()
                )
                if not health_db_config.enabled:
                    raise ValueError(
                        f"{command_name} --persist requires DB-history health DB "
                        "to be enabled",
                    )
                health_dsn = health_db_config.dsn
                if health_dsn is None:
                    raise ValueError(
                        f"{command_name} --persist requires a DB-history health DB DSN",
                    )
            try:
                report = (
                    _run_paper_autonomous_allocation_proposal_db_history_health(
                        dsn=dsn,
                        table_name=allocation_proposal_db_config.table_name,
                        limit=args.limit,
                        runner=(
                            paper_autonomous_allocation_proposal_db_history_health_runner
                        ),
                    )
                )
            except Exception as exc:
                if args.persist:
                    raise _redacted_paper_autonomous_allocation_proposal_db_history_health_persistence_error(
                        exc,
                        source_dsn=dsn,
                        source_table_name=allocation_proposal_db_config.table_name,
                        health_dsn=health_dsn,
                        health_table_name=health_db_config.table_name,
                    ) from None
                raise _redacted_paper_research_packet_db_history_error(
                    exc,
                    dsn=dsn,
                    table_name=allocation_proposal_db_config.table_name,
                ) from None
            _print_paper_autonomous_allocation_proposal_db_history_health_summary(
                report,
            )
            if args.persist:
                if (
                    paper_autonomous_allocation_proposal_db_history_health_db_sink
                    is None
                ):
                    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_psycopg import (
                        insert_paper_autonomous_allocation_proposal_db_history_health_report_with_psycopg,
                    )

                    health_sink = (
                        insert_paper_autonomous_allocation_proposal_db_history_health_report_with_psycopg
                    )
                else:
                    health_sink = (
                        paper_autonomous_allocation_proposal_db_history_health_db_sink
                    )
                try:
                    sink_result = health_sink(
                        dsn=health_dsn,
                        report=report,
                        table_name=health_db_config.table_name,
                    )
                except Exception as exc:
                    raise _redacted_paper_autonomous_allocation_proposal_db_history_health_persistence_error(
                        exc,
                        source_dsn=dsn,
                        source_table_name=allocation_proposal_db_config.table_name,
                        health_dsn=health_dsn,
                        health_table_name=health_db_config.table_name,
                    ) from None
                persisted = bool(getattr(sink_result, "inserted", sink_result))
                print(f"{command_name}: persisted={persisted}")
            return 0
        except Exception as exc:
            print(
                f"{command_name} failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-autonomous-allocation-proposal-db-history-health-trend":
        command_name = "paper-autonomous-allocation-proposal-db-history-health-trend"
        try:
            if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit < 1:
                raise ValueError(f"{command_name} limit must be positive")
            health_db_config = (
                from_paper_autonomous_allocation_proposal_db_history_health_db_env()
            )
            if not health_db_config.enabled:
                raise ValueError(
                    f"{command_name} requires DB-history health DB to be enabled",
                )
            dsn = health_db_config.dsn
            if dsn is None:
                raise ValueError(
                    f"{command_name} requires a DB-history health DB DSN",
                )
            try:
                report = (
                    _run_paper_autonomous_allocation_proposal_db_history_health_trend(
                        dsn=dsn,
                        table_name=health_db_config.table_name,
                        limit=args.limit,
                        runner=(
                            paper_autonomous_allocation_proposal_db_history_health_trend_runner
                        ),
                    )
                )
            except Exception as exc:
                raise _redacted_paper_research_packet_db_history_error(
                    exc,
                    dsn=dsn,
                    table_name=health_db_config.table_name,
                ) from None
            _print_paper_autonomous_allocation_proposal_db_history_health_trend_summary(
                report,
            )
            return 0
        except Exception as exc:
            print(
                f"{command_name} failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if (
        args.command
        == "paper-autonomous-allocation-proposal-db-history-health-trend-gate"
    ):
        command_name = (
            "paper-autonomous-allocation-proposal-db-history-health-trend-gate"
        )
        try:
            if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit < 1:
                raise ValueError(f"{command_name} limit must be positive")
            health_db_config = (
                from_paper_autonomous_allocation_proposal_db_history_health_db_env()
            )
            if not health_db_config.enabled:
                raise ValueError(
                    f"{command_name} requires DB-history health DB to be enabled",
                )
            dsn = health_db_config.dsn
            if dsn is None:
                raise ValueError(
                    f"{command_name} requires a DB-history health DB DSN",
                )
            try:
                report = (
                    _run_paper_autonomous_allocation_proposal_db_history_health_trend_gate(
                        dsn=dsn,
                        table_name=health_db_config.table_name,
                        limit=args.limit,
                        runner=(
                            paper_autonomous_allocation_proposal_db_history_health_trend_gate_runner
                        ),
                    )
                )
            except Exception as exc:
                raise _redacted_paper_research_packet_db_history_error(
                    exc,
                    dsn=dsn,
                    table_name=health_db_config.table_name,
                ) from None
            _print_paper_autonomous_allocation_proposal_db_history_health_trend_gate_summary(
                report,
            )
            return 0
        except Exception as exc:
            print(
                f"{command_name} failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command in (
        "paper-autonomous-allocation-proposal",
        "paper-autonomous-allocation-proposal-persist",
    ):
        command_name = args.command
        persist_proposal_report = (
            command_name == "paper-autonomous-allocation-proposal-persist"
        )
        try:
            _require_paper_autonomous_allocation_proposal_limit(
                args.limit,
                command_name=command_name,
            )
            screening_gate_db_config = (
                from_paper_autonomous_screening_decision_support_gate_db_env()
            )
            if not screening_gate_db_config.enabled:
                raise ValueError(
                    f"{command_name} requires "
                    "autonomous screening gate DB to be enabled",
                )
            screening_gate_dsn = screening_gate_db_config.dsn
            if screening_gate_dsn is None:
                raise ValueError(
                    f"{command_name} requires an "
                    "autonomous screening gate DB DSN",
                )
            decision_support_db_config = (
                from_action_gated_strategy_recommendation_queue_decision_support_db_env()
            )
            if not decision_support_db_config.enabled:
                raise ValueError(
                    f"{command_name} requires "
                    "action-gated queue decision-support DB to be enabled",
                )
            decision_support_dsn = decision_support_db_config.dsn
            if decision_support_dsn is None:
                raise ValueError(
                    f"{command_name} requires an "
                    "action-gated queue decision-support DB DSN",
                )
            source_queue_db_config = (
                from_action_gated_strategy_recommendation_queue_db_env()
            )
            if not source_queue_db_config.enabled:
                raise ValueError(
                    f"{command_name} requires "
                    "action-gated queue DB to be enabled",
                )
            source_queue_dsn = source_queue_db_config.dsn
            if source_queue_dsn is None:
                raise ValueError(
                    f"{command_name} requires an "
                    "action-gated queue DB DSN",
                )
            proposal_dsn = None
            proposal_table_name = None
            if persist_proposal_report:
                try:
                    proposal_db_config = (
                        from_paper_autonomous_allocation_proposal_db_env()
                    )
                except ValueError as exc:
                    if "must be set when DB is enabled" in str(exc):
                        raise ValueError(
                            f"{command_name} requires an autonomous allocation "
                            "proposal DB DSN",
                        ) from None
                    raise
                if not proposal_db_config.enabled:
                    raise ValueError(
                        f"{command_name} requires autonomous allocation proposal DB "
                        "to be enabled",
                    )
                proposal_dsn = proposal_db_config.dsn
                if proposal_dsn is None:
                    raise ValueError(
                        f"{command_name} requires an autonomous allocation "
                        "proposal DB DSN",
                    )
                proposal_table_name = proposal_db_config.table_name
                if proposal_table_name is None:
                    raise ValueError(
                        f"{command_name} requires an autonomous allocation "
                        "proposal DB table",
                    )
            try:
                report = _run_paper_autonomous_allocation_proposal(
                    screening_gate_dsn=screening_gate_dsn,
                    screening_gate_table_name=screening_gate_db_config.table_name,
                    action_gated_queue_decision_support_dsn=decision_support_dsn,
                    action_gated_queue_decision_support_table_name=(
                        decision_support_db_config.table_name
                    ),
                    source_queue_dsn=source_queue_dsn,
                    source_queue_table_name=source_queue_db_config.table_name,
                    limit=args.limit,
                    runner=paper_autonomous_allocation_proposal_runner,
                )
            except Exception as exc:
                raise _redacted_paper_autonomous_allocation_proposal_error(
                    exc,
                    screening_gate_dsn=screening_gate_dsn,
                    screening_gate_table_name=screening_gate_db_config.table_name,
                    action_gated_queue_decision_support_dsn=decision_support_dsn,
                    action_gated_queue_decision_support_table_name=(
                        decision_support_db_config.table_name
                    ),
                    source_queue_dsn=source_queue_dsn,
                    source_queue_table_name=source_queue_db_config.table_name,
                ) from None
            _print_paper_autonomous_allocation_proposal_summary(
                report,
                command_name=command_name,
            )
            if persist_proposal_report:
                if proposal_dsn is None or proposal_table_name is None:
                    raise RuntimeError(
                        f"{command_name} output DB config was not validated "
                        "before persistence",
                    )
                try:
                    if paper_autonomous_allocation_proposal_db_sink is None:
                        from polymarket_alpha_lab.paper_autonomous_allocation_proposal_psycopg import (
                            insert_paper_autonomous_allocation_proposal_report_with_psycopg,
                        )

                        paper_autonomous_allocation_proposal_db_sink = (
                            insert_paper_autonomous_allocation_proposal_report_with_psycopg
                        )
                    sink_result = paper_autonomous_allocation_proposal_db_sink(
                        dsn=proposal_dsn,
                        report=report,
                        table_name=proposal_table_name,
                    )
                except Exception as exc:
                    message = _redact_db_dsn(str(exc), dsn=proposal_dsn)
                    message = _redact_db_table_name_and_tail(
                        message,
                        table_name=proposal_table_name,
                    )
                    message = _redact_paper_research_packet_sensitive_fields(message)
                    if not message.strip():
                        message = exc.__class__.__name__
                    raise RuntimeError(message) from None
                persisted = bool(getattr(sink_result, "inserted", sink_result))
                print(f"{command_name}: persisted={persisted}")
            return 0
        except Exception as exc:
            print(
                f"{command_name} failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command in (
        "paper-execution-pipeline",
        "paper-execution-pipeline-persist",
    ):
        command_name = args.command
        persist_pipeline = command_name == "paper-execution-pipeline-persist"
        try:
            if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit < 1:
                raise ValueError(
                    f"{command_name} limit must be positive",
                )
            screening_gate_db_config = from_paper_autonomous_screening_decision_support_gate_db_env()
            if not screening_gate_db_config.enabled:
                raise ValueError(
                    f"{command_name} requires autonomous screening gate DB to be enabled",
                )
            screening_gate_dsn = screening_gate_db_config.dsn
            if screening_gate_dsn is None:
                raise ValueError(
                    f"{command_name} requires an autonomous screening gate DB DSN",
                )
            screening_gate_table_name = screening_gate_db_config.table_name
            if screening_gate_table_name is None:
                raise ValueError(
                    f"{command_name} requires an autonomous screening gate DB table",
                )
            pipeline_runner = (
                paper_execution_pipeline_runner
                if paper_execution_pipeline_runner is not None
                else _run_paper_execution_pipeline
            )
            pipeline_report = pipeline_runner(
                screening_gate_dsn=screening_gate_dsn,
                screening_gate_table_name=screening_gate_table_name,
                limit=args.limit,
            )
            _print_paper_execution_pipeline_summary(pipeline_report)
            if persist_pipeline:
                execution_db_config = from_paper_execution_pipeline_db_env()
                if not execution_db_config.enabled:
                    raise ValueError(
                        f"{command_name} requires paper execution pipeline DB to be enabled",
                    )
                execution_dsn = execution_db_config.dsn
                if execution_dsn is None:
                    raise ValueError(
                        f"{command_name} requires a paper execution pipeline DB DSN",
                    )
                execution_table_name = execution_db_config.table_name
                if execution_table_name is None:
                    raise ValueError(
                        f"{command_name} requires a paper execution pipeline DB table",
                    )
                paper_broker_db_config = from_paper_broker_db_env()
                broker_dsn = paper_broker_db_config.dsn
                broker_table_name = paper_broker_db_config.table_name
                if paper_broker_db_config.enabled and broker_dsn is None:
                    raise ValueError(f"{command_name} requires a paper broker DB DSN")
                investment_ledger_db_config = (
                    from_paper_autonomous_investment_ledger_db_env()
                )
                ledger_dsn = investment_ledger_db_config.dsn
                ledger_table_name = investment_ledger_db_config.table_name
                if investment_ledger_db_config.enabled and ledger_dsn is None:
                    raise ValueError(
                        f"{command_name} requires a paper autonomous investment "
                        "ledger DB DSN",
                    )
                pipeline_persister = (
                    paper_execution_pipeline_persister
                    if paper_execution_pipeline_persister is not None
                    else _persist_paper_execution_pipeline
                )
                persister_kwargs = {
                    "pipeline_report": pipeline_report,
                    "dsn": execution_dsn,
                    "table_name": execution_table_name,
                }
                if paper_broker_db_config.enabled and broker_dsn is not None:
                    persister_kwargs["broker_dsn"] = broker_dsn
                    persister_kwargs["broker_table_name"] = broker_table_name
                if investment_ledger_db_config.enabled and ledger_dsn is not None:
                    persister_kwargs["ledger_dsn"] = ledger_dsn
                    persister_kwargs["ledger_table_name"] = ledger_table_name
                try:
                    pipeline_persister(**persister_kwargs)
                except Exception as exc:
                    _raise_redacted_multi_db_sink_error(
                        exc,
                        dsns=(execution_dsn, broker_dsn, ledger_dsn),
                    )
            return 0
        except Exception as exc:
            print(
                f"{command_name} failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-execution-pipeline-db-history":
        command_name = "paper-execution-pipeline-db-history"
        try:
            if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit < 1:
                raise ValueError(
                    f"{command_name} limit must be positive",
                )
            execution_db_config = from_paper_execution_pipeline_db_env()
            if not execution_db_config.enabled:
                raise ValueError(
                    f"{command_name} requires paper execution pipeline DB to be enabled",
                )
            execution_dsn = execution_db_config.dsn
            if execution_dsn is None:
                raise ValueError(
                    f"{command_name} requires a paper execution pipeline DB DSN",
                )
            execution_table_name = execution_db_config.table_name
            if execution_table_name is None:
                raise ValueError(
                    f"{command_name} requires a paper execution pipeline DB table",
                )
            history_report = _load_paper_execution_pipeline_db_history(
                dsn=execution_dsn,
                table_name=execution_table_name,
                limit=args.limit,
            )
            _print_paper_execution_pipeline_history_summary(history_report)
            return 0
        except Exception as exc:
            print(
                f"{command_name} failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-autonomous-investment-ledger":
        command_name = "paper-autonomous-investment-ledger"
        try:
            if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit < 1:
                raise ValueError(f"{command_name} limit must be positive")
            if (
                isinstance(args.max_latest_source_age_seconds, bool)
                or type(args.max_latest_source_age_seconds) is not int
                or args.max_latest_source_age_seconds < 0
            ):
                raise ValueError(
                    f"{command_name} max latest source age seconds must be nonnegative",
                )
            broker_db_config = from_paper_broker_db_env()
            if not broker_db_config.enabled:
                raise ValueError(
                    f"{command_name} requires paper broker DB to be enabled",
                )
            broker_dsn = broker_db_config.dsn
            if broker_dsn is None:
                raise ValueError(f"{command_name} requires a paper broker DB DSN")
            broker_table_name = broker_db_config.table_name
            if broker_table_name is None:
                raise ValueError(f"{command_name} requires a paper broker DB table")
            ledger_runner = (
                paper_autonomous_investment_ledger_runner
                if paper_autonomous_investment_ledger_runner is not None
                else _load_paper_autonomous_investment_ledger_from_broker_db
            )
            try:
                ledger_report = ledger_runner(
                    broker_dsn=broker_dsn,
                    broker_table_name=broker_table_name,
                    limit=args.limit,
                    source_config_version=args.source_config_version,
                    execution_status=args.execution_status,
                    source_gate_status=args.source_gate_status,
                    max_latest_source_age_seconds=args.max_latest_source_age_seconds,
                )
            except Exception as exc:
                raise _redacted_paper_autonomous_investment_ledger_error(
                    exc,
                    broker_dsn=broker_dsn,
                    broker_table_name=broker_table_name,
                ) from None
            _print_paper_autonomous_investment_ledger_summary(ledger_report)
            if args.persist:
                ledger_db_config = from_paper_autonomous_investment_ledger_db_env()
                if not ledger_db_config.enabled:
                    raise ValueError(
                        f"{command_name} persistence requires paper autonomous "
                        "investment ledger DB to be enabled",
                    )
                ledger_dsn = ledger_db_config.dsn
                if ledger_dsn is None:
                    raise ValueError(
                        f"{command_name} persistence requires a paper autonomous "
                        "investment ledger DB DSN",
                    )
                ledger_table_name = ledger_db_config.table_name
                if ledger_table_name is None:
                    raise ValueError(
                        f"{command_name} persistence requires a paper autonomous "
                        "investment ledger DB table",
                    )
                ledger_sink = (
                    paper_autonomous_investment_ledger_db_sink
                    if paper_autonomous_investment_ledger_db_sink is not None
                    else _persist_paper_autonomous_investment_ledger_report
                )
                try:
                    persist_result = ledger_sink(
                        dsn=ledger_dsn,
                        report=ledger_report,
                        table_name=ledger_table_name,
                    )
                except Exception as exc:
                    raise _redacted_paper_autonomous_investment_ledger_error(
                        exc,
                        broker_dsn=broker_dsn,
                        broker_table_name=broker_table_name,
                        ledger_dsn=ledger_dsn,
                        ledger_table_name=ledger_table_name,
                    ) from None
                persisted = getattr(persist_result, "inserted", True)
                if type(persisted) is not bool:
                    persisted = True
                print(
                    "paper-autonomous-investment-ledger: persisted="
                    f"{persisted}",
                )
            return 0
        except Exception as exc:
            print(
                f"{command_name} failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-autonomous-investment-ledger-db-history":
        command_name = "paper-autonomous-investment-ledger-db-history"
        try:
            if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit < 1:
                raise ValueError(f"{command_name} limit must be positive")
            ledger_db_config = from_paper_autonomous_investment_ledger_db_env()
            if not ledger_db_config.enabled:
                raise ValueError(
                    f"{command_name} requires paper autonomous investment ledger "
                    "DB to be enabled",
                )
            ledger_dsn = ledger_db_config.dsn
            if ledger_dsn is None:
                raise ValueError(
                    f"{command_name} requires a paper autonomous investment "
                    "ledger DB DSN",
                )
            ledger_table_name = ledger_db_config.table_name
            if ledger_table_name is None:
                raise ValueError(
                    f"{command_name} requires a paper autonomous investment "
                    "ledger DB table",
                )
            history_runner = (
                paper_autonomous_investment_ledger_db_history_runner
                if paper_autonomous_investment_ledger_db_history_runner is not None
                else _load_paper_autonomous_investment_ledger_db_history
            )
            try:
                reports = history_runner(
                    dsn=ledger_dsn,
                    table_name=ledger_table_name,
                    limit=args.limit,
                    config_version=args.config_version,
                    ledger_status=args.ledger_status,
                )
            except Exception as exc:
                raise _redacted_paper_autonomous_investment_ledger_error(
                    exc,
                    broker_dsn=ledger_dsn,
                    broker_table_name=ledger_table_name,
                ) from None
            _print_paper_autonomous_investment_ledger_db_history_summary(reports)
            return 0
        except Exception as exc:
            print(
                f"{command_name} failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-autonomous-investment-ledger-db-history-health":
        command_name = "paper-autonomous-investment-ledger-db-history-health"
        try:
            if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit < 1:
                raise ValueError(f"{command_name} limit must be positive")
            ledger_dsn, ledger_table_name = (
                _paper_autonomous_investment_ledger_db_config_from_env(
                    command_name,
                )
            )
            try:
                report = _run_paper_autonomous_investment_ledger_db_history_health(
                    dsn=ledger_dsn,
                    table_name=ledger_table_name,
                    limit=args.limit,
                    runner=(
                        paper_autonomous_investment_ledger_db_history_health_runner
                    ),
                )
            except Exception as exc:
                raise _redacted_paper_autonomous_investment_ledger_error(
                    exc,
                    broker_dsn=ledger_dsn,
                    broker_table_name=ledger_table_name,
                ) from None
            _print_paper_autonomous_investment_ledger_db_history_health_summary(
                report,
            )
            return 0
        except Exception as exc:
            print(
                f"{command_name} failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-autonomous-investment-ledger-db-history-health-trend":
        command_name = "paper-autonomous-investment-ledger-db-history-health-trend"
        try:
            if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit < 1:
                raise ValueError(f"{command_name} limit must be positive")
            health_dsn, health_table_name = (
                _paper_autonomous_investment_ledger_db_history_health_config_from_env(
                    command_name,
                )
            )
            try:
                report = _run_paper_autonomous_investment_ledger_db_history_health_trend(
                    dsn=health_dsn,
                    table_name=health_table_name,
                    limit=args.limit,
                    runner=(
                        paper_autonomous_investment_ledger_db_history_health_trend_runner
                    ),
                )
            except Exception as exc:
                raise _redacted_paper_autonomous_investment_ledger_error(
                    exc,
                    broker_dsn=health_dsn,
                    broker_table_name=health_table_name,
                ) from None
            _print_paper_autonomous_investment_ledger_db_history_health_trend_summary(
                report,
            )
            return 0
        except Exception as exc:
            print(
                f"{command_name} failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-autonomous-investment-ledger-db-history-health-trend-gate":
        command_name = "paper-autonomous-investment-ledger-db-history-health-trend-gate"
        try:
            if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit < 1:
                raise ValueError(f"{command_name} limit must be positive")
            health_dsn, health_table_name = (
                _paper_autonomous_investment_ledger_db_history_health_config_from_env(
                    command_name,
                )
            )
            try:
                report = (
                    _run_paper_autonomous_investment_ledger_db_history_health_trend_gate(
                        dsn=health_dsn,
                        table_name=health_table_name,
                        limit=args.limit,
                        runner=(
                            paper_autonomous_investment_ledger_db_history_health_trend_gate_runner
                        ),
                    )
                )
            except Exception as exc:
                raise _redacted_paper_autonomous_investment_ledger_error(
                    exc,
                    broker_dsn=health_dsn,
                    broker_table_name=health_table_name,
                ) from None
            _print_paper_autonomous_investment_ledger_db_history_health_trend_gate_summary(
                report,
            )
            return 0
        except Exception as exc:
            print(
                f"{command_name} failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-autonomous-readiness-digest":
        command_name = "paper-autonomous-readiness-digest"
        try:
            _require_paper_autonomous_readiness_digest_limit(args.limit)
            readiness_gate_db_config = from_paper_autonomous_readiness_gate_db_env()
            if not readiness_gate_db_config.enabled:
                raise ValueError(
                    f"{command_name} requires paper autonomous readiness gate DB "
                    "to be enabled",
                )
            dsn = readiness_gate_db_config.dsn
            if dsn is None:
                raise ValueError(
                    f"{command_name} requires a paper autonomous readiness gate DB DSN",
                )
            digest_db_config = None
            digest_dsn = None
            if args.persist:
                digest_db_config = from_paper_autonomous_readiness_digest_db_env()
                if not digest_db_config.enabled:
                    raise ValueError(
                        f"{command_name} --persist requires paper autonomous "
                        "readiness digest DB to be enabled",
                    )
                digest_dsn = digest_db_config.dsn
                if digest_dsn is None:
                    raise ValueError(
                        f"{command_name} --persist requires a paper autonomous "
                        "readiness digest DB DSN",
                    )
            agreement_db_config = from_probability_selection_scorer_agreement_db_env()
            agreement_dsn = agreement_db_config.dsn
            if agreement_db_config.enabled:
                if agreement_dsn is None:
                    raise ValueError(
                        f"{PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR} "
                        "must be set when DB is enabled",
                    )
                validate_local_postgres_dsn(
                    agreement_dsn,
                    env_var_name=(
                        PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR
                    ),
                )
            try:
                report = _run_paper_autonomous_readiness_digest(
                    dsn=dsn,
                    table_name=readiness_gate_db_config.table_name,
                    limit=args.limit,
                    runner=paper_autonomous_readiness_digest_runner,
                    agreement_dsn=agreement_dsn if agreement_db_config.enabled else None,
                    agreement_table_name=(
                        agreement_db_config.table_name
                        if agreement_db_config.enabled
                        else None
                    ),
                )
            except Exception as exc:
                raise _redacted_paper_readiness_digest_error(
                    exc,
                    readiness_dsn=dsn,
                    readiness_table_name=readiness_gate_db_config.table_name,
                    agreement_dsn=(
                        agreement_dsn if agreement_db_config.enabled else None
                    ),
                    agreement_table_name=(
                        agreement_db_config.table_name
                        if agreement_db_config.enabled
                        else None
                    ),
                    digest_dsn=digest_dsn,
                    digest_table_name=(
                        digest_db_config.table_name
                        if digest_db_config is not None
                        else None
                    ),
                ) from None
            _print_paper_autonomous_readiness_digest_summary(report)
            if args.persist:
                if digest_db_config is None or digest_dsn is None:
                    raise ValueError(
                        f"{command_name} --persist requires paper autonomous "
                        "readiness digest DB config",
                    )
                if paper_autonomous_readiness_digest_db_sink is None:
                    from polymarket_alpha_lab.paper_autonomous_readiness_digest_psycopg import (
                        insert_paper_autonomous_readiness_digest_report_with_psycopg,
                    )

                    digest_sink = (
                        insert_paper_autonomous_readiness_digest_report_with_psycopg
                    )
                else:
                    digest_sink = paper_autonomous_readiness_digest_db_sink
                try:
                    sink_result = digest_sink(
                        dsn=digest_dsn,
                        report=report,
                        table_name=digest_db_config.table_name,
                    )
                except Exception as exc:
                    raise _redacted_paper_readiness_digest_error(
                        exc,
                        readiness_dsn=dsn,
                        readiness_table_name=readiness_gate_db_config.table_name,
                        agreement_dsn=(
                            agreement_dsn if agreement_db_config.enabled else None
                        ),
                        agreement_table_name=(
                            agreement_db_config.table_name
                            if agreement_db_config.enabled
                            else None
                        ),
                        digest_dsn=digest_dsn,
                        digest_table_name=digest_db_config.table_name,
                    ) from None
                persisted = getattr(sink_result, "inserted", True)
                if type(persisted) is not bool:
                    persisted = True
                print(f"{command_name}: persisted={persisted}")
            return 0
        except Exception as exc:
            print(
                f"{command_name} failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "paper-research-packet-operator-flow":
        try:
            if isinstance(args.limit, bool) or type(args.limit) is not int or args.limit < 1:
                raise ValueError(
                    "paper-research-packet-operator-flow limit must be positive",
                )
            if (
                isinstance(args.quality_history_limit, bool)
                or type(args.quality_history_limit) is not int
                or args.quality_history_limit < 1
            ):
                raise ValueError(
                    "paper-research-packet-operator-flow quality history "
                    "limit must be positive",
                )
            source_db_config = from_strategy_candidate_research_queue_db_env()
            packet_db_config = from_paper_research_packet_db_env()
            quality_db_config = from_paper_research_packet_quality_db_env()
            operator_flow_db_config = (
                from_paper_research_packet_operator_flow_db_env()
            )
            operator_flow_dsn = operator_flow_db_config.dsn
            if operator_flow_db_config.enabled and operator_flow_dsn is None:
                raise ValueError(
                    "POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN "
                    "must be set when DB is enabled",
                )
            if not source_db_config.enabled:
                raise ValueError(
                    "paper-research-packet-operator-flow requires "
                    "strategy candidate research queue read-only DB config "
                    "to be enabled",
                )
            source_dsn = source_db_config.dsn
            if source_dsn is None:
                raise ValueError(
                    "paper-research-packet-operator-flow requires "
                    "a source DB DSN",
                )
            if not packet_db_config.enabled:
                raise ValueError(
                    "paper-research-packet-operator-flow requires "
                    "paper research packet DB to be enabled",
                )
            packet_dsn = packet_db_config.dsn
            if packet_dsn is None:
                raise ValueError(
                    "paper-research-packet-operator-flow requires "
                    "a paper research packet DB DSN",
                )
            if not quality_db_config.enabled:
                raise ValueError(
                    "paper-research-packet-operator-flow requires "
                    "paper research packet quality DB to be enabled",
                )
            quality_dsn = quality_db_config.dsn
            if quality_dsn is None:
                raise ValueError(
                    "paper-research-packet-operator-flow requires "
                    "a paper research packet quality DB DSN",
                )
            try:
                packet_report, packet_persisted = _run_paper_research_packet(
                    source_config_version=args.source_config_version,
                    action_status=args.action_status,
                    research_status=args.research_status,
                    limit=args.limit,
                    packet_config_version=args.packet_config_version,
                    max_packet_rows=args.max_packet_rows,
                    min_score=args.min_score,
                    persist=True,
                    loader=strategy_candidate_research_queue_loader,
                    packet_builder=paper_research_packet_builder,
                    packet_db_sink=paper_research_packet_db_sink,
                )
                quality_report = _run_paper_research_packet_quality(
                    dsn=packet_dsn,
                    table_name=packet_db_config.table_name,
                    persist=True,
                    quality_db_config=quality_db_config,
                    runner=paper_research_packet_quality_runner,
                )
                history_report = _run_paper_research_packet_quality_db_history(
                    dsn=quality_dsn,
                    table_name=quality_db_config.table_name,
                    limit=args.quality_history_limit,
                    runner=paper_research_packet_quality_db_history_runner,
                )
                operator_flow_report = build_paper_research_packet_operator_flow_report(
                    packet_report=packet_report,
                    packet_persisted=packet_persisted,
                    quality_report=quality_report,
                    quality_persisted=True,
                    quality_history_report=history_report,
                    config=PaperResearchPacketOperatorFlowConfig(),
                    generated_at=datetime.now(UTC),
                )
                if operator_flow_db_config.enabled:
                    if paper_research_packet_operator_flow_db_sink is None:
                        from polymarket_alpha_lab.paper_research_packet_operator_flow_psycopg import (
                            insert_paper_research_packet_operator_flow_report_with_psycopg,
                        )

                        operator_flow_sink = (
                            insert_paper_research_packet_operator_flow_report_with_psycopg
                        )
                    else:
                        operator_flow_sink = paper_research_packet_operator_flow_db_sink
                    operator_flow_sink(
                        dsn=operator_flow_dsn,
                        report=operator_flow_report,
                        table_name=operator_flow_db_config.table_name,
                    )
            except Exception as exc:
                raise _redacted_paper_research_packet_operator_flow_error(
                    exc,
                    source_dsn=source_dsn,
                    source_table_name=source_db_config.table_name,
                    packet_dsn=packet_dsn,
                    packet_table_name=packet_db_config.table_name,
                    quality_dsn=quality_dsn,
                    quality_table_name=quality_db_config.table_name,
                    operator_flow_dsn=operator_flow_dsn,
                    operator_flow_table_name=operator_flow_db_config.table_name,
                ) from None
            _print_paper_research_packet_operator_flow_summary(
                operator_flow_report,
            )
            _print_paper_research_packet_summary(
                packet_report,
                persisted=packet_persisted,
            )
            _print_paper_research_packet_quality_summary(
                quality_report,
                persisted=True,
            )
            _print_paper_research_packet_quality_db_history_summary(history_report)
            return 0
        except Exception as exc:
            print(
                f"paper-research-packet-operator-flow failed: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.command == "run":
        try:
            cycle_snapshot_db_config = from_cycle_snapshot_db_env()
            paper_strategy_cycle_report_db_config = (
                from_paper_strategy_cycle_report_db_env()
            )
            action_gated_queue_db_config = (
                from_action_gated_strategy_recommendation_queue_db_env()
            )
            paper_trade_db_config = from_paper_trade_journal_db_env()
            paper_nav_db_config = from_paper_nav_snapshot_db_env()
            run_cycle_report_sink = None
            run_cycle_snapshot_source = None
            run_cycle_snapshot_sink = None
            run_action_gated_queue_source = None
            run_action_gated_queue_sink = None
            run_paper_trade_record_sink = None
            run_nav_snapshot_sink = None
            if paper_strategy_cycle_report_db_config.enabled:
                dsn = paper_strategy_cycle_report_db_config.dsn
                if dsn is None:
                    raise ValueError(
                        "paper strategy cycle report DB persistence requires a DB DSN",
                    )

                def run_cycle_report_sink(
                    report: PaperStrategyCycleReport,
                    *,
                    db_dsn: str = dsn,
                    table_name: str = (
                        paper_strategy_cycle_report_db_config.table_name
                    ),
                ) -> object:
                    try:
                        return paper_strategy_cycle_report_db_sink(
                            dsn=db_dsn,
                            report=report,
                            table_name=table_name,
                        )
                    except Exception as exc:
                        _raise_redacted_db_sink_error(
                            exc,
                            dsn=db_dsn,
                            table_name=table_name,
                        )

            if cycle_snapshot_db_config.enabled:
                dsn = cycle_snapshot_db_config.dsn
                if dsn is None:
                    raise ValueError(
                        "cycle snapshot DB persistence requires a DB DSN",
                    )

                def run_cycle_snapshot_sink(
                    report: object,
                    *,
                    db_dsn: str = dsn,
                    table_name: str = cycle_snapshot_db_config.table_name,
                ) -> object:
                    try:
                        return cycle_snapshot_db_sink(
                            dsn=db_dsn,
                            report=report,
                            table_name=table_name,
                        )
                    except Exception as exc:
                        _raise_redacted_db_sink_error(exc, dsn=db_dsn)

                run_cycle_snapshot_source = (
                    cycle_snapshot_source
                    if cycle_snapshot_source is not None
                    else build_strategy_cycle_snapshot_source_report
                )
            if action_gated_queue_db_config.enabled:
                dsn = action_gated_queue_db_config.dsn
                if dsn is None:
                    raise ValueError(
                        "action-gated queue DB persistence requires a DB DSN",
                    )

                def run_action_gated_queue_sink(
                    report: object,
                    *,
                    db_dsn: str = dsn,
                    table_name: str = action_gated_queue_db_config.table_name,
                ) -> object:
                    try:
                        return action_gated_queue_db_sink(
                            dsn=db_dsn,
                            report=report,
                            table_name=table_name,
                        )
                    except Exception as exc:
                        _raise_redacted_db_sink_error(exc, dsn=db_dsn)

                run_action_gated_queue_source = (
                    action_gated_queue_source
                    if action_gated_queue_source is not None
                    else build_strategy_cycle_action_gated_queue_source_report
                )
            if paper_trade_db_config.enabled:
                dsn = paper_trade_db_config.dsn
                if dsn is None:
                    raise ValueError(
                        "paper trade journal DB persistence requires a DB DSN",
                    )

                def run_paper_trade_record_sink(
                    record: object,
                    *,
                    db_dsn: str = dsn,
                    table_name: str = paper_trade_db_config.table_name,
                ) -> object:
                    try:
                        return paper_trade_record_db_sink(
                            dsn=db_dsn,
                            record=record,
                            table_name=table_name,
                        )
                    except Exception as exc:
                        _raise_redacted_db_sink_error(exc, dsn=db_dsn)

            if paper_nav_db_config.enabled:
                dsn = paper_nav_db_config.dsn
                if dsn is None:
                    raise ValueError(
                        "paper NAV snapshot DB persistence requires a DB DSN",
                    )

                def run_nav_snapshot_sink(
                    snapshot: PaperNavSnapshot,
                    *,
                    db_dsn: str = dsn,
                    table_name: str = paper_nav_db_config.table_name,
                ) -> object:
                    try:
                        return paper_nav_snapshot_db_sink(
                            dsn=db_dsn,
                            snapshot=snapshot,
                            table_name=table_name,
                        )
                    except Exception as exc:
                        _raise_redacted_db_sink_error(exc, dsn=db_dsn)
            scan_config = MarketScanConfig(
                limit=args.limit,
                archive_root=args.archive_root,
                output_path=args.cycle_log,
                fetch_books=True,
            )
            cycle_config = _build_default_cycle_config(
                max_markets_per_cycle=args.max_markets,
                prefilter_by_score=args.prefilter,
                paper_execute=args.paper_execute,
                paper_journal=args.paper_journal,
                forecast_provider=args.forecast_provider,
                llm_api_token=args.llm_api_token,
            )
            repeat_mode = "interval" if args.repeat_interval > 0 else "once"
            if args.strategy_audit_preflight:
                if args.nav_log is None:
                    raise ValueError("strategy audit preflight requires --nav-log")
                audit_report = _run_strategy_audit(
                    cycle_log=args.cycle_log,
                    trade_log=args.paper_journal,
                    nav_log=args.nav_log,
                    outcome_log=args.outcome_log,
                    runner=strategy_audit_runner,
                )
                if args.strategy_audit_log is not None:
                    PaperStrategyRiskAuditLog(args.strategy_audit_log).append(
                        audit_report,
                    )
                _print_strategy_audit_summary(audit_report)
                if audit_report.status != "audit_ready":
                    print(
                        "run blocked by strategy audit preflight: "
                        f"status={audit_report.status}",
                        file=sys.stderr,
                    )
                    return 1
            loop_runner_kwargs = {
                "client": client_factory(),
                "scan_config": scan_config,
                "cycle_config": cycle_config,
                "starting_cash": args.starting_cash,
                "nav_log_path": args.nav_log,
                "cycle_report_log_path": args.cycle_log,
                "repeat_mode": repeat_mode,
                "interval_seconds": args.repeat_interval,
                "max_iterations": args.max_iterations,
                "cycle_report_sink": run_cycle_report_sink,
                "cycle_snapshot_source": run_cycle_snapshot_source,
                "cycle_snapshot_sink": run_cycle_snapshot_sink,
                "paper_trade_record_sink": run_paper_trade_record_sink,
                "nav_snapshot_sink": run_nav_snapshot_sink,
            }
            execution_pipeline_db_config = from_paper_execution_pipeline_db_env()
            if execution_pipeline_db_config.enabled:
                screening_gate_db_config = (
                    from_paper_autonomous_screening_decision_support_gate_db_env()
                )
                if not screening_gate_db_config.enabled:
                    raise ValueError(
                        "execution pipeline run persistence requires "
                        "autonomous screening gate DB to be enabled",
                    )
                screening_gate_dsn = screening_gate_db_config.dsn
                if screening_gate_dsn is None:
                    raise ValueError(
                        "execution pipeline run persistence requires "
                        "an autonomous screening gate DB DSN",
                    )
                execution_pipeline_dsn = execution_pipeline_db_config.dsn
                if execution_pipeline_dsn is None:
                    raise ValueError(
                        "execution pipeline DB persistence requires a DB DSN",
                    )
                execution_pipeline_table_name = execution_pipeline_db_config.table_name
                paper_broker_db_config = from_paper_broker_db_env()
                broker_dsn = paper_broker_db_config.dsn
                broker_table_name = paper_broker_db_config.table_name
                if paper_broker_db_config.enabled and broker_dsn is None:
                    raise ValueError("paper broker DB persistence requires a DB DSN")
                investment_ledger_db_config = (
                    from_paper_autonomous_investment_ledger_db_env()
                )
                ledger_dsn = investment_ledger_db_config.dsn
                ledger_table_name = investment_ledger_db_config.table_name
                if investment_ledger_db_config.enabled and ledger_dsn is None:
                    raise ValueError(
                        "paper autonomous investment ledger DB persistence "
                        "requires a DB DSN",
                    )
                pipeline_runner = (
                    paper_execution_pipeline_runner
                    if paper_execution_pipeline_runner is not None
                    else _run_paper_execution_pipeline
                )
                pipeline_persister = (
                    paper_execution_pipeline_persister
                    if paper_execution_pipeline_persister is not None
                    else _persist_paper_execution_pipeline
                )

                def _run_execution_pipeline_source(
                    cycle_report: object,
                    iteration_started_at: object,
                    *,
                    _screening_gate_dsn: str = screening_gate_dsn,
                    _screening_gate_table_name: str = (
                        screening_gate_db_config.table_name
                    ),
                ) -> object:
                    return pipeline_runner(
                        screening_gate_dsn=_screening_gate_dsn,
                        screening_gate_table_name=_screening_gate_table_name,
                        limit=1,
                    )

                def _run_execution_pipeline_sink(
                    pipeline_report: object,
                    *,
                    _execution_pipeline_dsn: str = execution_pipeline_dsn,
                    _execution_pipeline_table_name: str = (
                        execution_pipeline_table_name
                    ),
                    _broker_dsn: str | None = (
                        broker_dsn if paper_broker_db_config.enabled else None
                    ),
                    _broker_table_name: str | None = (
                        broker_table_name if paper_broker_db_config.enabled else None
                    ),
                    _ledger_dsn: str | None = (
                        ledger_dsn if investment_ledger_db_config.enabled else None
                    ),
                    _ledger_table_name: str | None = (
                        ledger_table_name
                        if investment_ledger_db_config.enabled
                        else None
                    ),
                ) -> None:
                    try:
                        persister_kwargs = {
                            "pipeline_report": pipeline_report,
                            "dsn": _execution_pipeline_dsn,
                            "table_name": _execution_pipeline_table_name,
                        }
                        if _broker_dsn is not None and _broker_table_name is not None:
                            persister_kwargs["broker_dsn"] = _broker_dsn
                            persister_kwargs["broker_table_name"] = _broker_table_name
                        if _ledger_dsn is not None and _ledger_table_name is not None:
                            persister_kwargs["ledger_dsn"] = _ledger_dsn
                            persister_kwargs["ledger_table_name"] = _ledger_table_name
                        pipeline_persister(**persister_kwargs)
                    except Exception as exc:
                        _raise_redacted_multi_db_sink_error(
                            exc,
                            dsns=(
                                _execution_pipeline_dsn,
                                _broker_dsn,
                                _ledger_dsn,
                            ),
                        )

                loop_runner_kwargs["execution_pipeline_source"] = (
                    _run_execution_pipeline_source
                )
                loop_runner_kwargs["execution_pipeline_sink"] = (
                    _run_execution_pipeline_sink
                )
            if action_gated_queue_db_config.enabled:
                loop_runner_kwargs["action_gated_queue_source"] = (
                    run_action_gated_queue_source
                )
                loop_runner_kwargs["action_gated_queue_sink"] = (
                    run_action_gated_queue_sink
                )
            summary = loop_runner(**loop_runner_kwargs)
            _print_run_loop_summary(summary)
            return 0
        except Exception as exc:
            print(f"run failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "search":
        try:
            client = client_factory()
            payload = client.list_markets(
                active=not args.closed,
                closed=args.closed,
                limit=args.limit,
                search=args.query,
            )
            if isinstance(payload, list):
                for m in payload:
                    slug = m.get("slug", "?") if isinstance(m, dict) else "?"
                    q = m.get("question", "?") if isinstance(m, dict) else "?"
                    outs = m.get("outcomes", []) if isinstance(m, dict) else []
                    print(f"{slug}: {q} [{', '.join(str(o) for o in outs)}]")
                print(f"\n{len(payload) if isinstance(payload, list) else 0} markets found")
            else:
                print("unexpected response format")
            return 0
        except Exception as exc:
            print(f"search failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "check-outcomes":
        try:
            outcome_tracking_db_config = from_outcome_tracking_db_env()
            report = outcome_runner(
                client=client_factory(),
                journal_path=args.journal,
                config=OutcomeTrackingConfig(
                    config_version="outcome-tracker-v1",
                ),
                generated_at=datetime.now(UTC),
            )
            if (
                args.evidence_log is not None
                and report.forecast_evidence_report is not None
            ):
                PaperForecastEvidenceLog(args.evidence_log).append(
                    report.forecast_evidence_report,
                )
            if args.outcome_log is not None:
                OutcomeTrackingLog(args.outcome_log).append(report)
            if outcome_tracking_db_config.enabled:
                dsn = outcome_tracking_db_config.dsn
                if dsn is None:
                    raise ValueError(
                        "outcome tracking DB persistence requires a DB DSN",
                    )
                try:
                    outcome_tracking_db_sink(
                        dsn=dsn,
                        report=report,
                        table_name=outcome_tracking_db_config.table_name,
                    )
                except Exception as exc:
                    _raise_redacted_db_sink_error(exc, dsn=dsn)
            _print_outcome_tracking_summary(report)
            return 0
        except Exception as exc:
            print(f"check-outcomes failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "outcome-tracking-db-history":
        try:
            if args.limit <= 0:
                raise ValueError("outcome-tracking-db-history limit must be positive")
            outcome_tracking_db_config = from_outcome_tracking_db_env()
            if not outcome_tracking_db_config.enabled:
                raise ValueError(
                    "outcome-tracking-db-history requires outcome tracking "
                    "DB to be enabled",
                )
            dsn = outcome_tracking_db_config.dsn
            if dsn is None:
                raise ValueError(
                    "outcome-tracking-db-history requires an outcome tracking "
                    "DB DSN",
                )
            try:
                report = _run_outcome_tracking_db_history(
                    dsn=dsn,
                    table_name=outcome_tracking_db_config.table_name,
                    limit=args.limit,
                    stale_after_seconds=args.stale_after_seconds,
                    runner=outcome_tracking_db_history_runner,
                )
            except Exception as exc:
                _raise_redacted_db_read_error(exc, dsn=dsn)
            _print_outcome_tracking_db_history_summary(report)
            return 0
        except Exception as exc:
            print(f"outcome-tracking-db-history failed: {exc}", file=sys.stderr)
            return 1

    return 2


def _build_default_cycle_config(
    *,
    max_markets_per_cycle: int,
    prefilter_by_score: bool,
    paper_execute: bool = False,
    paper_journal: Path | None = None,
    forecast_provider: str = "naive",
    llm_api_token: str | None = None,
) -> PaperStrategyCycleConfig:
    """Assemble the frozen paper-only cycle config used by the strategy-cycle CLI.

    All nested configs use the same canonical ``config_version`` and rely on
    their dataclass defaults except ``cost_assumptions`` (no defaults), which
    is given realistic Polymarket fee assumptions via
    ``polymarket_default_cost_assumptions`` (2% taker fee + small slippage).
    When ``paper_execute`` is set, the Stage 4 inline paper-execution pass is
    enabled with the canonical ``PaperExecutionConfig`` and the journal sink.
    When ``forecast_provider`` is ``llm`` and ``llm_api_token`` is supplied, a
    caller-supplied ``GLMChatTransport`` is wired alongside the canonical
    ``PaperLLMForecastConfig`` (the token is never read from env/disk here).
    """

    base = PaperStrategyCycleConfig(
        config_version="strategy-cycle-v1",
        forecast_config=PaperForecastConfig(config_version="strategy-cycle-v1"),
        snapshot_config=PaperCostAwareSnapshotConfig(
            config_version="strategy-cycle-v1",
        ),
        strategy_config=PaperCostAwareEventStrategyConfig(
            config_version="strategy-cycle-v1",
        ),
        screening_config=PaperProjectScreeningConfig(
            config_version="strategy-cycle-v1",
        ),
        cost_assumptions=polymarket_default_cost_assumptions(),
        max_markets_per_cycle=max_markets_per_cycle,
        prefilter_by_score=prefilter_by_score,
    )
    if forecast_provider == "llm" and llm_api_token:
        base = replace(
            base,
            forecast_provider="llm",
            llm_transport=GLMChatTransport(api_token=llm_api_token),
            llm_forecast_config=PaperLLMForecastConfig(
                config_version="strategy-cycle-v1",
            ),
        )
    if not paper_execute:
        return base
    journal_path = paper_journal if paper_journal is not None else Path(
        "artifacts/paper-trades.jsonl",
    )
    return replace(
        base,
        paper_execution_config=PaperExecutionConfig(
            config_version="paper-execution-v1",
        ),
        paper_trade_journal_path=journal_path,
    )


def _print_strategy_cycle_summary(report: PaperStrategyCycleReport) -> None:
    """Print a human-readable summary of one strategy-cycle run to stdout.

    Handles a ``screening_report`` of ``None`` (naive forecast defers/blocks
    every market) and a screening queue with few/no ``research_ready`` items.
    """

    print(
        "strategy-cycle: "
        f"scanned={report.scan_market_count} "
        f"considered={report.considered_count} "
        f"snapshot_ready={report.snapshot_ready_count} "
        f"cost_aware_reports={report.cost_aware_report_count}",
    )
    if report.blocked_counts:
        blocked_text = ", ".join(
            f"{status}={count}" for status, count in report.blocked_counts
        )
        print(f"blocked: {blocked_text}")
    screening = report.screening_report
    if screening is None:
        return
    print(
        "screening: "
        f"ready={screening.ready_count} "
        f"watch={screening.watch_count} "
        f"defer={screening.defer_count} "
        f"blocked={screening.blocked_count}",
    )
    for item in screening.queue_items[:5]:
        print(
            f"  #{item.queue_position} [{item.research_bucket}] "
            f"{item.market_slug} score={item.screening_score}",
        )


def _print_portfolio_nav_summary(snapshot: PaperNavSnapshot) -> None:
    """Print a human-readable NAV summary (starting cash, balances, P&L)."""

    print(
        "portfolio-nav: "
        f"starting_cash={snapshot.starting_cash} "
        f"cash_balance={snapshot.cash_balance} "
        f"realized_pnl={snapshot.realized_pnl} "
        f"exit_nav={snapshot.exit_nav} "
        f"unrealized_pnl={snapshot.unrealized_exit_pnl} "
        f"position_count={len(snapshot.marks)}",
    )


def _run_history(
    *,
    cycle_log: Path,
    trade_log: Path,
    nav_log: Path,
    runner: HistoryRunner | None,
) -> PerformanceSummary:
    """Read the three JSONL history logs and build a performance summary.

    When ``runner`` is supplied (for tests), it is called with the three paths
    and returns the summary directly -- no file reads. Otherwise the default
    reads each JSONL log via its typed reader and aggregates via
    ``build_performance_summary``. ``generated_at`` is stamped now.
    """
    generated_at = datetime.now(UTC)
    config = PerformanceSummaryConfig(config_version="performance-summary-v1")
    if runner is not None:
        return runner(
            cycle_log=cycle_log,
            trade_log=trade_log,
            nav_log=nav_log,
            config=config,
            generated_at=generated_at,
        )
    cycle_reports = PaperStrategyCycleLog.read(cycle_log)
    trade_records = PaperTradeJournal.read(trade_log)
    nav_snapshots = PaperNavLog.read(nav_log)
    return build_performance_summary(
        cycle_reports,
        trade_records,
        nav_snapshots,
        config=config,
        generated_at=generated_at,
    )


def _run_nav_risk(
    *,
    nav_log: Path,
    runner: NavRiskRunner | None,
) -> "PaperNavRiskMetricsReport":
    """Read typed NAV snapshots and build the paper-only risk report."""

    from polymarket_alpha_lab.nav_risk_metrics import (
        PaperNavRiskMetricsConfig,
        build_paper_nav_risk_metrics_report,
    )

    nav_snapshots = PaperNavLog.read(nav_log)
    config = PaperNavRiskMetricsConfig(config_version="nav-risk-metrics-v0")
    generated_at = datetime.now(UTC)
    if runner is not None:
        return runner(
            nav_snapshots=nav_snapshots,
            config=config,
            generated_at=generated_at,
        )
    return build_paper_nav_risk_metrics_report(
        nav_snapshots,
        config=config,
        generated_at=generated_at,
    )


def _run_nav_snapshot_db_trend(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: NavSnapshotDbTrendRunner | None,
) -> PaperNavRiskTrendReport:
    generated_at = datetime.now(UTC)
    config_version = "nav-snapshot-db-trend-v0"
    if runner is not None:
        return runner(
            dsn=dsn,
            table_name=table_name,
            limit=limit,
            config_version=config_version,
            generated_at=generated_at,
        )

    from polymarket_alpha_lab.paper_nav_snapshot_db_trend_load import (
        load_paper_nav_snapshot_db_trend_report,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the NAV snapshot DB trend "
            "psycopg adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(dsn)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper NAV snapshot database",
        ) from None
    try:
        report = load_paper_nav_snapshot_db_trend_report(
            generated_at=generated_at,
            config_version=config_version,
            connection=connection,
            limit=limit,
            table_name=table_name,
        )
        connection.commit()
        return report
    except BaseException:
        try:
            connection.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _run_cycle_snapshot_db_trend(
    *,
    source_config_version: str | None,
    limit: int,
    runner: CycleSnapshotDbTrendRunner | None,
) -> object:
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")
    db_config = from_cycle_snapshot_db_env()
    if not db_config.enabled:
        raise ValueError("cycle-snapshot-db-trend requires cycle snapshot DB to be enabled")
    if db_config.dsn is None:
        raise ValueError("cycle-snapshot-db-trend requires a DB DSN")
    generated_at = datetime.now(UTC)
    config_version = "cycle-snapshot-db-trend-v0"
    if runner is not None:
        return runner(
            dsn=db_config.dsn,
            generated_at=generated_at,
            config_version=config_version,
            source_config_version=source_config_version,
            limit=limit,
            table_name=db_config.table_name,
        )
    snapshots = load_paper_recommendation_cycle_snapshots_with_psycopg(
        db_config.dsn,
        config_version=source_config_version,
        limit=limit,
        table_name=db_config.table_name,
    )
    if not snapshots:
        raise ValueError("no paper recommendation cycle snapshots found")
    # Store-backed loaders return newest-first; the trend builder expects
    # chronological input so equal-timestamp latest-status tie handling is stable.
    return build_paper_recommendation_cycle_snapshot_trend_report(
        generated_at=generated_at,
        config_version=config_version,
        snapshots=tuple(reversed(snapshots)),
    )


def _run_cycle_snapshot_db_review(
    *,
    source_config_version: str | None,
    limit: int,
    stale_after_hours: Decimal,
    runner: CycleSnapshotDbReviewRunner | None,
) -> object:
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")
    db_config = from_cycle_snapshot_db_env()
    if not db_config.enabled:
        raise ValueError(
            "paper-recommendation-cycle-review requires cycle snapshot DB to be enabled",
        )
    if db_config.dsn is None:
        raise ValueError("paper-recommendation-cycle-review requires a DB DSN")
    generated_at = datetime.now(UTC)
    config = PaperRecommendationCycleReviewConfig(
        config_version="paper-recommendation-cycle-review-v0",
        stale_after_hours=stale_after_hours.quantize(Decimal("0.000001")),
    )
    if runner is not None:
        try:
            return runner(
                dsn=db_config.dsn,
                generated_at=generated_at,
                config=config,
                source_config_version=source_config_version,
                limit=limit,
                table_name=db_config.table_name,
            )
        except Exception as exc:
            _raise_redacted_db_sink_error(exc, dsn=db_config.dsn)
    try:
        snapshots = load_paper_recommendation_cycle_snapshots_with_psycopg(
            db_config.dsn,
            config_version=source_config_version,
            limit=limit,
            table_name=db_config.table_name,
        )
    except Exception as exc:
        _raise_redacted_db_sink_error(exc, dsn=db_config.dsn)
    return build_paper_recommendation_cycle_review_report(
        tuple(reversed(snapshots)),
        config=config,
        generated_at=generated_at,
    )


def _run_cycle_snapshot_db_action_gate(
    *,
    source_config_version: str | None,
    limit: int,
    stale_after_hours: Decimal,
    runner: CycleSnapshotDbActionGateRunner | None,
) -> object:
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")
    db_config = from_cycle_snapshot_db_env()
    if not db_config.enabled:
        raise ValueError(
            "paper-recommendation-cycle-action-gate requires "
            "cycle snapshot DB to be enabled",
        )
    if db_config.dsn is None:
        raise ValueError("paper-recommendation-cycle-action-gate requires a DB DSN")
    generated_at = datetime.now(UTC)
    review_config = PaperRecommendationCycleReviewConfig(
        config_version="paper-recommendation-cycle-review-v0",
        stale_after_hours=stale_after_hours.quantize(Decimal("0.000001")),
    )
    action_gate_config = PaperRecommendationCycleActionGateConfig(
        config_version="paper-recommendation-cycle-action-gate-v0",
    )
    if runner is not None:
        try:
            return runner(
                dsn=db_config.dsn,
                generated_at=generated_at,
                review_config=review_config,
                action_gate_config=action_gate_config,
                source_config_version=source_config_version,
                limit=limit,
                table_name=db_config.table_name,
            )
        except Exception as exc:
            _raise_redacted_db_sink_error(exc, dsn=db_config.dsn)
    try:
        snapshots = load_paper_recommendation_cycle_snapshots_with_psycopg(
            db_config.dsn,
            config_version=source_config_version,
            limit=limit,
            table_name=db_config.table_name,
        )
    except Exception as exc:
        _raise_redacted_db_sink_error(exc, dsn=db_config.dsn)
    review_report = build_paper_recommendation_cycle_review_report(
        tuple(reversed(snapshots)),
        config=review_config,
        generated_at=generated_at,
    )
    return build_paper_recommendation_cycle_action_gate_report(
        review_report,
        config=action_gate_config,
        generated_at=generated_at,
    )


def _run_action_gated_queue_decision_support(
    *,
    source_config_version: str | None,
    action_status: str | None,
    limit: int,
    max_total_ready_notional: Decimal,
    max_single_queue_ready_notional: Decimal,
    max_ready_candidate_count: int,
    max_total_candidate_count: int,
    throttle_utilization_threshold: Decimal,
    loader: ActionGatedQueueLoader | None,
    priority_builder: ActionGatedQueuePriorityBuilder | None,
    risk_builder: ActionGatedQueueRiskBuilder | None,
) -> tuple[object, object]:
    from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_priority import (
        build_paper_action_gated_strategy_recommendation_queue_priority_report,
    )
    from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_psycopg_read import (
        PaperActionGatedStrategyRecommendationQueueReadOptions,
        load_paper_action_gated_strategy_recommendation_queue_reports_with_psycopg,
    )
    from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_risk import (
        PaperActionGatedStrategyRecommendationQueueRiskConfig,
        build_paper_action_gated_strategy_recommendation_queue_risk_report,
    )

    db_config = from_action_gated_strategy_recommendation_queue_db_env()
    if not db_config.enabled:
        raise ValueError(
            "action-gated-queue-decision-support requires action-gated queue "
            "read-only DB config to be enabled",
        )
    if db_config.dsn is None:
        raise ValueError("action-gated-queue-decision-support requires a DB DSN")

    read_options = PaperActionGatedStrategyRecommendationQueueReadOptions(
        source_config_version=source_config_version,
        action_status=action_status,
        limit=limit,
        table_name=db_config.table_name,
    )
    risk_config = PaperActionGatedStrategyRecommendationQueueRiskConfig(
        config_version="action-gated-queue-risk-v0",
        max_total_ready_notional=max_total_ready_notional,
        max_single_queue_ready_notional=max_single_queue_ready_notional,
        max_ready_candidate_count=max_ready_candidate_count,
        max_total_candidate_count=max_total_candidate_count,
        throttle_utilization_threshold=throttle_utilization_threshold,
    )
    generated_at = datetime.now(UTC)
    resolved_loader = (
        loader
        if loader is not None
        else load_paper_action_gated_strategy_recommendation_queue_reports_with_psycopg
    )
    resolved_priority_builder = (
        priority_builder
        if priority_builder is not None
        else build_paper_action_gated_strategy_recommendation_queue_priority_report
    )
    resolved_risk_builder = (
        risk_builder
        if risk_builder is not None
        else build_paper_action_gated_strategy_recommendation_queue_risk_report
    )

    try:
        queue_reports = resolved_loader(db_config.dsn, options=read_options)
    except Exception as exc:
        _raise_redacted_db_read_error(exc, dsn=db_config.dsn)

    priority_report = resolved_priority_builder(
        queue_reports,
        generated_at=generated_at,
    )
    risk_report = resolved_risk_builder(
        queue_reports,
        config=risk_config,
        generated_at=generated_at,
    )
    return priority_report, risk_report


def _run_action_gated_queue_history(
    *,
    source_config_version: str | None,
    action_status: str | None,
    limit: int,
    persist: bool,
    loader: ActionGatedQueueLoader | None,
    history_builder: ActionGatedQueueHistoryBuilder | None,
    history_db_sink: ActionGatedQueueHistoryDbSink | None,
) -> tuple[object, bool]:
    from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_history import (
        build_paper_action_gated_strategy_recommendation_queue_history_report,
    )
    from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_psycopg_read import (
        PaperActionGatedStrategyRecommendationQueueReadOptions,
        load_paper_action_gated_strategy_recommendation_queue_reports_with_psycopg,
    )

    db_config = from_action_gated_strategy_recommendation_queue_db_env()
    if not db_config.enabled:
        raise ValueError(
            "action-gated-queue-history requires action-gated queue "
            "read-only DB config to be enabled",
        )
    if db_config.dsn is None:
        raise ValueError("action-gated-queue-history requires a DB DSN")
    history_db_config = (
        from_action_gated_strategy_recommendation_queue_history_db_env()
        if persist
        else None
    )
    if persist:
        if history_db_config is None:
            raise ValueError(
                "action-gated-queue-history persistence requires history DB config",
            )
        if not history_db_config.enabled:
            raise ValueError(
                "action-gated-queue-history persistence requires history DB to be enabled",
            )
        if history_db_config.dsn is None:
            raise ValueError(
                "action-gated-queue-history persistence requires a history DB DSN",
            )

    read_options = PaperActionGatedStrategyRecommendationQueueReadOptions(
        source_config_version=source_config_version,
        action_status=action_status,
        limit=limit,
        table_name=db_config.table_name,
    )
    generated_at = datetime.now(UTC)
    resolved_loader = (
        loader
        if loader is not None
        else load_paper_action_gated_strategy_recommendation_queue_reports_with_psycopg
    )
    resolved_history_builder = (
        history_builder
        if history_builder is not None
        else build_paper_action_gated_strategy_recommendation_queue_history_report
    )

    try:
        queue_reports = resolved_loader(db_config.dsn, options=read_options)
    except Exception as exc:
        message = _redact_db_dsn(str(exc), dsn=db_config.dsn)
        if not message.strip():
            message = exc.__class__.__name__
        raise RuntimeError(message) from None

    report = resolved_history_builder(
        queue_reports,
        generated_at=generated_at,
    )
    if not persist:
        return report, False
    if history_db_sink is None:
        from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_history_psycopg import (
            insert_paper_action_gated_strategy_recommendation_queue_history_report_with_psycopg,
        )

        resolved_history_db_sink = (
            insert_paper_action_gated_strategy_recommendation_queue_history_report_with_psycopg
        )
    else:
        resolved_history_db_sink = history_db_sink
    try:
        resolved_history_db_sink(
            dsn=history_db_config.dsn,
            report=report,
            table_name=history_db_config.table_name,
        )
    except Exception as exc:
        message = _redact_db_dsn(str(exc), dsn=history_db_config.dsn)
        message = _redact_db_dsn(message, dsn=db_config.dsn)
        if not message.strip():
            message = exc.__class__.__name__
        raise RuntimeError(message) from None
    return report, True


def _run_strategy_candidate_research_queue_history(
    *,
    source_config_version: str | None,
    action_status: str | None,
    research_status: str | None,
    limit: int,
    persist: bool,
    loader: StrategyCandidateResearchQueueLoader | None,
    history_builder: StrategyCandidateResearchQueueHistoryBuilder | None,
    history_db_sink: StrategyCandidateResearchQueueHistoryDbSink | None,
) -> tuple[object, bool]:
    from polymarket_alpha_lab.strategy_candidate_research_queue_history import (
        build_paper_strategy_candidate_research_queue_history_report,
    )
    from polymarket_alpha_lab.strategy_candidate_research_queue_psycopg_read import (
        PaperStrategyCandidateResearchQueueReadOptions,
        load_paper_strategy_candidate_research_queue_reports_with_psycopg,
    )

    db_config = from_strategy_candidate_research_queue_db_env()
    if not db_config.enabled:
        raise ValueError(
            "strategy-candidate-research-queue-history requires strategy "
            "candidate research queue read-only DB config to be enabled",
        )
    if db_config.dsn is None:
        raise ValueError(
            "strategy-candidate-research-queue-history requires a DB DSN",
        )
    history_db_config = (
        from_strategy_candidate_research_queue_history_db_env() if persist else None
    )
    if persist:
        if history_db_config is None:
            raise ValueError(
                "strategy-candidate-research-queue-history persistence requires "
                "history DB config",
            )
        if not history_db_config.enabled:
            raise ValueError(
                "strategy-candidate-research-queue-history persistence requires "
                "history DB to be enabled",
            )
        if history_db_config.dsn is None:
            raise ValueError(
                "strategy-candidate-research-queue-history persistence requires "
                "a history DB DSN",
            )

    read_options = PaperStrategyCandidateResearchQueueReadOptions(
        source_config_version=source_config_version,
        action_status=action_status,
        research_status=research_status,
        limit=limit,
        table_name=db_config.table_name,
    )
    generated_at = datetime.now(UTC)
    resolved_loader = (
        loader
        if loader is not None
        else load_paper_strategy_candidate_research_queue_reports_with_psycopg
    )
    resolved_history_builder = (
        history_builder
        if history_builder is not None
        else build_paper_strategy_candidate_research_queue_history_report
    )

    try:
        queue_reports = resolved_loader(db_config.dsn, options=read_options)
    except Exception as exc:
        message = _redact_db_dsn(str(exc), dsn=db_config.dsn)
        message = _redact_db_table_name(message, table_name=db_config.table_name)
        if not message.strip():
            message = exc.__class__.__name__
        raise RuntimeError(message) from None

    report = resolved_history_builder(
        queue_reports,
        generated_at=generated_at,
    )
    if not persist:
        return report, False
    if history_db_sink is None:
        from polymarket_alpha_lab.strategy_candidate_research_queue_history_psycopg import (
            insert_paper_strategy_candidate_research_queue_history_report_with_psycopg,
        )

        resolved_history_db_sink = (
            insert_paper_strategy_candidate_research_queue_history_report_with_psycopg
        )
    else:
        resolved_history_db_sink = history_db_sink
    try:
        resolved_history_db_sink(
            dsn=history_db_config.dsn,
            report=report,
            table_name=history_db_config.table_name,
        )
    except Exception as exc:
        message = _redact_db_dsn(str(exc), dsn=history_db_config.dsn)
        message = _redact_db_dsn(message, dsn=db_config.dsn)
        message = _redact_db_table_name(
            message,
            table_name=history_db_config.table_name,
        )
        message = _redact_db_table_name(message, table_name=db_config.table_name)
        if not message.strip():
            message = exc.__class__.__name__
        raise RuntimeError(message) from None
    return report, True


def _run_paper_probability_selection_summary_history(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: PaperProbabilitySelectionSummaryHistoryRunner | None,
) -> object:
    command_name = "paper-probability-selection-summary-history"
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError(f"{command_name} limit must be positive")
    generated_at = datetime.now(UTC)

    from polymarket_alpha_lab.paper_probability_selection_summary_history import (
        PaperProbabilitySelectionSummaryHistoryConfig,
        build_paper_probability_selection_summary_history_report,
    )

    config = PaperProbabilitySelectionSummaryHistoryConfig(
        config_version="paper-probability-selection-summary-history-v0",
    )
    if runner is not None:
        return runner(
            dsn=dsn,
            table_name=table_name,
            limit=limit,
            config=config,
            generated_at=generated_at,
        )

    from polymarket_alpha_lab.paper_probability_selection_summary_store import (
        load_paper_probability_selection_summary_reports,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper probability selection "
            "summary history read adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper probability selection summary database",
        ) from None
    try:
        newest_first_reports = load_paper_probability_selection_summary_reports(
            connection,
            limit=limit,
            table_name=table_name,
        )
        source_reports = tuple(reversed(newest_first_reports))
        return build_paper_probability_selection_summary_history_report(
            source_reports,
            config=config,
            generated_at=generated_at,
        )
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _run_paper_probability_selection_summary_history_trend(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: PaperProbabilitySelectionSummaryHistoryTrendRunner | None,
) -> object:
    command_name = "paper-probability-selection-summary-history-trend"
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError(f"{command_name} limit must be positive")
    generated_at = datetime.now(UTC)

    from polymarket_alpha_lab.paper_probability_selection_summary_history_trend import (
        PaperProbabilitySelectionSummaryHistoryTrendConfig,
        build_paper_probability_selection_summary_history_trend_report,
    )

    config = PaperProbabilitySelectionSummaryHistoryTrendConfig(
        config_version="paper-probability-selection-summary-history-trend-v0",
    )
    if runner is not None:
        return runner(
            dsn=dsn,
            table_name=table_name,
            limit=limit,
            config=config,
            generated_at=generated_at,
        )

    from polymarket_alpha_lab.paper_probability_selection_summary_history_store import (
        load_paper_probability_selection_summary_history_reports,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper probability selection "
            "summary history trend read adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper probability selection summary "
            "history database",
        ) from None
    try:
        newest_first_reports = load_paper_probability_selection_summary_history_reports(
            connection,
            limit=limit,
            table_name=table_name,
        )
        history_reports = tuple(reversed(newest_first_reports))
        return build_paper_probability_selection_summary_history_trend_report(
            history_reports,
            config=config,
            generated_at=generated_at,
        )
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _run_autonomous_market_scorer_history(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: AutonomousMarketScorerHistoryRunner | None,
) -> object:
    command_name = "autonomous-market-scorer-history"
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError(f"{command_name} limit must be positive")
    generated_at = datetime.now(UTC)

    from polymarket_alpha_lab.autonomous_market_scorer_history import (
        AutonomousMarketScorerHistoryConfig,
        build_autonomous_market_scorer_history_report,
    )

    config = AutonomousMarketScorerHistoryConfig(
        config_version="autonomous-market-scorer-history-v0",
    )
    if runner is not None:
        return runner(
            dsn=dsn,
            table_name=table_name,
            limit=limit,
            config=config,
            generated_at=generated_at,
        )

    from polymarket_alpha_lab.autonomous_market_scorer_store import (
        load_autonomous_market_scorer_reports,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the autonomous market scorer "
            "history read adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the autonomous market scorer database",
        ) from None
    try:
        newest_first_reports = load_autonomous_market_scorer_reports(
            connection,
            limit=limit,
            table_name=table_name,
        )
        scorer_reports = tuple(reversed(newest_first_reports))
        return build_autonomous_market_scorer_history_report(
            scorer_reports,
            config=config,
            generated_at=generated_at,
        )
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _run_probability_selection_scorer_agreement(
    *,
    selection_summary_dsn: str,
    selection_summary_table_name: str,
    scorer_dsn: str,
    scorer_table_name: str,
    limit: int,
    runner: ProbabilitySelectionScorerAgreementRunner | None,
) -> object:
    _require_probability_selection_scorer_agreement_limit(limit)
    generated_at = datetime.now(UTC)

    from polymarket_alpha_lab.probability_selection_scorer_agreement import (
        ProbabilitySelectionScorerAgreementConfig,
    )

    config = ProbabilitySelectionScorerAgreementConfig(
        config_version="probability-selection-scorer-agreement-v0",
    )
    if runner is not None:
        try:
            return runner(
                selection_summary_dsn=selection_summary_dsn,
                selection_summary_table_name=selection_summary_table_name,
                scorer_dsn=scorer_dsn,
                scorer_table_name=scorer_table_name,
                limit=limit,
                config=config,
                generated_at=generated_at,
            )
        except Exception as exc:
            raise _redacted_probability_selection_scorer_agreement_error(
                exc,
                selection_summary_dsn=selection_summary_dsn,
                selection_summary_table_name=selection_summary_table_name,
                scorer_dsn=scorer_dsn,
                scorer_table_name=scorer_table_name,
            ) from None

    from polymarket_alpha_lab.probability_selection_scorer_agreement_load import (
        load_probability_selection_scorer_agreement_report,
    )
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the probability selection scorer "
            "agreement read adapter; install the postgres extra.",
        ) from exc

    try:
        selection_connection = psycopg.connect(
            selection_summary_dsn,
            autocommit=True,
        )
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper probability selection summary database",
        ) from None
    try:
        try:
            scorer_connection = psycopg.connect(scorer_dsn, autocommit=True)
        except Exception:
            raise RuntimeError(
                "failed to connect to the autonomous market scorer database",
            ) from None
        try:
            return load_probability_selection_scorer_agreement_report(
                selection_connection,
                scorer_connection,
                selection_limit=limit,
                scorer_limit=limit,
                selection_table_name=selection_summary_table_name,
                scorer_table_name=scorer_table_name,
                config=config,
                generated_at=generated_at,
            )
        finally:
            try:
                scorer_connection.close()
            except Exception:
                pass
    except Exception as exc:
        raise _redacted_probability_selection_scorer_agreement_error(
            exc,
            selection_summary_dsn=selection_summary_dsn,
            selection_summary_table_name=selection_summary_table_name,
            scorer_dsn=scorer_dsn,
            scorer_table_name=scorer_table_name,
        ) from None
    finally:
        try:
            selection_connection.close()
        except Exception:
            pass


def _run_probability_selection_scorer_agreement_trend(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: ProbabilitySelectionScorerAgreementTrendRunner | None,
) -> object:
    command_name = "probability-selection-scorer-agreement-trend"
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError(f"{command_name} limit must be positive")
    generated_at = datetime.now(UTC)

    from polymarket_alpha_lab.probability_selection_scorer_agreement_trend import (
        ProbabilitySelectionScorerAgreementTrendConfig,
        ProbabilitySelectionScorerAgreementTrendReport,
        build_probability_selection_scorer_agreement_trend_report,
    )

    config = ProbabilitySelectionScorerAgreementTrendConfig(
        config_version="probability-selection-scorer-agreement-trend-v0",
    )
    if runner is not None:
        report = runner(
            dsn=dsn,
            table_name=table_name,
            limit=limit,
            config=config,
            generated_at=generated_at,
        )
        if type(report) is not ProbabilitySelectionScorerAgreementTrendReport:
            raise ValueError(
                "runner must return exactly "
                "ProbabilitySelectionScorerAgreementTrendReport",
            )
        return report

    from polymarket_alpha_lab.probability_selection_scorer_agreement_store import (
        load_probability_selection_scorer_agreement_reports,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the probability selection scorer "
            "agreement trend read adapter; install the postgres extra.",
        ) from exc

    try:
        connection = psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the probability selection scorer agreement "
            "database",
        ) from None
    try:
        newest_first_reports = load_probability_selection_scorer_agreement_reports(
            connection,
            limit=limit,
            table_name=table_name,
        )
        agreement_reports = tuple(reversed(newest_first_reports))
        return build_probability_selection_scorer_agreement_trend_report(
            agreement_reports,
            config=config,
            generated_at=generated_at,
        )
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _run_probability_selection_scorer_agreement_trend_gate(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: ProbabilitySelectionScorerAgreementTrendGateRunner | None,
) -> object:
    command_name = "probability-selection-scorer-agreement-trend-gate"
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError(f"{command_name} limit must be positive")
    generated_at = datetime.now(UTC)

    from polymarket_alpha_lab.probability_selection_scorer_agreement_trend import (
        ProbabilitySelectionScorerAgreementTrendConfig,
        build_probability_selection_scorer_agreement_trend_report,
    )
    from polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate import (
        ProbabilitySelectionScorerAgreementTrendGateConfig,
        ProbabilitySelectionScorerAgreementTrendGateReport,
        build_probability_selection_scorer_agreement_trend_gate_report,
    )

    trend_config = ProbabilitySelectionScorerAgreementTrendConfig(
        config_version="probability-selection-scorer-agreement-trend-v0",
    )
    gate_config = ProbabilitySelectionScorerAgreementTrendGateConfig(
        config_version="probability-selection-scorer-agreement-trend-gate-v0",
    )
    if runner is not None:
        report = runner(
            dsn=dsn,
            table_name=table_name,
            limit=limit,
            trend_config=trend_config,
            gate_config=gate_config,
            generated_at=generated_at,
        )
        if type(report) is not ProbabilitySelectionScorerAgreementTrendGateReport:
            raise ValueError(
                "runner must return exactly "
                "ProbabilitySelectionScorerAgreementTrendGateReport",
            )
        return report

    from polymarket_alpha_lab.probability_selection_scorer_agreement_store import (
        load_probability_selection_scorer_agreement_reports,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the probability selection scorer "
            "agreement trend gate read adapter; install the postgres extra.",
        ) from exc

    try:
        connection = psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the probability selection scorer agreement "
            "database",
        ) from None
    try:
        newest_first_reports = load_probability_selection_scorer_agreement_reports(
            connection,
            limit=limit,
            table_name=table_name,
        )
        agreement_reports = tuple(reversed(newest_first_reports))
        trend_report = build_probability_selection_scorer_agreement_trend_report(
            agreement_reports,
            config=trend_config,
            generated_at=generated_at,
        )
        return build_probability_selection_scorer_agreement_trend_gate_report(
            trend_report,
            config=gate_config,
            generated_at=generated_at,
        )
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _run_paper_autonomous_readiness_digest(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: PaperAutonomousReadinessDigestRunner | None,
    agreement_dsn: str | None = None,
    agreement_table_name: str | None = None,
) -> object:
    _require_paper_autonomous_readiness_digest_limit(limit)
    if agreement_dsn is not None:
        validate_local_postgres_dsn(
            agreement_dsn,
            env_var_name=PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN_ENV_VAR,
        )
    generated_at = datetime.now(UTC)

    from polymarket_alpha_lab.paper_autonomous_readiness_digest import (
        PaperAutonomousReadinessDigestConfig,
    )

    config = PaperAutonomousReadinessDigestConfig()
    if runner is not None:
        try:
            return runner(
                dsn=dsn,
                table_name=table_name,
                limit=limit,
                config=config,
                generated_at=generated_at,
            )
        except Exception as exc:
            raise _redacted_paper_readiness_digest_error(
                exc,
                readiness_dsn=dsn,
                readiness_table_name=table_name,
                agreement_dsn=agreement_dsn,
                agreement_table_name=agreement_table_name,
            ) from None

    from polymarket_alpha_lab.paper_autonomous_readiness_digest_load import (
        load_paper_autonomous_readiness_digest_report,
    )
    from polymarket_alpha_lab.paper_autonomous_readiness_gate_store import (
        load_paper_autonomous_readiness_gate_reports,
    )
    from polymarket_alpha_lab.probability_selection_scorer_agreement_store import (
        load_probability_selection_scorer_agreement_reports,
    )
    from polymarket_alpha_lab.probability_selection_scorer_agreement_trend import (
        ProbabilitySelectionScorerAgreementTrendConfig,
        build_probability_selection_scorer_agreement_trend_report,
    )
    from polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate import (
        ProbabilitySelectionScorerAgreementTrendGateConfig,
        build_probability_selection_scorer_agreement_trend_gate_report,
    )

    def readiness_loader(
        connection: object,
        *,
        table_name: str,
        limit: int | None,
        generated_at: datetime,
    ) -> object:
        del generated_at
        reports = load_paper_autonomous_readiness_gate_reports(
            connection,
            limit=limit,
            table_name=table_name,
        )
        if not reports:
            raise ValueError("paper autonomous readiness gate DB returned no reports")
        return reports[0]

    trend_config = ProbabilitySelectionScorerAgreementTrendConfig(
        config_version="probability-selection-scorer-agreement-trend-v0",
    )
    gate_config = ProbabilitySelectionScorerAgreementTrendGateConfig(
        config_version="probability-selection-scorer-agreement-trend-gate-v0",
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper autonomous readiness digest "
            "read adapter; install the postgres extra.",
        ) from exc
    agreement_connection = None
    try:
        connection = psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper autonomous readiness gate database",
        ) from None
    try:
        agreement_trend_gate_loader = None
        agreement_trend_gate_table_name = None
        if agreement_dsn is not None:
            if agreement_table_name is None:
                raise ValueError("agreement_trend_gate_table_name is required")
            try:
                agreement_connection = psycopg.connect(
                    agreement_dsn,
                    autocommit=True,
                )
            except Exception:
                raise RuntimeError(
                    "failed to connect to the probability selection scorer "
                    "agreement database",
                ) from None

            def agreement_trend_gate_loader(
                connection: object,
                *,
                table_name: str,
                limit: int | None,
                generated_at: datetime,
            ) -> object:
                del connection
                newest_first_reports = load_probability_selection_scorer_agreement_reports(
                    agreement_connection,
                    limit=limit,
                    table_name=table_name,
                )
                agreement_reports = tuple(reversed(newest_first_reports))
                trend_report = build_probability_selection_scorer_agreement_trend_report(
                    agreement_reports,
                    config=trend_config,
                    generated_at=generated_at,
                )
                return build_probability_selection_scorer_agreement_trend_gate_report(
                    trend_report,
                    config=gate_config,
                    generated_at=generated_at,
                )

            agreement_trend_gate_table_name = agreement_table_name
        return load_paper_autonomous_readiness_digest_report(
            connection,
            readiness_loader=readiness_loader,
            readiness_table_name=table_name,
            limit=limit,
            config=config,
            generated_at=generated_at,
            agreement_trend_gate_loader=agreement_trend_gate_loader,
            agreement_trend_gate_table_name=agreement_trend_gate_table_name,
        )
    except Exception as exc:
        raise _redacted_paper_readiness_digest_error(
            exc,
            readiness_dsn=dsn,
            readiness_table_name=table_name,
            agreement_dsn=agreement_dsn,
            agreement_table_name=agreement_table_name,
        ) from None
    finally:
        if agreement_connection is not None:
            try:
                agreement_connection.close()
            except Exception:
                pass
        try:
            connection.close()
        except Exception:
            pass


def _run_paper_research_packet(
    *,
    source_config_version: str | None,
    action_status: str | None,
    research_status: str | None,
    limit: int,
    packet_config_version: str,
    max_packet_rows: int,
    min_score: Decimal,
    persist: bool,
    loader: StrategyCandidateResearchQueueLoader | None,
    packet_builder: PaperResearchPacketBuilder | None,
    packet_db_sink: PaperResearchPacketDbSink | None,
) -> tuple[object, bool]:
    from polymarket_alpha_lab.strategy_candidate_research_packet_source import (
        build_paper_research_packet_report_from_strategy_candidate_research_queue_report,
    )
    from polymarket_alpha_lab.strategy_candidate_research_queue_psycopg_read import (
        PaperStrategyCandidateResearchQueueReadOptions,
        load_paper_strategy_candidate_research_queue_reports_with_psycopg,
    )

    db_config = from_strategy_candidate_research_queue_db_env()
    if not db_config.enabled:
        raise ValueError(
            "paper-research-packet requires strategy candidate research queue "
            "read-only DB config to be enabled",
        )
    if not db_config.dsn:
        raise ValueError("paper-research-packet requires a source DB DSN")
    packet_db_config = from_paper_research_packet_db_env() if persist else None
    if persist:
        if packet_db_config is None:
            raise ValueError(
                "paper-research-packet persistence requires packet DB config",
            )
        if not packet_db_config.enabled:
            raise ValueError(
                "paper-research-packet persistence requires packet DB to be enabled",
            )
        if not packet_db_config.dsn:
            raise ValueError(
                "paper-research-packet persistence requires a packet DB DSN",
            )

    read_options = PaperStrategyCandidateResearchQueueReadOptions(
        source_config_version=source_config_version,
        action_status=action_status,
        research_status=research_status,
        limit=limit,
        table_name=db_config.table_name,
    )
    packet_config = PaperResearchPacketConfig(
        config_version=packet_config_version,
        max_packet_rows=max_packet_rows,
        min_score=min_score,
    )
    resolved_loader = (
        loader
        if loader is not None
        else load_paper_strategy_candidate_research_queue_reports_with_psycopg
    )
    resolved_packet_builder = (
        packet_builder
        if packet_builder is not None
        else build_paper_research_packet_report_from_strategy_candidate_research_queue_report
    )

    try:
        queue_reports = resolved_loader(db_config.dsn, options=read_options)
    except Exception as exc:
        message = _redact_db_dsn(str(exc), dsn=db_config.dsn)
        message = _redact_db_table_name(message, table_name=db_config.table_name)
        if not message.strip():
            message = exc.__class__.__name__
        raise RuntimeError(message) from None
    if not queue_reports:
        raise ValueError("paper-research-packet requires at least one source report")
    latest_source_report = max(
        queue_reports,
        key=lambda source_report: source_report.generated_at,
    )

    generated_at = datetime.now(UTC)
    try:
        report = resolved_packet_builder(
            latest_source_report,
            config=packet_config,
            generated_at=generated_at,
        )
    except Exception as exc:
        message = _redact_db_dsn(str(exc), dsn=db_config.dsn)
        message = _redact_db_table_name(message, table_name=db_config.table_name)
        if packet_db_config is not None:
            message = _redact_db_dsn(message, dsn=packet_db_config.dsn)
            message = _redact_db_table_name(
                message,
                table_name=packet_db_config.table_name,
            )
        if not message.strip():
            message = exc.__class__.__name__
        raise RuntimeError(message) from None
    if not persist:
        return report, False
    if packet_db_sink is None:
        from polymarket_alpha_lab.paper_research_packet_psycopg import (
            insert_paper_research_packet_report_with_psycopg,
        )

        resolved_packet_db_sink = insert_paper_research_packet_report_with_psycopg
    else:
        resolved_packet_db_sink = packet_db_sink
    try:
        resolved_packet_db_sink(
            dsn=packet_db_config.dsn,
            report=report,
            table_name=packet_db_config.table_name,
        )
    except Exception as exc:
        message = _redact_db_dsn(str(exc), dsn=packet_db_config.dsn)
        message = _redact_db_dsn(message, dsn=db_config.dsn)
        message = _redact_db_table_name(message, table_name=packet_db_config.table_name)
        message = _redact_db_table_name(message, table_name=db_config.table_name)
        if not message.strip():
            message = exc.__class__.__name__
        raise RuntimeError(message) from None
    return report, True


def _run_paper_research_packet_db_history(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: PaperResearchPacketDbHistoryRunner | None,
) -> object:
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError("paper-research-packet-db-history limit must be positive")
    generated_at = datetime.now(UTC)
    config = PaperResearchPacketDbHistoryConfig(
        config_version=DEFAULT_PAPER_RESEARCH_PACKET_DB_HISTORY_CONFIG_VERSION,
    )
    if runner is not None:
        try:
            return runner(
                dsn=dsn,
                table_name=table_name,
                limit=limit,
                config=config,
                generated_at=generated_at,
            )
        except Exception as exc:
            raise _redacted_paper_research_packet_db_history_error(
                exc,
                dsn=dsn,
                table_name=table_name,
            ) from None

    from polymarket_alpha_lab.paper_research_packet_db_history_load import (
        load_paper_research_packet_db_history_report,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper research packet DB history "
            "read adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper research packet database",
        ) from None
    try:
        return load_paper_research_packet_db_history_report(
            connection,
            limit=limit,
            table_name=table_name,
            config=config,
            generated_at=generated_at,
        )
    except Exception as exc:
        raise _redacted_paper_research_packet_db_history_error(
            exc,
            dsn=dsn,
            table_name=table_name,
        ) from None
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _run_action_gated_queue_decision_support_trend(
    *,
    source_limit: int,
    source_risk_status: str | None,
    persist: bool,
    runner: ActionGatedQueueDecisionSupportTrendRunner | None,
) -> tuple[object, bool]:
    from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend_db_row import (
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SCHEMA_VERSION,
    )
    from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_psycopg import (
        load_paper_action_gated_strategy_recommendation_queue_decision_support_reports_with_psycopg,
    )
    from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend import (
        build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report,
    )
    from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend_psycopg import (
        insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg,
    )

    if (
        isinstance(source_limit, bool)
        or not isinstance(source_limit, int)
        or source_limit < 1
    ):
        raise ValueError("source_limit must be a positive integer")
    source_db_config = (
        from_action_gated_strategy_recommendation_queue_decision_support_db_env()
    )
    if not source_db_config.enabled:
        raise ValueError(
            "action-gated-queue-decision-support-trend requires action-gated "
            "queue decision-support DB to be enabled",
        )
    if source_db_config.dsn is None:
        raise ValueError(
            "action-gated-queue-decision-support-trend requires a source DB DSN",
        )
    trend_db_config = (
        from_action_gated_strategy_recommendation_queue_decision_support_trend_db_env()
        if persist
        else None
    )
    generated_at = datetime.now(UTC)
    config_version = ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SCHEMA_VERSION
    if persist:
        if trend_db_config is None:
            raise ValueError(
                "action-gated-queue-decision-support-trend persistence requires "
                "trend DB config",
            )
        if not trend_db_config.enabled:
            raise ValueError(
                "action-gated-queue-decision-support-trend persistence requires "
                "trend DB to be enabled",
            )
        if trend_db_config.dsn is None:
            raise ValueError(
                "action-gated-queue-decision-support-trend persistence requires "
                "a trend DB DSN",
            )
    if runner is not None:
        try:
            return runner(
                source_dsn=source_db_config.dsn,
                generated_at=generated_at,
                config_version=config_version,
                source_limit=source_limit,
                source_risk_status=source_risk_status,
                source_table_name=source_db_config.table_name,
                persist=persist,
                trend_dsn=None if trend_db_config is None else trend_db_config.dsn,
                trend_reports_table_name=(
                    None
                    if trend_db_config is None
                    else trend_db_config.reports_table_name
                ),
                trend_sources_table_name=(
                    None
                    if trend_db_config is None
                    else trend_db_config.sources_table_name
                ),
            )
        except Exception as exc:
            message = _redact_db_dsn(str(exc), dsn=source_db_config.dsn)
            if trend_db_config is not None and trend_db_config.dsn is not None:
                message = _redact_db_dsn(message, dsn=trend_db_config.dsn)
            if not message.strip():
                message = exc.__class__.__name__
            raise RuntimeError(message) from None

    try:
        newest_first_pairs = (
            load_paper_action_gated_strategy_recommendation_queue_decision_support_reports_with_psycopg(
                source_db_config.dsn,
                risk_status=source_risk_status,
                limit=source_limit,
                table_name=source_db_config.table_name,
            )
        )
    except Exception as exc:
        _raise_redacted_db_read_error(exc, dsn=source_db_config.dsn)
    if not newest_first_pairs:
        raise ValueError("no paper action-gated queue decision-support reports found")

    chronological_pairs = tuple(reversed(newest_first_pairs))
    trend_report = (
        build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
            chronological_pairs,
            generated_at=generated_at,
        )
    )
    if not persist:
        return trend_report, False

    try:
        insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg(
            trend_db_config.dsn,
            trend_report,
            chronological_pairs,
            reports_table_name=trend_db_config.reports_table_name,
            sources_table_name=trend_db_config.sources_table_name,
        )
    except Exception as exc:
        _raise_redacted_db_sink_error(exc, dsn=trend_db_config.dsn)
    return trend_report, True


def _run_action_gated_queue_decision_support_trend_db_history(
    *,
    dsn: str,
    reports_table_name: str,
    sources_table_name: str,
    latest_risk_status: str | None,
    limit: int,
    runner: ActionGatedQueueDecisionSupportTrendDbHistoryRunner | None,
) -> object:
    generated_at = datetime.now(UTC)
    config_version = "action-gated-queue-decision-support-trend-db-history-v0"
    if runner is not None:
        return runner(
            dsn=dsn,
            reports_table_name=reports_table_name,
            sources_table_name=sources_table_name,
            latest_risk_status=latest_risk_status,
            limit=limit,
            config_version=config_version,
            generated_at=generated_at,
        )

    from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend_db_history import (
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbHistoryConfig,
        build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_history_report,
    )
    from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend_psycopg import (
        load_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg,
    )

    trend_rows = (
        load_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg(
            dsn,
            latest_risk_status=latest_risk_status,
            limit=limit,
            reports_table_name=reports_table_name,
            sources_table_name=sources_table_name,
        )
    )
    return build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_history_report(
        trend_rows,
        config=(
            PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbHistoryConfig(
                config_version=config_version,
            )
        ),
        generated_at=generated_at,
    )


def _run_action_gated_queue_history_db_history(
    *,
    dsn: str,
    table_name: str,
    latest_action_status: str | None,
    limit: int,
    runner: ActionGatedQueueHistoryDbHistoryRunner | None,
) -> object:
    generated_at = datetime.now(UTC)
    config_version = "action-gated-queue-history-db-history-v0"
    if runner is not None:
        return runner(
            dsn=dsn,
            table_name=table_name,
            latest_action_status=latest_action_status,
            limit=limit,
            config_version=config_version,
            generated_at=generated_at,
        )

    from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_history_db_history import (
        PaperActionGatedStrategyRecommendationQueueHistoryDbHistoryConfig,
        build_paper_action_gated_strategy_recommendation_queue_history_db_history_report,
    )
    from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_history_psycopg import (
        load_paper_action_gated_strategy_recommendation_queue_history_reports_with_psycopg,
    )

    history_reports = (
        load_paper_action_gated_strategy_recommendation_queue_history_reports_with_psycopg(
            dsn,
            latest_action_status=latest_action_status,
            limit=limit,
            table_name=table_name,
        )
    )
    return build_paper_action_gated_strategy_recommendation_queue_history_db_history_report(
        history_reports,
        config=(
            PaperActionGatedStrategyRecommendationQueueHistoryDbHistoryConfig(
                config_version=config_version,
            )
        ),
        generated_at=generated_at,
    )


def _run_cost_audit(
    *,
    trade_log: Path,
    runner: CostAuditRunner | None,
) -> PaperTradeCostAuditReport:
    """Read typed paper trades and build the paper-only cost audit report."""

    trade_records = PaperTradeJournal.read(trade_log)
    config = PaperTradeCostAuditConfig(config_version="paper-trade-cost-audit-v0")
    generated_at = datetime.now(UTC)
    if runner is not None:
        return runner(
            trade_records=trade_records,
            config=config,
            generated_at=generated_at,
        )
    return build_paper_trade_cost_audit_report(
        trade_records,
        config=config,
        generated_at=generated_at,
    )


def _run_strategy_audit(
    *,
    cycle_log: Path,
    trade_log: Path,
    nav_log: Path,
    outcome_log: Path | None,
    runner: StrategyAuditRunner | None,
) -> PaperStrategyRiskAuditReport:
    """Read local paper logs and build a strategy risk audit report."""

    generated_at = datetime.now(UTC)
    config = PaperStrategyRiskAuditConfig(config_version="strategy-risk-audit-v0")
    trade_records = PaperTradeJournal.read(trade_log)
    cost_audit_report = build_paper_trade_cost_audit_report(
        trade_records,
        config=PaperTradeCostAuditConfig(config_version="paper-trade-cost-audit-v0"),
        generated_at=generated_at,
    )
    if runner is not None:
        return runner(
            cycle_log=cycle_log,
            trade_log=trade_log,
            nav_log=nav_log,
            outcome_log=outcome_log,
            cost_audit_report=cost_audit_report,
            config=config,
            generated_at=generated_at,
        )
    performance_summary = _run_history(
        cycle_log=cycle_log,
        trade_log=trade_log,
        nav_log=nav_log,
        runner=None,
    )
    nav_risk_report = _run_nav_risk(nav_log=nav_log, runner=None)
    return build_paper_strategy_risk_audit_report(
        performance_summary=performance_summary,
        nav_risk_report=nav_risk_report,
        outcome_report=_latest_outcome_report(outcome_log),
        cost_audit_report=cost_audit_report,
        config=config,
        generated_at=generated_at,
    )


def _latest_outcome_report(path: Path | None) -> OutcomeTrackingReport | None:
    if path is None:
        return None
    reports = OutcomeTrackingLog.read(path)
    if not reports:
        return None
    return reports[-1]


def _run_strategy_audit_history(
    *,
    strategy_audit_log: Path,
    runner: StrategyAuditHistoryRunner | None,
) -> PaperStrategyRiskAuditHistoryReport:
    reports = PaperStrategyRiskAuditLog.read(strategy_audit_log)
    config = PaperStrategyRiskAuditHistoryConfig(
        config_version="strategy-audit-history-v0",
    )
    generated_at = datetime.now(UTC)
    if runner is not None:
        return runner(
            reports=reports,
            config=config,
            generated_at=generated_at,
        )
    return build_paper_strategy_risk_audit_history_report(
        reports,
        config=config,
        generated_at=generated_at,
    )


def _run_strategy_recommendation_history(
    *,
    recommendation_log: Path,
    runner: StrategyRecommendationHistoryRunner | None,
) -> tuple[PaperStrategyRecommendationHistoryReport, int, Decimal, dict[str, object]]:
    bundles = read_paper_strategy_recommendation_bundle_log(recommendation_log)
    recommendation_reports = tuple(bundle.recommendation_report for bundle in bundles)
    config_version = "strategy-recommendation-history-v0"
    generated_at = datetime.now(UTC)
    if runner is not None:
        report = runner(
            recommendation_reports=recommendation_reports,
            config_version=config_version,
            generated_at=generated_at,
        )
    else:
        report = build_paper_strategy_recommendation_history_report(
            recommendation_reports,
            config_version=config_version,
            generated_at=generated_at,
        )
    latest_bundle = _latest_strategy_recommendation_bundle(bundles)
    latest_selected_count = 0 if latest_bundle is None else latest_bundle.selected_count
    latest_selected_notional = (
        Decimal("0")
        if latest_bundle is None
        else latest_bundle.total_selected_notional
    )
    selection_score_metrics = _strategy_recommendation_history_selection_score_metrics(
        report,
        bundles,
    )
    return (
        report,
        latest_selected_count,
        latest_selected_notional,
        selection_score_metrics,
    )


def _run_paper_recommendation_reason_trend(
    *,
    recommendation_log: Path,
) -> tuple[
    PaperRecommendationReasonTrendReport,
    Counter[str],
    Counter[tuple[str, str]],
]:
    bundles = read_paper_strategy_recommendation_bundle_log(recommendation_log)
    source_reports = tuple(
        _paper_recommendation_reason_trend_source_report(bundle)
        for bundle in bundles
    )
    config = PaperRecommendationReasonTrendConfig(
        config_version="paper-recommendation-reason-trend-v0",
        window_size=max(1, len(source_reports)),
    )
    report = build_paper_recommendation_reason_trend_report(
        source_reports,
        config=config,
        generated_at=datetime.now(UTC),
    )
    windowed_source_reports = source_reports[-config.window_size :]
    action_counts: Counter[str] = Counter()
    for source_report in windowed_source_reports:
        action_counts.update(row.action for row in source_report.rows)
    reason_code_counts: Counter[tuple[str, str]] = Counter()
    for row in report.reason_trend_rows:
        reason_code_counts[(row.reason_code, row.source_status)] += row.count
    return report, action_counts, reason_code_counts


def _run_paper_probability_side_edge_report(
    *,
    input_path: Path,
) -> tuple["PaperProbabilitySideEdgeReport", Counter[str]]:
    from polymarket_alpha_lab.json_recovery import from_jsonable
    from polymarket_alpha_lab.paper_side_edge_adapter import (
        PaperSideEdgeAdapterConfig,
        PaperSideEdgeAdapterInput,
        build_paper_side_edge_report_from_strategy_rows,
    )

    raw_rows = _read_paper_probability_side_edge_row_payloads(input_path)
    rows = tuple(
        _paper_probability_side_edge_input_from_payload(
            row,
            row_number=row_number,
            input_type=PaperSideEdgeAdapterInput,
            recover=from_jsonable,
        )
        for row_number, row in enumerate(raw_rows, start=1)
    )
    report = build_paper_side_edge_report_from_strategy_rows(
        rows,
        config=PaperSideEdgeAdapterConfig(
            config_version="paper-probability-side-edge-report-v0",
            min_net_probability_edge=Decimal("0.010000"),
        ),
        generated_at=datetime.now(UTC),
    )
    reason_code_counts: Counter[str] = Counter(
        reason_code
        for row in report.rows
        for reason_code in row.reason_codes
    )
    return report, reason_code_counts


def _run_paper_recommendation_queue_report(
    *,
    input_path: Path,
) -> tuple[object, Counter[str]]:
    from polymarket_alpha_lab.paper_probability_recommendation_queue import (
        PaperProbabilityRecommendationQueueConfig,
        build_paper_probability_recommendation_queue_report,
    )
    from polymarket_alpha_lab.paper_probability_recommendation_queue_local_input import (
        read_paper_probability_recommendation_queue_side_edge_rows,
    )

    rows = read_paper_probability_recommendation_queue_side_edge_rows(input_path)
    report = build_paper_probability_recommendation_queue_report(
        rows,
        config=PaperProbabilityRecommendationQueueConfig(
            config_version="paper-recommendation-queue-cli-v0",
            max_queue_rows=25,
            min_recommendation_score=Decimal("0.000001"),
            include_watch=True,
        ),
        generated_at=datetime.now(UTC),
    )
    reason_code_counts: Counter[str] = Counter(
        reason_code
        for row in report.queue_rows
        for reason_code in row.reason_codes
    )
    return report, reason_code_counts


def _run_paper_recommendation_risk_budget_report(
    *,
    input_path: Path,
    nav_notional: Decimal | None,
) -> tuple[object, int]:
    from polymarket_alpha_lab.paper_recommendation_risk_budget import (
        PaperRecommendationRiskBudgetConfig,
        build_paper_recommendation_risk_budget_report,
    )
    from polymarket_alpha_lab.paper_recommendation_risk_budget_local_input import (
        paper_recommendation_risk_budget_nav_report_from_notional,
        read_paper_recommendation_risk_budget_selection_report,
    )

    selection_report = read_paper_recommendation_risk_budget_selection_report(
        input_path,
    )
    nav_report = paper_recommendation_risk_budget_nav_report_from_notional(
        nav_notional,
    )
    report = build_paper_recommendation_risk_budget_report(
        selection_report,
        config=PaperRecommendationRiskBudgetConfig(
            config_version="paper-recommendation-risk-budget-cli-v0",
            max_total_utilization=Decimal("0.250000"),
            max_single_recommendation_share=Decimal("0.100000"),
            min_remaining_notional=Decimal("10.000000"),
            max_selected_count=25,
        ),
        generated_at=datetime.now(UTC),
        nav_risk_metrics_report=nav_report,
    )
    zero_allocation_count = sum(
        1
        for row in selection_report.selection_rows
        if row.selected_position_notional == Decimal("0.000000")
    )
    return report, zero_allocation_count


def _read_paper_probability_side_edge_row_payloads(
    path: Path,
) -> tuple[object, ...]:
    import json

    text = path.read_text(encoding="utf-8")
    stripped = text.strip()
    if not stripped:
        return ()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        rows: list[object] = []
        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{path} line {line_number} is not valid JSON: {exc}",
                ) from exc
        if not rows:
            return ()
        return tuple(rows)
    if isinstance(parsed, list):
        return tuple(parsed)
    if isinstance(parsed, dict):
        for field_name in ("rows", "inputs", "input_rows"):
            if field_name not in parsed:
                continue
            value = parsed[field_name]
            if not isinstance(value, list):
                raise ValueError(f"{path} {field_name} must be a JSON array")
            return tuple(value)
        return (parsed,)
    raise ValueError(
        f"{path} input must be a JSON object, JSON array, or JSONL file",
    )


def _paper_probability_side_edge_input_from_payload(
    row: object,
    *,
    row_number: int,
    input_type: type[object],
    recover: Callable[[type[object], dict[str, object]], object],
) -> object:
    if not isinstance(row, dict):
        raise ValueError(f"input row {row_number} must be a JSON object")
    try:
        return recover(input_type, row)
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "input row "
            f"{row_number} is not a valid PaperSideEdgeAdapterInput: {exc}",
        ) from exc


def _paper_recommendation_reason_trend_source_report(
    bundle: PaperStrategyRecommendationBundleReport,
) -> _PaperRecommendationReasonTrendAdapterReport:
    recommendation_report = bundle.recommendation_report
    return _PaperRecommendationReasonTrendAdapterReport(
        generated_at=bundle.generated_at,
        rows=tuple(
            _paper_recommendation_reason_trend_adapter_row(row)
            for row in recommendation_report.recommendation_rows
        ),
    )


def _paper_recommendation_reason_trend_adapter_row(
    row: object,
) -> _PaperRecommendationReasonTrendAdapterRow:
    side = getattr(row, "scoring_side", None)
    if side not in ("yes", "no", "none"):
        raise ValueError("recommendation rows must have a yes/no/none scoring_side")
    action = getattr(row, "action", None)
    if action not in ("recommend", "watch", "reject"):
        raise ValueError("recommendation rows must have an action")
    market_slug = getattr(row, "market_slug", None)
    if not isinstance(market_slug, str):
        raise ValueError("recommendation rows must have a market_slug")
    reason_codes = getattr(row, "reason_codes", None)
    if isinstance(reason_codes, (str, bytes)) or reason_codes is None:
        raise ValueError("recommendation rows must have reason_codes")
    return _PaperRecommendationReasonTrendAdapterRow(
        market_slug=market_slug,
        side=side,
        action=action,
        reason_codes=tuple(reason_codes),
    )


def _latest_strategy_recommendation_bundle(bundles):
    ordered = _ordered_strategy_recommendation_bundles(bundles)
    if not ordered:
        return None
    return ordered[-1]


def _ordered_strategy_recommendation_bundles(bundles) -> tuple[object, ...]:
    return tuple(
        sorted(
            bundles,
            key=_strategy_recommendation_bundle_order_key,
        ),
    )


def _strategy_recommendation_bundle_order_key(bundle: object) -> tuple[datetime, str]:
    recommendation_report = getattr(bundle, "recommendation_report", None)
    generated_at = getattr(recommendation_report, "generated_at", None)
    if not isinstance(generated_at, datetime):
        generated_at = getattr(bundle, "generated_at", None)
    if not isinstance(generated_at, datetime):
        generated_at = datetime.min.replace(tzinfo=UTC)
    elif generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=UTC)
    else:
        generated_at = generated_at.astimezone(UTC)

    config_version = getattr(recommendation_report, "config_version", None)
    if not isinstance(config_version, str):
        config_version = getattr(bundle, "config_version", "")
    if not isinstance(config_version, str):
        config_version = ""
    return generated_at, config_version


def _strategy_recommendation_history_selection_score_metrics(
    report: PaperStrategyRecommendationHistoryReport,
    bundles: tuple[object, ...],
) -> dict[str, object]:
    metrics: dict[str, object] = {}
    _copy_existing_metrics(
        metrics,
        report,
        (
            "total_selected_count",
            "total_selected",
            "total_selected_notional",
            "latest_selected_count",
            "latest_selected",
            "latest_selected_notional",
            "first_recommendation_score",
            "latest_recommendation_score",
            "latest_selected_score",
        ),
    )
    _copy_matching_selection_score_metrics(metrics, report)

    ordered_bundles = _ordered_strategy_recommendation_bundles(bundles)
    if not ordered_bundles:
        return metrics

    first_bundle = ordered_bundles[0]
    latest_bundle = ordered_bundles[-1]
    _copy_existing_metrics(
        metrics,
        latest_bundle,
        (
            "latest_selected_count",
            "latest_selected",
            "latest_selected_notional",
            "latest_recommendation_score",
            "latest_selected_score",
        ),
    )

    if not _has_any_metric(metrics, ("total_selected", "total_selected_count")):
        total_selected = _sum_bundle_int_metric(ordered_bundles, "selected_count")
        if total_selected is not None:
            metrics["total_selected"] = total_selected
    if "total_selected_notional" not in metrics:
        total_selected_notional = _sum_bundle_decimal_metric(
            ordered_bundles,
            "total_selected_notional",
        )
        if total_selected_notional is not None:
            metrics["total_selected_notional"] = total_selected_notional
    if "first_recommendation_score" not in metrics:
        first_score = _max_recommendation_score(
            getattr(first_bundle, "recommendation_report", None),
        )
        if first_score is not None:
            metrics["first_recommendation_score"] = first_score
    if "latest_recommendation_score" not in metrics:
        latest_score = _max_recommendation_score(
            getattr(latest_bundle, "recommendation_report", None),
        )
        if latest_score is not None:
            metrics["latest_recommendation_score"] = latest_score
    if "latest_selected_score" not in metrics:
        latest_selected_score = _max_selected_score(latest_bundle)
        if latest_selected_score is not None:
            metrics["latest_selected_score"] = latest_selected_score
    _copy_matching_selection_score_metrics(metrics, latest_bundle)
    return metrics


def _copy_existing_metrics(
    metrics: dict[str, object],
    source: object,
    field_names: tuple[str, ...],
) -> None:
    for field_name in field_names:
        value = getattr(source, field_name, _MISSING)
        if value is not _MISSING and field_name not in metrics:
            metrics[field_name] = value


def _copy_matching_selection_score_metrics(
    metrics: dict[str, object],
    source: object,
) -> None:
    for field_name in dir(source):
        if field_name.startswith("_") or field_name in metrics:
            continue
        if not _is_selection_score_metric_name(field_name):
            continue
        try:
            value = getattr(source, field_name)
        except Exception:
            continue
        if _is_printable_metric_value(value):
            metrics[field_name] = value


def _is_selection_score_metric_name(field_name: str) -> bool:
    return (
        "selected" in field_name
        or "selection" in field_name
        or "score" in field_name
    )


def _is_printable_metric_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return False
    return isinstance(value, (int, Decimal, str))


def _has_any_metric(metrics: dict[str, object], field_names: tuple[str, ...]) -> bool:
    return any(field_name in metrics for field_name in field_names)


def _sum_bundle_int_metric(bundles: tuple[object, ...], field_name: str) -> int | None:
    total = 0
    observed = False
    for bundle in bundles:
        value = getattr(bundle, field_name, None)
        if isinstance(value, bool) or not isinstance(value, int):
            continue
        total += value
        observed = True
    return total if observed else None


def _sum_bundle_decimal_metric(
    bundles: tuple[object, ...],
    field_name: str,
) -> Decimal | None:
    total = Decimal("0")
    observed = False
    for bundle in bundles:
        value = getattr(bundle, field_name, None)
        if not isinstance(value, Decimal):
            continue
        total += value
        observed = True
    return total if observed else None


def _max_recommendation_score(report: object) -> Decimal | None:
    rows = _tuple_or_empty(getattr(report, "recommendation_rows", ()))
    scores = tuple(
        score
        for row in rows
        if isinstance((score := getattr(row, "recommendation_score", None)), Decimal)
    )
    return max(scores) if scores else None


def _max_selected_score(bundle: object) -> Decimal | None:
    selection_report = getattr(bundle, "selection_policy_report", None)
    rows = _tuple_or_empty(getattr(selection_report, "selection_rows", ()))
    scores = tuple(
        score
        for row in rows
        if getattr(row, "decision", None) == "selected"
        and isinstance((score := getattr(row, "recommendation_score", None)), Decimal)
    )
    return max(scores) if scores else None


def _tuple_or_empty(value: object) -> tuple[object, ...]:
    if value is None or isinstance(value, (str, bytes)):
        return ()
    try:
        return tuple(value)
    except TypeError:
        return ()


def _run_strategy_evidence(
    *,
    cycle_log: Path,
    trade_log: Path,
    nav_log: Path,
    outcome_log: Path | None,
    strategy_audit_log: Path | None,
    runner: StrategyEvidenceRunner | None,
) -> "PaperStrategyEvidenceSnapshotReport":
    from polymarket_alpha_lab.strategy_evidence import (
        PaperStrategyEvidenceSnapshotConfig,
        build_paper_strategy_evidence_snapshot_report,
    )

    generated_at = datetime.now(UTC)
    performance_summary = _run_history(
        cycle_log=cycle_log,
        trade_log=trade_log,
        nav_log=nav_log,
        runner=None,
    )
    nav_risk_report = _run_nav_risk(nav_log=nav_log, runner=None)
    cost_audit_report = _run_cost_audit(trade_log=trade_log, runner=None)
    strategy_audit_history_report = (
        None
        if strategy_audit_log is None
        else _run_strategy_audit_history(
            strategy_audit_log=strategy_audit_log,
            runner=None,
        )
    )
    outcome_report = _latest_outcome_report(outcome_log)
    config = PaperStrategyEvidenceSnapshotConfig(
        config_version="strategy-evidence-snapshot-v0",
    )
    if runner is not None:
        return runner(
            performance_summary=performance_summary,
            nav_risk_report=nav_risk_report,
            cost_audit_report=cost_audit_report,
            outcome_report=outcome_report,
            audit_history_report=strategy_audit_history_report,
            config=config,
            generated_at=generated_at,
        )
    return build_paper_strategy_evidence_snapshot_report(
        performance_summary=performance_summary,
        nav_risk_report=nav_risk_report,
        cost_audit_report=cost_audit_report,
        outcome_report=outcome_report,
        audit_history_report=strategy_audit_history_report,
        config=config,
        generated_at=generated_at,
    )


def _run_strategy_audit_db_history(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: StrategyAuditDbHistoryRunner | None,
) -> PaperStrategyRiskAuditHistoryReport:
    generated_at = datetime.now(UTC)
    config = PaperStrategyRiskAuditHistoryConfig(
        config_version="strategy-audit-db-history-v0",
    )
    if runner is not None:
        return runner(
            dsn=dsn,
            table_name=table_name,
            limit=limit,
            config=config,
            generated_at=generated_at,
        )

    from polymarket_alpha_lab.strategy_audit_db_history_load import (
        load_strategy_audit_db_history_report,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the strategy audit DB history "
            "psycopg adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(dsn)
    except Exception:
        raise RuntimeError(
            "failed to connect to the strategy risk audit database",
        ) from None
    try:
        report = load_strategy_audit_db_history_report(
            generated_at=generated_at,
            config_version=config.config_version,
            connection=connection,
            limit=limit,
            table_name=table_name,
        )
        connection.commit()
        return report
    except BaseException:
        try:
            connection.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _run_strategy_cycle_report_db_history(
    *,
    dsn: str,
    table_name: str,
    source_config_version: str | None,
    limit: int,
    runner: StrategyCycleReportDbHistoryRunner | None,
) -> PaperStrategyCycleReportHistoryReport:
    if isinstance(limit, bool) or type(limit) is not int or limit <= 0:
        raise ValueError("strategy-cycle-db-history limit must be positive")
    generated_at = datetime.now(UTC)
    config = PaperStrategyCycleReportHistoryConfig()
    if runner is not None:
        try:
            return runner(
                dsn=dsn,
                table_name=table_name,
                source_config_version=source_config_version,
                limit=limit,
                config=config,
                generated_at=generated_at,
            )
        except Exception as exc:
            _raise_redacted_strategy_cycle_report_db_history_error(
                exc,
                dsn=dsn,
                table_name=table_name,
            )
    try:
        reports = load_paper_strategy_cycle_reports_with_psycopg(
            dsn,
            config_version=source_config_version,
            limit=limit,
            table_name=table_name,
        )
        if not reports:
            raise ValueError("no paper strategy cycle reports found")
        return build_paper_strategy_cycle_report_history_report(
            tuple(reversed(reports)),
            config=config,
            generated_at=generated_at,
        )
    except Exception as exc:
        _raise_redacted_strategy_cycle_report_db_history_error(
            exc,
            dsn=dsn,
            table_name=table_name,
        )


def _run_strategy_cycle_history_gate(
    *,
    dsn: str,
    table_name: str,
    source_config_version: str | None,
    limit: int,
    gate_runner: StrategyCycleHistoryGateRunner | None,
) -> object:
    if isinstance(limit, bool) or type(limit) is not int or limit <= 0:
        raise ValueError("strategy-cycle-history-gate limit must be positive")
    generated_at = datetime.now(UTC)
    history_config = PaperStrategyCycleReportHistoryConfig()
    try:
        reports = load_paper_strategy_cycle_reports_with_psycopg(
            dsn,
            config_version=source_config_version,
            limit=limit,
            table_name=table_name,
        )
        if not reports:
            raise ValueError("no paper strategy cycle reports found")
        history_report = build_paper_strategy_cycle_report_history_report(
            tuple(reversed(reports)),
            config=history_config,
            generated_at=generated_at,
        )
    except Exception as exc:
        _raise_redacted_strategy_cycle_history_gate_error(
            exc,
            source_dsn=dsn,
            source_table_name=table_name,
        )
    gate_config = _paper_strategy_cycle_report_history_gate_config()
    gate_builder = gate_runner or _build_paper_strategy_cycle_report_history_gate_report
    return gate_builder(
        history_report,
        config=gate_config,
        generated_at=generated_at,
    )


def _paper_strategy_cycle_report_history_gate_config() -> object:
    from polymarket_alpha_lab.paper_strategy_cycle_report_history_gate import (
        PaperStrategyCycleReportHistoryGateConfig,
    )

    return PaperStrategyCycleReportHistoryGateConfig()


def _build_paper_strategy_cycle_report_history_gate_report(
    source_history_report: object,
    *,
    config: object,
    generated_at: datetime,
) -> object:
    from polymarket_alpha_lab.paper_strategy_cycle_report_history_gate import (
        build_paper_strategy_cycle_report_history_gate_report,
    )

    return build_paper_strategy_cycle_report_history_gate_report(
        source_history_report,
        config=config,
        generated_at=generated_at,
    )


def _from_paper_strategy_cycle_report_history_gate_db_env() -> object:
    from polymarket_alpha_lab.supabase_paper_strategy_cycle_report_history_gate_config import (
        from_paper_strategy_cycle_report_history_gate_db_env,
    )

    return from_paper_strategy_cycle_report_history_gate_db_env()


def _insert_paper_strategy_cycle_report_history_gate_report_with_psycopg(
    *,
    dsn: str,
    report: object,
    table_name: str,
) -> object:
    from polymarket_alpha_lab.paper_strategy_cycle_report_history_gate_psycopg import (
        insert_paper_strategy_cycle_report_history_gate_report_with_psycopg,
    )

    return insert_paper_strategy_cycle_report_history_gate_report_with_psycopg(
        dsn=dsn,
        report=report,
        table_name=table_name,
    )


def _run_cost_audit_db_trend(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: CostAuditDbTrendRunner | None,
) -> PaperTradeCostTrendReport:
    generated_at = datetime.now(UTC)
    config_version = "cost-audit-db-trend-v0"
    if runner is not None:
        return runner(
            dsn=dsn,
            table_name=table_name,
            limit=limit,
            config_version=config_version,
            generated_at=generated_at,
        )

    from polymarket_alpha_lab.paper_trade_cost_audit_db_history_load import (
        load_paper_trade_cost_audit_db_history_report,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the cost audit DB trend psycopg "
            "adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(dsn)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper trade cost audit database",
        ) from None
    try:
        report = load_paper_trade_cost_audit_db_history_report(
            generated_at=generated_at,
            config_version=config_version,
            connection=connection,
            limit=limit,
            table_name=table_name,
        )
        connection.commit()
        return report
    except BaseException:
        try:
            connection.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _run_paper_research_packet_quality(
    *,
    dsn: str,
    table_name: str,
    persist: bool = False,
    quality_db_config: Any | None = None,
    runner: PaperResearchPacketQualityRunner | None,
) -> object:
    from polymarket_alpha_lab.paper_research_packet_quality import (
        PaperResearchPacketQualityConfig,
    )

    if persist and quality_db_config is None:
        quality_db_config = from_paper_research_packet_quality_db_env()
    quality_dsn: str | None = None
    quality_table_name: str | None = None
    if persist:
        if quality_db_config is None:
            raise ValueError(
                "paper-research-packet-quality --persist requires "
                "paper research packet quality DB config",
            )
        if not quality_db_config.enabled:
            raise ValueError(
                "paper-research-packet-quality --persist requires "
                "paper research packet quality DB to be enabled",
            )
        quality_dsn = quality_db_config.dsn
        if quality_dsn is None:
            raise ValueError(
                "paper-research-packet-quality --persist requires "
                "a paper research packet quality DB DSN",
            )
        quality_table_name = quality_db_config.table_name

    def redacted_error(exc: Exception) -> RuntimeError:
        return _redacted_paper_research_packet_quality_error(
            exc,
            source_dsn=dsn,
            source_table_name=table_name,
            quality_dsn=quality_dsn,
            quality_table_name=quality_table_name,
        )

    generated_at = datetime.now(UTC)
    config = PaperResearchPacketQualityConfig()
    if runner is not None:
        try:
            report = runner(
                dsn=dsn,
                table_name=table_name,
                config=config,
                generated_at=generated_at,
            )
        except Exception as exc:
            raise redacted_error(exc) from None
    else:
        from polymarket_alpha_lab.paper_research_packet_quality import (
            build_paper_research_packet_quality_report,
        )
        from polymarket_alpha_lab.paper_research_packet_store import (
            load_paper_research_packet_reports,
        )

        try:
            import psycopg
        except ModuleNotFoundError as exc:
            if exc.name != "psycopg":
                raise
            raise RuntimeError(
                "psycopg is required to use the paper research packet quality "
                "read adapter; install the postgres extra.",
            ) from exc
        try:
            connection = psycopg.connect(dsn, autocommit=True)
        except Exception:
            raise RuntimeError(
                "failed to connect to the paper research packet database",
            ) from None
        try:
            packet_reports = load_paper_research_packet_reports(
                connection,
                limit=1,
                table_name=table_name,
            )
            if not packet_reports:
                raise ValueError("no persisted paper research packet reports found")
            report = build_paper_research_packet_quality_report(
                packet_reports[0],
                config=config,
                generated_at=generated_at,
            )
        except Exception as exc:
            raise redacted_error(exc) from None
        finally:
            try:
                connection.close()
            except Exception:
                pass

    if not persist:
        return report

    from polymarket_alpha_lab.paper_research_packet_quality_store import (
        insert_paper_research_packet_quality_report,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper research packet quality "
            "write adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(quality_dsn)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper research packet quality database",
        ) from None
    try:
        insert_paper_research_packet_quality_report(
            connection,
            report,
            table_name=quality_table_name,
        )
        connection.commit()
        return report
    except BaseException as exc:
        try:
            connection.rollback()
        except Exception:
            pass
        raise redacted_error(exc) from None
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _run_paper_research_packet_quality_db_history(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: PaperResearchPacketQualityDbHistoryRunner | None,
) -> object:
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError("paper-research-packet-quality-db-history limit must be positive")
    generated_at = datetime.now(UTC)
    config = PaperResearchPacketQualityHistoryConfig(
        config_version=DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_HISTORY_CONFIG_VERSION,
    )
    if runner is not None:
        try:
            return runner(
                dsn=dsn,
                table_name=table_name,
                limit=limit,
                config=config,
                generated_at=generated_at,
            )
        except Exception as exc:
            raise _redacted_paper_research_packet_db_history_error(
                exc,
                dsn=dsn,
                table_name=table_name,
            ) from None

    from polymarket_alpha_lab.paper_research_packet_quality_history_load import (
        load_paper_research_packet_quality_history_report,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper research packet quality "
            "DB history read adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper research packet quality database",
        ) from None
    try:
        return load_paper_research_packet_quality_history_report(
            connection,
            limit=limit,
            table_name=table_name,
            config=config,
            generated_at=generated_at,
        )
    except Exception as exc:
        raise _redacted_paper_research_packet_db_history_error(
            exc,
            dsn=dsn,
            table_name=table_name,
        ) from None
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _run_paper_research_packet_operator_flow_db_history(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: PaperResearchPacketOperatorFlowDbHistoryRunner | None,
) -> object:
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError(
            "paper-research-packet-operator-flow-db-history limit must be positive",
        )
    generated_at = datetime.now(UTC)

    from polymarket_alpha_lab.paper_research_packet_operator_flow_db_history import (
        PaperResearchPacketOperatorFlowDbHistoryConfig,
    )

    config = PaperResearchPacketOperatorFlowDbHistoryConfig()
    if runner is not None:
        try:
            return runner(
                dsn=dsn,
                table_name=table_name,
                limit=limit,
                config=config,
                generated_at=generated_at,
            )
        except Exception as exc:
            raise _redacted_paper_research_packet_db_history_error(
                exc,
                dsn=dsn,
                table_name=table_name,
            ) from None

    from polymarket_alpha_lab.paper_research_packet_operator_flow_db_history_load import (
        load_paper_research_packet_operator_flow_db_history_report,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper research packet operator-flow "
            "DB history read adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper research packet operator-flow database",
        ) from None
    try:
        return load_paper_research_packet_operator_flow_db_history_report(
            connection,
            limit=limit,
            table_name=table_name,
            config=config,
            generated_at=generated_at,
        )
    except Exception as exc:
        raise _redacted_paper_research_packet_db_history_error(
            exc,
            dsn=dsn,
            table_name=table_name,
        ) from None
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _run_paper_autonomous_allocation_proposal_db_history(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: PaperAutonomousAllocationProposalDbHistoryRunner | None,
) -> object:
    command_name = "paper-autonomous-allocation-proposal-db-history"
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError(f"{command_name} limit must be positive")
    generated_at = datetime.now(UTC)

    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history import (
        PaperAutonomousAllocationProposalDbHistoryConfig,
    )

    config = PaperAutonomousAllocationProposalDbHistoryConfig()
    if runner is not None:
        try:
            return runner(
                dsn=dsn,
                table_name=table_name,
                limit=limit,
                config=config,
                generated_at=generated_at,
            )
        except Exception as exc:
            raise _redacted_paper_research_packet_db_history_error(
                exc,
                dsn=dsn,
                table_name=table_name,
            ) from None

    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_load import (
        load_paper_autonomous_allocation_proposal_db_history_report,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper autonomous allocation proposal "
            "DB history read adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper autonomous allocation proposal database",
        ) from None
    try:
        return load_paper_autonomous_allocation_proposal_db_history_report(
            connection,
            limit=limit,
            table_name=table_name,
            config=config,
            generated_at=generated_at,
        )
    except Exception as exc:
        raise _redacted_paper_research_packet_db_history_error(
            exc,
            dsn=dsn,
            table_name=table_name,
        ) from None
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _run_paper_autonomous_allocation_proposal_db_history_gate(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: PaperAutonomousAllocationProposalDbHistoryGateRunner | None,
) -> object:
    command_name = "paper-autonomous-allocation-proposal-db-history-gate"
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError(f"{command_name} limit must be positive")
    generated_at = datetime.now(UTC)

    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history import (
        PaperAutonomousAllocationProposalDbHistoryConfig,
    )
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_gate import (
        PaperAutonomousAllocationProposalDbHistoryGateConfig,
    )

    history_config = PaperAutonomousAllocationProposalDbHistoryConfig()
    gate_config = PaperAutonomousAllocationProposalDbHistoryGateConfig()
    if runner is not None:
        try:
            return runner(
                dsn=dsn,
                table_name=table_name,
                limit=limit,
                history_config=history_config,
                gate_config=gate_config,
                generated_at=generated_at,
            )
        except Exception as exc:
            raise _redacted_paper_research_packet_db_history_error(
                exc,
                dsn=dsn,
                table_name=table_name,
            ) from None

    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_gate_load import (
        load_paper_autonomous_allocation_proposal_db_history_gate_report,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper autonomous allocation proposal "
            "DB history gate read adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper autonomous allocation proposal database",
        ) from None
    try:
        return load_paper_autonomous_allocation_proposal_db_history_gate_report(
            connection,
            limit=limit,
            table_name=table_name,
            history_config=history_config,
            gate_config=gate_config,
            generated_at=generated_at,
        )
    except Exception as exc:
        raise _redacted_paper_research_packet_db_history_error(
            exc,
            dsn=dsn,
            table_name=table_name,
        ) from None
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _run_paper_autonomous_allocation_proposal_db_history_metrics_evaluation(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationRunner | None,
) -> object:
    command_name = "paper-autonomous-allocation-proposal-db-history-metrics-evaluation"
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError(f"{command_name} limit must be positive")
    generated_at = datetime.now(UTC)

    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics_evaluation import (
        PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig,
    )

    config = PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig()
    if runner is not None:
        try:
            return runner(
                dsn=dsn,
                table_name=table_name,
                limit=limit,
                config=config,
                generated_at=generated_at,
            )
        except Exception as exc:
            raise _redacted_paper_research_packet_db_history_error(
                exc,
                dsn=dsn,
                table_name=table_name,
            ) from None

    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics_evaluation_load import (
        load_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper autonomous allocation proposal "
            "DB history metrics evaluation read adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(dsn, autocommit=True)
    except Exception as exc:
        raise _redacted_paper_research_packet_db_history_error(
            exc,
            dsn=dsn,
            table_name=table_name,
        ) from None
    try:
        return load_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
            connection,
            limit=limit,
            table_name=table_name,
            config=config,
            generated_at=generated_at,
        )
    except Exception as exc:
        raise _redacted_paper_research_packet_db_history_error(
            exc,
            dsn=dsn,
            table_name=table_name,
        ) from None
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _run_paper_autonomous_allocation_proposal_db_history_metrics(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: PaperAutonomousAllocationProposalDbHistoryMetricsRunner | None,
) -> object:
    command_name = "paper-autonomous-allocation-proposal-db-history-metrics"
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError(f"{command_name} limit must be positive")
    generated_at = datetime.now(UTC)

    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics import (
        PaperAutonomousAllocationProposalDbHistoryMetricsConfig,
    )

    config = PaperAutonomousAllocationProposalDbHistoryMetricsConfig()
    if runner is not None:
        try:
            return runner(
                dsn=dsn,
                table_name=table_name,
                limit=limit,
                config=config,
                generated_at=generated_at,
            )
        except Exception as exc:
            raise _redacted_paper_research_packet_db_history_error(
                exc,
                dsn=dsn,
                table_name=table_name,
            ) from None

    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics_load import (
        load_paper_autonomous_allocation_proposal_db_history_metrics_report,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper autonomous allocation proposal "
            "DB history metrics read adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(dsn, autocommit=True)
    except Exception as exc:
        raise _redacted_paper_research_packet_db_history_error(
            exc,
            dsn=dsn,
            table_name=table_name,
        ) from None
    try:
        return load_paper_autonomous_allocation_proposal_db_history_metrics_report(
            connection,
            limit=limit,
            table_name=table_name,
            config=config,
            generated_at=generated_at,
        )
    except Exception as exc:
        raise _redacted_paper_research_packet_db_history_error(
            exc,
            dsn=dsn,
            table_name=table_name,
        ) from None
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _run_paper_autonomous_allocation_proposal_db_history_health(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: PaperAutonomousAllocationProposalDbHistoryHealthRunner | None,
) -> object:
    command_name = "paper-autonomous-allocation-proposal-db-history-health"
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError(f"{command_name} limit must be positive")
    generated_at = datetime.now(UTC)

    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history import (
        PaperAutonomousAllocationProposalDbHistoryConfig,
    )
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health import (
        PaperAutonomousAllocationProposalDbHistoryHealthConfig,
    )

    history_config = PaperAutonomousAllocationProposalDbHistoryConfig()
    health_config = PaperAutonomousAllocationProposalDbHistoryHealthConfig()
    if runner is not None:
        try:
            return runner(
                dsn=dsn,
                table_name=table_name,
                limit=limit,
                history_config=history_config,
                health_config=health_config,
                generated_at=generated_at,
            )
        except Exception as exc:
            raise _redacted_paper_research_packet_db_history_error(
                exc,
                dsn=dsn,
                table_name=table_name,
            ) from None

    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_load import (
        load_paper_autonomous_allocation_proposal_db_history_health_report,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper autonomous allocation proposal "
            "DB history health read adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper autonomous allocation proposal database",
        ) from None
    try:
        return load_paper_autonomous_allocation_proposal_db_history_health_report(
            connection,
            limit=limit,
            table_name=table_name,
            history_config=history_config,
            health_config=health_config,
            generated_at=generated_at,
        )
    except Exception as exc:
        raise _redacted_paper_research_packet_db_history_error(
            exc,
            dsn=dsn,
            table_name=table_name,
        ) from None
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _run_paper_autonomous_allocation_proposal_db_history_health_trend(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: PaperAutonomousAllocationProposalDbHistoryHealthTrendRunner | None,
) -> object:
    command_name = "paper-autonomous-allocation-proposal-db-history-health-trend"
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError(f"{command_name} limit must be positive")
    generated_at = datetime.now(UTC)

    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health import (
        PaperAutonomousAllocationProposalDbHistoryHealthConfig,
    )
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend import (
        PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig,
    )

    health_config = PaperAutonomousAllocationProposalDbHistoryHealthConfig()
    trend_config = PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig()
    if runner is not None:
        try:
            return runner(
                dsn=dsn,
                table_name=table_name,
                limit=limit,
                health_config=health_config,
                trend_config=trend_config,
                generated_at=generated_at,
            )
        except Exception as exc:
            raise _redacted_paper_research_packet_db_history_error(
                exc,
                dsn=dsn,
                table_name=table_name,
            ) from None

    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend_load import (
        load_paper_autonomous_allocation_proposal_db_history_health_trend_report,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper autonomous allocation proposal "
            "DB history health trend read adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper autonomous allocation proposal database",
        ) from None
    try:
        return load_paper_autonomous_allocation_proposal_db_history_health_trend_report(
            connection,
            limit=limit,
            table_name=table_name,
            health_config=health_config,
            trend_config=trend_config,
            generated_at=generated_at,
        )
    except Exception as exc:
        raise _redacted_paper_research_packet_db_history_error(
            exc,
            dsn=dsn,
            table_name=table_name,
        ) from None
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _run_paper_autonomous_allocation_proposal_db_history_health_trend_gate(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: (
        PaperAutonomousAllocationProposalDbHistoryHealthTrendGateRunner | None
    ),
) -> object:
    command_name = (
        "paper-autonomous-allocation-proposal-db-history-health-trend-gate"
    )
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError(f"{command_name} limit must be positive")
    generated_at = datetime.now(UTC)

    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health import (
        PaperAutonomousAllocationProposalDbHistoryHealthConfig,
    )
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend import (
        PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig,
    )
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend_gate import (
        PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig,
    )

    health_config = PaperAutonomousAllocationProposalDbHistoryHealthConfig()
    trend_config = PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig()
    gate_config = PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig()
    if runner is not None:
        try:
            return runner(
                dsn=dsn,
                table_name=table_name,
                limit=limit,
                health_config=health_config,
                trend_config=trend_config,
                gate_config=gate_config,
                generated_at=generated_at,
            )
        except Exception as exc:
            raise _redacted_paper_research_packet_db_history_error(
                exc,
                dsn=dsn,
                table_name=table_name,
            ) from None

    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend_gate_load import (
        load_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper autonomous allocation proposal "
            "DB history health trend gate read adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper autonomous allocation proposal database",
        ) from None
    try:
        return load_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(
            connection,
            limit=limit,
            table_name=table_name,
            health_config=health_config,
            trend_config=trend_config,
            gate_config=gate_config,
            generated_at=generated_at,
        )
    except Exception as exc:
        raise _redacted_paper_research_packet_db_history_error(
            exc,
            dsn=dsn,
            table_name=table_name,
        ) from None
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _run_paper_research_packet_operator_flow_db_history_gate(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: PaperResearchPacketOperatorFlowDbHistoryGateRunner | None,
) -> object:
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError(
            "paper-research-packet-operator-flow-db-history-gate limit must be positive",
        )
    generated_at = datetime.now(UTC)

    from polymarket_alpha_lab.paper_research_packet_operator_flow_db_history import (
        PaperResearchPacketOperatorFlowDbHistoryConfig,
    )
    from polymarket_alpha_lab.paper_research_packet_operator_flow_db_history_gate import (
        PaperResearchPacketOperatorFlowDbHistoryGateConfig,
    )

    history_config = PaperResearchPacketOperatorFlowDbHistoryConfig()
    gate_config = PaperResearchPacketOperatorFlowDbHistoryGateConfig()
    if runner is not None:
        try:
            return runner(
                dsn=dsn,
                table_name=table_name,
                limit=limit,
                history_config=history_config,
                gate_config=gate_config,
                generated_at=generated_at,
            )
        except Exception as exc:
            raise _redacted_paper_research_packet_db_history_error(
                exc,
                dsn=dsn,
                table_name=table_name,
            ) from None

    from polymarket_alpha_lab.paper_research_packet_operator_flow_db_history_gate_load import (
        load_paper_research_packet_operator_flow_db_history_gate_report,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper research packet operator-flow "
            "DB history gate read adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper research packet operator-flow database",
        ) from None
    try:
        return load_paper_research_packet_operator_flow_db_history_gate_report(
            connection,
            limit=limit,
            table_name=table_name,
            history_config=history_config,
            gate_config=gate_config,
            generated_at=generated_at,
        )
    except Exception as exc:
        raise _redacted_paper_research_packet_db_history_error(
            exc,
            dsn=dsn,
            table_name=table_name,
        ) from None
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _run_paper_autonomous_screening_decision_support_gate(
    *,
    rank_stability_dsn: str | None,
    rank_stability_table_name: str | None,
    operator_flow_dsn: str,
    operator_flow_table_name: str,
    action_queue_dsn: str,
    action_queue_table_name: str,
    limit: int,
    runner: PaperAutonomousScreeningDecisionSupportGateRunner | None,
) -> object:
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError(
            "paper-autonomous-screening-decision-support-gate limit must be positive",
        )
    generated_at = datetime.now(UTC)

    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate import (
        DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_CONFIG_VERSION,
    )
    from polymarket_alpha_lab.paper_research_packet_operator_flow_db_history import (
        PaperResearchPacketOperatorFlowDbHistoryConfig,
    )
    from polymarket_alpha_lab.paper_research_packet_operator_flow_db_history_gate import (
        PaperResearchPacketOperatorFlowDbHistoryGateConfig,
    )

    gate_config = _PaperAutonomousScreeningDecisionSupportGateConfig(
        config_version=(
            DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_CONFIG_VERSION
        ),
    )
    if runner is not None:
        runner_kwargs = {
            "operator_flow_dsn": operator_flow_dsn,
            "operator_flow_table_name": operator_flow_table_name,
            "action_queue_dsn": action_queue_dsn,
            "action_queue_table_name": action_queue_table_name,
            "limit": limit,
            "gate_config": gate_config,
            "generated_at": generated_at,
        }
        if rank_stability_dsn is not None:
            runner_kwargs["rank_stability_dsn"] = rank_stability_dsn
            runner_kwargs["rank_stability_table_name"] = rank_stability_table_name
        try:
            return runner(**runner_kwargs)
        except Exception as exc:
            raise _redacted_paper_autonomous_screening_gate_error(
                exc,
                rank_stability_dsn=rank_stability_dsn,
                rank_stability_table_name=rank_stability_table_name,
                operator_flow_dsn=operator_flow_dsn,
                operator_flow_table_name=operator_flow_table_name,
                action_queue_dsn=action_queue_dsn,
                action_queue_table_name=action_queue_table_name,
            ) from None

    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_load import (
        load_paper_autonomous_screening_decision_support_gate_report,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper autonomous screening "
            "decision-support gate read adapter; install the postgres extra.",
        ) from exc
    if operator_flow_dsn != action_queue_dsn:
        raise RuntimeError(
            "paper-autonomous-screening-decision-support-gate read adapter "
            "requires operator-flow and action-gated queue decision-support "
            "DB DSNs to use the same DSN",
        )
    if rank_stability_dsn is not None and rank_stability_dsn != operator_flow_dsn:
        raise RuntimeError(
            "paper-autonomous-screening-decision-support-gate read adapter "
            "requires enabled rank-stability DB DSN to use the same DSN",
        )
    connection = None
    try:
        connection = psycopg.connect(operator_flow_dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper autonomous screening gate "
            "upstream databases",
        ) from None
    try:
        loader_kwargs = {
            "operator_flow_history_limit": limit,
            "operator_flow_table_name": operator_flow_table_name,
            "operator_flow_history_config": PaperResearchPacketOperatorFlowDbHistoryConfig(),
            "operator_flow_gate_config": PaperResearchPacketOperatorFlowDbHistoryGateConfig(),
            "action_gated_queue_limit": limit,
            "action_gated_queue_table_name": action_queue_table_name,
            "action_gated_queue_risk_status": None,
            "action_gated_queue_risk_config_version": None,
            "include_action_gated_queue_trend_report": True,
            "gate_config": gate_config,
            "generated_at": generated_at,
        }
        if rank_stability_dsn is not None:
            loader_kwargs.update(
                {
                    "project_screening_rank_stability_limit": limit,
                    "project_screening_rank_stability_table_name": rank_stability_table_name,
                    "project_screening_rank_stability_config_version": None,
                    "project_screening_rank_stability_status": None,
                },
            )
        return load_paper_autonomous_screening_decision_support_gate_report(
            connection,
            **loader_kwargs,
        )
    except Exception as exc:
        raise _redacted_paper_autonomous_screening_gate_error(
            exc,
            rank_stability_dsn=rank_stability_dsn,
            rank_stability_table_name=rank_stability_table_name,
            operator_flow_dsn=operator_flow_dsn,
            operator_flow_table_name=operator_flow_table_name,
            action_queue_dsn=action_queue_dsn,
            action_queue_table_name=action_queue_table_name,
        ) from None
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass


def _run_paper_autonomous_allocation_proposal(
    *,
    screening_gate_dsn: str,
    screening_gate_table_name: str,
    action_gated_queue_decision_support_dsn: str,
    action_gated_queue_decision_support_table_name: str,
    source_queue_dsn: str,
    source_queue_table_name: str,
    limit: int,
    runner: PaperAutonomousAllocationProposalRunner | None,
) -> object:
    _require_paper_autonomous_allocation_proposal_limit(limit)
    generated_at = datetime.now(UTC)

    if runner is not None:
        try:
            return runner(
                screening_gate_dsn=screening_gate_dsn,
                screening_gate_table_name=screening_gate_table_name,
                action_gated_queue_decision_support_dsn=(
                    action_gated_queue_decision_support_dsn
                ),
                action_gated_queue_decision_support_table_name=(
                    action_gated_queue_decision_support_table_name
                ),
                source_queue_dsn=source_queue_dsn,
                source_queue_table_name=source_queue_table_name,
                limit=limit,
                generated_at=generated_at,
            )
        except Exception as exc:
            raise _redacted_paper_autonomous_allocation_proposal_error(
                exc,
                screening_gate_dsn=screening_gate_dsn,
                screening_gate_table_name=screening_gate_table_name,
                action_gated_queue_decision_support_dsn=(
                    action_gated_queue_decision_support_dsn
                ),
                action_gated_queue_decision_support_table_name=(
                    action_gated_queue_decision_support_table_name
                ),
                source_queue_dsn=source_queue_dsn,
                source_queue_table_name=source_queue_table_name,
            ) from None

    if not (
        screening_gate_dsn
        == action_gated_queue_decision_support_dsn
        == source_queue_dsn
    ):
        raise RuntimeError(
            "paper-autonomous-allocation-proposal read adapter requires all "
            "upstream DB DSNs to match",
        )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper autonomous allocation proposal "
            "read adapter; install the postgres extra.",
        ) from exc

    connection = None
    try:
        connection = psycopg.connect(screening_gate_dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper autonomous allocation proposal "
            "upstream databases",
        ) from None
    try:
        return _load_paper_autonomous_allocation_proposal_report(
            connection,
            screening_gate_limit=limit,
            screening_gate_table_name=screening_gate_table_name,
            action_gated_queue_decision_support_limit=limit,
            action_gated_queue_decision_support_table_name=(
                action_gated_queue_decision_support_table_name
            ),
            source_queue_limit=limit,
            source_queue_table_name=source_queue_table_name,
            generated_at=generated_at,
        )
    except Exception as exc:
        raise _redacted_paper_autonomous_allocation_proposal_error(
            exc,
            screening_gate_dsn=screening_gate_dsn,
            screening_gate_table_name=screening_gate_table_name,
            action_gated_queue_decision_support_dsn=(
                action_gated_queue_decision_support_dsn
            ),
            action_gated_queue_decision_support_table_name=(
                action_gated_queue_decision_support_table_name
            ),
            source_queue_dsn=source_queue_dsn,
            source_queue_table_name=source_queue_table_name,
        ) from None
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass


def _load_paper_autonomous_allocation_proposal_report(
    connection: object,
    **kwargs: object,
) -> object:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_load import (
        load_paper_autonomous_allocation_proposal_report,
    )

    return load_paper_autonomous_allocation_proposal_report(connection, **kwargs)


def _run_outcome_tracking_db_history(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    stale_after_seconds: int,
    runner: OutcomeTrackingDbHistoryRunner | None,
) -> OutcomeFreshnessReport:
    generated_at = datetime.now(UTC)
    config_version = "outcome-tracking-db-history-v0"
    if runner is not None:
        return runner(
            dsn=dsn,
            table_name=table_name,
            limit=limit,
            stale_after_seconds=stale_after_seconds,
            config_version=config_version,
            generated_at=generated_at,
        )

    from polymarket_alpha_lab.outcome_tracking_db_history_load import (
        load_outcome_tracking_db_history_report,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the outcome tracking DB history "
            "psycopg adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(dsn)
    except Exception:
        raise RuntimeError(
            "failed to connect to the outcome tracking database",
        ) from None
    try:
        report = load_outcome_tracking_db_history_report(
            generated_at=generated_at,
            config_version=config_version,
            connection=connection,
            stale_after_seconds=stale_after_seconds,
            limit=limit,
            table_name=table_name,
        )
        connection.commit()
        return report
    except BaseException:
        try:
            connection.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _run_local_observability_trends_db_history(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: LocalObservabilityTrendsDbHistoryRunner | None,
) -> LocalObservabilityTrendsDbHistoryReport:
    generated_at = datetime.now(UTC)
    config = LocalObservabilityTrendsDbHistoryConfig(
        config_version="local-observability-trends-db-history-v0",
    )
    if runner is not None:
        return runner(
            dsn=dsn,
            table_name=table_name,
            limit=limit,
            config=config,
            generated_at=generated_at,
        )

    from polymarket_alpha_lab.local_observability_trends_db_history_load import (
        load_local_observability_trends_db_history_report,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the local observability trends "
            "psycopg adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(dsn)
    except Exception:
        raise RuntimeError(
            "failed to connect to the local observability trends database",
        ) from None
    try:
        report = load_local_observability_trends_db_history_report(
            generated_at=generated_at,
            config_version=config.config_version,
            connection=connection,
            limit=limit,
            table_name=table_name,
        )
        connection.commit()
        return report
    except BaseException:
        try:
            connection.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _print_nav_risk_summary(report: "PaperNavRiskMetricsReport") -> None:
    """Print a compact NAV risk report summary to stdout."""

    print(
        "nav-risk: "
        f"snapshots={report.nav_snapshot_count} "
        f"latest_exit_nav={report.latest_exit_nav} "
        f"max_drawdown={report.max_drawdown} "
        f"max_drawdown_pct={report.max_drawdown_pct}",
    )


def _print_cost_audit_summary(report: PaperTradeCostAuditReport) -> None:
    """Print a compact paper trade cost audit summary."""

    print(
        "cost-audit: "
        f"trades={report.trade_count} "
        f"filled={report.total_filled_size} "
        f"requested={report.total_requested_size} "
        f"fill_rate={report.fill_rate} "
        f"mean_edge_cost_drag={report.mean_edge_cost_drag} "
        f"total_edge_cost_drag={report.total_edge_cost_drag} "
        f"partial_fills={report.partial_fill_count} "
        "negative_cost_adjusted_edge="
        f"{report.negative_cost_adjusted_edge_count}",
    )
    if report.mean_research_slippage is not None:
        print(f"  mean_research_slippage={report.mean_research_slippage}")
    if report.mean_fill_slippage is not None:
        print(f"  mean_fill_slippage={report.mean_fill_slippage}")
    if report.largest_single_trade_cost_drag is not None:
        print(
            "  largest_single_trade_cost_drag="
            f"{report.largest_single_trade_cost_drag}",
        )


def _print_performance_summary(summary: PerformanceSummary) -> None:
    """Print a human-readable performance summary to stdout."""

    print(
        "history: "
        f"cycles={summary.cycle_count} "
        f"markets_scanned={summary.total_scan_market_count} "
        f"candidates_ready={summary.total_snapshot_ready_count} "
        f"cost_aware_reports={summary.total_cost_aware_report_count} "
        f"paper_trades={summary.paper_trade_count} "
        f"nav_snapshots={summary.nav_snapshot_count}",
    )
    if summary.last_exit_nav is not None:
        print(f"  last_exit_nav={summary.last_exit_nav}")
    if summary.last_starting_cash is not None:
        print(f"  last_starting_cash={summary.last_starting_cash}")
    if summary.total_realized_pnl is not None:
        print(f"  total_realized_pnl={summary.total_realized_pnl}")
    if summary.first_cycle_at is not None and summary.last_cycle_at is not None:
        print(
            f"  cycle_span={summary.first_cycle_at.isoformat()} "
            f"to {summary.last_cycle_at.isoformat()}",
        )


def _print_strategy_audit_summary(
    report: PaperStrategyRiskAuditReport,
    *,
    persisted: bool = False,
) -> None:
    """Print a compact local strategy audit summary."""

    print(
        "strategy-audit: "
        f"status={report.status} "
        f"gates={report.gate_count} "
        f"pass={report.pass_count} "
        f"fail={report.fail_count} "
        f"incomplete={report.incomplete_count} "
        f"persisted={persisted}",
    )
    for gate in report.gate_results:
        print(
            f"  {gate.gate_name}: "
            f"status={gate.status} "
            f"observed={gate.observed_value} "
            f"threshold={gate.threshold}",
        )


def _print_strategy_audit_history_summary(
    report: PaperStrategyRiskAuditHistoryReport,
    *,
    prefix: str = "strategy-audit-history",
) -> None:
    status_counts = {
        row.audit_status: row.audit_count for row in report.status_rows
    }
    first = _iso_or_none(report.first_audit_generated_at)
    latest = _iso_or_none(report.latest_audit_generated_at)
    latest_status = report.latest_audit_status or "none"
    print(
        f"{prefix}: "
        f"reports={report.audit_report_count} "
        f"status={report.status} "
        f"latest_status={latest_status} "
        f"audit_ready={status_counts['audit_ready']} "
        f"insufficient_evidence={status_counts['insufficient_evidence']} "
        f"blocked_by_risk={status_counts['blocked_by_risk']} "
        f"first={first} "
        f"latest={latest} "
        f"consecutive_non_ready={report.consecutive_non_ready_count}",
    )
    print(
        "  latest_failed_gates="
        f"{_csv_or_none(report.latest_failed_gate_names)}",
    )
    print(
        "  latest_incomplete_gates="
        f"{_csv_or_none(report.latest_incomplete_gate_names)}",
    )
    gate_counts = {
        (row.gate_name, row.gate_status): row.audit_count
        for row in report.gate_status_summaries
    }
    for gate_name in (
        "paper_history",
        "settlement_evidence",
        "forecast_quality",
        "cost_discipline",
        "nav_drawdown",
        "open_exposure",
    ):
        print(
            f"  {gate_name}: "
            f"pass={gate_counts[(gate_name, 'pass')]} "
            f"fail={gate_counts[(gate_name, 'fail')]} "
            f"incomplete={gate_counts[(gate_name, 'incomplete')]}",
        )


def _print_strategy_cycle_report_db_history_summary(
    report: PaperStrategyCycleReportHistoryReport,
) -> None:
    print(
        "strategy-cycle-db-history: "
        f"status={report.history_status} "
        f"reports={report.report_count} "
        f"latest_snapshot_ready_share={report.latest_snapshot_ready_share} "
        f"blocked_market_share={report.blocked_market_share}",
    )


def _print_strategy_cycle_history_gate_summary(
    report: object,
    *,
    persisted: bool,
) -> None:
    persisted_text = "true" if persisted else "false"
    print(
        "strategy-cycle-history-gate: "
        f"status={report.gate_status} "
        f"source_history_status={report.source_history_status} "
        f"reports={report.source_report_count} "
        f"latest_snapshot_ready_share={report.latest_snapshot_ready_share} "
        f"blocked_market_share={report.blocked_market_share} "
        f"persisted={persisted_text}",
    )


def _print_strategy_recommendation_history_summary(
    report: PaperStrategyRecommendationHistoryReport,
    *,
    latest_selected_count: int,
    latest_selected_notional: Decimal,
    selection_score_metrics: dict[str, object] | None = None,
) -> None:
    print(
        "strategy-recommendation-history: "
        f"source_reports={report.source_report_count} "
        f"total_candidates={report.total_candidate_count} "
        f"total_recommend={report.total_recommend_count} "
        f"total_watch={report.total_watch_count} "
        f"total_reject={report.total_reject_count} "
        f"latest_candidates={report.latest_candidate_count} "
        f"latest_recommend={report.latest_recommend_count} "
        f"latest_selected={latest_selected_count} "
        f"latest_selected_notional={latest_selected_notional} "
        f"first={_iso_or_none(report.first_generated_at)} "
        f"latest={_iso_or_none(report.latest_generated_at)}",
    )
    _print_selection_score_trend_metrics(selection_score_metrics or {})


def _print_paper_recommendation_reason_trend_summary(
    report: PaperRecommendationReasonTrendReport,
    *,
    action_counts: Counter[str],
    reason_code_counts: Counter[tuple[str, str]],
) -> None:
    print(
        "paper-recommendation-reason-trend: "
        f"source_reports={report.source_report_count} "
        f"recommend={action_counts.get('recommend', 0)} "
        f"watch={action_counts.get('watch', 0)} "
        f"reject={action_counts.get('reject', 0)} "
        f"paper_only={report.paper_only} "
        f"report_only={report.report_only} "
        f"readonly={report.readonly}",
    )
    print(
        "  reason_code_counts_by_status: "
        f"{_format_reason_code_counts(reason_code_counts)}",
    )
    print(
        "  transitions: "
        f"{_format_reason_trend_transitions(report.transition_trend_rows)}",
    )


def _print_paper_probability_side_edge_report_summary(
    report: "PaperProbabilitySideEdgeReport",
    *,
    reason_code_counts: Counter[str],
) -> None:
    print(
        "paper-probability-side-edge-report: "
        f"input_rows={report.input_count} "
        f"row_count={report.row_count} "
        f"recommend={report.recommend_count} "
        f"watch={report.watch_count} "
        f"reject={report.reject_count} "
        f"paper_only={report.paper_only} "
        f"report_only={report.report_only} "
        f"readonly={report.readonly}",
    )
    print(
        "  reason_code_counts: "
        f"{_format_paper_probability_side_edge_reason_code_counts(reason_code_counts)}",
    )


def _print_paper_recommendation_queue_report_summary(
    report: object,
    *,
    reason_code_counts: Counter[str],
) -> None:
    print(
        "paper-recommendation-queue-report: "
        f"input_count={report.input_count} "
        f"queue_count={report.queue_count} "
        f"research_review={report.research_review_count} "
        f"await_fresh_context={report.await_fresh_context_count} "
        f"skip={report.skip_count} "
        f"excluded={report.excluded_count} "
        f"paper_only={report.paper_only} "
        f"report_only={report.report_only} "
        f"readonly={report.readonly}",
    )
    print(
        "  reason_code_counts: "
        f"{_format_paper_probability_side_edge_reason_code_counts(reason_code_counts)}",
    )


def _print_paper_recommendation_risk_budget_report_summary(
    report: object,
    *,
    zero_allocation_count: int,
) -> None:
    print(
        "paper-recommendation-risk-budget-report: "
        f"status={report.status} "
        f"selected_count={report.selected_count} "
        f"blocked_count={report.blocked_count} "
        f"zero_allocation_count={zero_allocation_count} "
        f"total_suggested_notional={report.total_suggested_notional} "
        f"remaining_total_notional={report.remaining_total_notional} "
        f"total_notional_utilization={report.total_notional_utilization} "
        "largest_single_recommendation_share="
        f"{report.largest_single_recommendation_share} "
        f"nav_notional={report.nav_notional} "
        f"paper_only={report.paper_only} "
        f"report_only={report.report_only} "
        f"readonly={report.readonly}",
    )
    print(
        "  reason_codes: "
        f"{_format_paper_recommendation_risk_budget_reason_codes(report.reason_codes)}",
    )


def _print_paper_probability_selection_summary_history_summary(report: object) -> None:
    print(
        "paper-probability-selection-summary-history: "
        f"source_report_count={report.source_report_count} "
        f"first_generated_at={_iso_or_none(report.first_generated_at)} "
        f"latest_generated_at={_iso_or_none(report.latest_generated_at)} "
        f"history_span_seconds={_none_or_value(report.history_span_seconds)} "
        f"latest_age_seconds={_none_or_value(report.latest_age_seconds)} "
        f"latest_queue_count={report.latest_queue_count} "
        f"latest_selected_count={report.latest_selected_count} "
        f"latest_pending_count={report.latest_pending_count} "
        f"latest_rejected_count={report.latest_rejected_count} "
        f"latest_skipped_count={report.latest_skipped_count} "
        f"aggregate_queue_count={report.aggregate_queue_count} "
        f"aggregate_selected_count={report.aggregate_selected_count} "
        f"aggregate_pending_count={report.aggregate_pending_count} "
        f"aggregate_rejected_count={report.aggregate_rejected_count} "
        f"aggregate_skipped_count={report.aggregate_skipped_count} "
        f"latest_selected_share={report.latest_selected_share} "
        f"average_selected_share={report.average_selected_share} "
        f"distinct_config_versions={_csv_or_none(report.distinct_config_versions)} "
        f"history_status={report.history_status} "
        f"recommended_next_step={report.recommended_next_step} "
        f"reason_codes={_csv_or_none(report.reason_codes)}",
    )
    print(
        "reason_code_counts: "
        f"{_format_probability_selection_history_reason_code_counts(report.reason_code_counts)}",
    )


def _print_paper_probability_selection_summary_history_trend_summary(
    report: object,
) -> None:
    print(
        "paper-probability-selection-summary-history-trend: "
        f"source_history_count={report.source_history_count} "
        f"first_generated_at={_iso_or_none(report.first_generated_at)} "
        f"latest_generated_at={_iso_or_none(report.latest_generated_at)} "
        f"history_span_seconds={report.history_span_seconds} "
        f"latest_history_status={report.latest_history_status} "
        f"latest_status_streak={report.latest_status_streak} "
        f"latest_selected_share={report.latest_selected_share} "
        f"average_selected_share={report.average_selected_share} "
        f"selected_share_delta={report.selected_share_delta} "
        f"stale_history_count={report.stale_history_count} "
        f"thin_history_count={report.thin_history_count} "
        f"trend_status={report.trend_status} "
        f"recommended_next_step={report.recommended_next_step} "
        "reason_codes="
        f"{_csv_or_none(_safe_reason_codes_for_cli(report.reason_codes))}",
    )
    print(
        "recurring_reason_code_counts: "
        f"{_format_safe_probability_selection_history_reason_code_counts(report.recurring_reason_code_counts)}",
    )


def _print_autonomous_market_scorer_history_summary(report: object) -> None:
    print(
        "autonomous-market-scorer-history: "
        f"source_report_count={report.source_report_count} "
        f"first_generated_at={_iso_or_none(report.first_generated_at)} "
        f"latest_generated_at={_iso_or_none(report.latest_generated_at)} "
        f"history_span_seconds={report.history_span_seconds} "
        f"latest_gate_status={report.latest_gate_status} "
        f"latest_gate_status_streak={report.latest_gate_status_streak} "
        f"latest_candidate_count={report.latest_candidate_count} "
        f"average_candidate_count={report.average_candidate_count} "
        f"latest_recommended_notional={report.latest_recommended_notional} "
        f"total_recommended_notional={report.total_recommended_notional} "
        f"notional_delta={report.notional_delta} "
        f"blocked_report_count={report.blocked_report_count} "
        f"skipped_report_count={report.skipped_report_count} "
        f"history_status={report.history_status} "
        f"recommended_next_step={report.recommended_next_step}",
    )
    market_count, max_market_count = _recurrence_count_summary(
        report.recurring_market_slug_counts,
    )
    condition_count, max_condition_count = _recurrence_count_summary(
        report.recurring_condition_id_counts,
    )
    print(
        "identifier_recurrence: "
        f"recurring_market_slug_count={market_count} "
        f"max_recurring_market_slug_report_count={max_market_count} "
        f"recurring_condition_id_count={condition_count} "
        f"max_recurring_condition_id_report_count={max_condition_count}",
    )
    safe_reason_codes = _safe_reason_codes_for_cli(report.reason_codes)
    redacted_reason_code_count = safe_reason_codes.count("<redacted-reason-code>")
    print(
        "reason_codes: "
        f"{_csv_or_none(safe_reason_codes)} "
        f"redacted_reason_code_count={redacted_reason_code_count}",
    )
    print(
        "recurring_reason_code_counts: "
        f"{_format_safe_autonomous_market_scorer_reason_code_counts(report.recurring_reason_code_counts)} "
        "redacted_recurring_reason_code_count="
        f"{_redacted_autonomous_market_scorer_reason_code_count(report.recurring_reason_code_counts)}",
    )


def _print_probability_selection_scorer_agreement_summary(report: object) -> None:
    print(
        "probability-selection-scorer-agreement: "
        f"generated_at={_iso_or_none(report.generated_at)} "
        f"config_version={report.config_version} "
        f"selection_generated_at={_iso_or_none(report.selection_generated_at)} "
        f"scorer_generated_at={_iso_or_none(report.scorer_generated_at)} "
        f"selected_count={report.selected_count} "
        f"scorer_candidate_count={report.scorer_candidate_count} "
        "selected_market_overlap_count="
        f"{report.selected_market_overlap_count} "
        "selected_condition_overlap_count="
        f"{report.selected_condition_overlap_count} "
        f"rejected_but_scored_count={report.rejected_but_scored_count} "
        f"scored_but_unselected_count={report.scored_but_unselected_count} "
        f"scorer_gate_status={report.scorer_gate_status} "
        f"agreement_status={report.agreement_status} "
        f"recommended_next_step={report.recommended_next_step} "
        f"paper_only={report.paper_only} "
        f"report_only={report.report_only} "
        f"readonly={report.readonly}",
    )
    print(
        "reason_codes: "
        f"{_csv_or_none(_safe_reason_codes_for_cli(report.reason_codes))}",
    )
    print(
        "reason_code_divergence_counts: "
        f"{_format_safe_probability_selection_history_reason_code_counts(report.reason_code_divergence_counts)}",
    )


def _print_probability_selection_scorer_agreement_trend_summary(
    report: object,
) -> None:
    print(
        "probability-selection-scorer-agreement-trend: "
        f"source_report_count={report.source_report_count} "
        f"first_generated_at={_iso_or_none(report.first_generated_at)} "
        f"latest_generated_at={_iso_or_none(report.latest_generated_at)} "
        f"history_span_seconds={report.history_span_seconds} "
        f"latest_agreement_status={report.latest_agreement_status} "
        f"latest_status_streak={report.latest_status_streak} "
        f"aligned_report_count={report.aligned_report_count} "
        f"low_overlap_report_count={report.low_overlap_report_count} "
        f"gate_blocked_report_count={report.gate_blocked_report_count} "
        f"missing_inputs_report_count={report.missing_inputs_report_count} "
        "insufficient_identifiers_report_count="
        f"{report.insufficient_identifiers_report_count} "
        f"average_selected_count={report.average_selected_count} "
        f"average_scorer_candidate_count={report.average_scorer_candidate_count} "
        f"trend_status={report.trend_status} "
        f"recommended_next_step={report.recommended_next_step} "
        "reason_codes="
        f"{_csv_or_none(_safe_reason_codes_for_cli(report.reason_codes))}",
    )
    print(
        "recurring_reason_code_counts: "
        f"{_format_safe_probability_selection_history_reason_code_counts(report.recurring_reason_code_counts)}",
    )


def _print_probability_selection_scorer_agreement_trend_gate_summary(
    report: object,
) -> None:
    print(
        "probability-selection-scorer-agreement-trend-gate: "
        f"gate_status={report.gate_status} "
        f"recommended_next_step={report.recommended_next_step} "
        f"source_report_count={report.source_report_count} "
        f"source_trend_status={report.source_trend_status} "
        f"source_recommended_next_step={report.source_recommended_next_step} "
        f"source_generated_at={_iso_or_none(report.source_generated_at)} "
        f"trend_report_age_seconds={report.trend_report_age_seconds} "
        f"latest_agreement_status={report.latest_agreement_status} "
        f"latest_agreement_status_streak={report.latest_agreement_status_streak} "
        f"aligned_report_count={report.aligned_report_count} "
        f"low_overlap_report_count={report.low_overlap_report_count} "
        f"gate_blocked_report_count={report.gate_blocked_report_count} "
        f"missing_inputs_report_count={report.missing_inputs_report_count} "
        "insufficient_identifiers_report_count="
        f"{report.insufficient_identifiers_report_count} "
        f"average_selected_count={report.average_selected_count} "
        f"average_scorer_candidate_count={report.average_scorer_candidate_count} "
        "reason_codes="
        f"{_csv_or_none(_safe_reason_codes_for_cli(report.reason_codes))}",
    )
    print(
        "reason_code_counts: "
        f"{_format_safe_probability_selection_gate_reason_code_counts(report.reason_code_counts)}",
    )
    print(
        "latest_source_reason_codes: "
        f"{_csv_or_none(_safe_reason_codes_for_cli(report.latest_source_reason_codes))}",
    )
    print(
        "recurring_source_reason_code_counts: "
        f"{_format_safe_probability_selection_history_reason_code_counts(report.recurring_source_reason_code_counts)}",
    )


def _recurrence_count_summary(rows: object) -> tuple[int, int]:
    values = tuple(rows)
    if not values:
        return (0, 0)
    return (len(values), max(getattr(row, "report_count") for row in values))


def _format_safe_autonomous_market_scorer_reason_code_counts(
    rows: tuple[object, ...],
) -> str:
    visible_rows = tuple(
        (
            _safe_reason_code_for_cli(getattr(row, "reason_code")),
            getattr(row, "report_count"),
        )
        for row in rows
        if _safe_reason_code_for_cli(getattr(row, "reason_code"))
        != "<redacted-reason-code>"
    )
    if not visible_rows:
        return "none"
    return ",".join(f"{reason_code}:{count}" for reason_code, count in visible_rows)


def _redacted_autonomous_market_scorer_reason_code_count(
    rows: tuple[object, ...],
) -> int:
    return sum(
        1
        for row in rows
        if _safe_reason_code_for_cli(getattr(row, "reason_code"))
        == "<redacted-reason-code>"
    )


def _format_safe_probability_selection_history_reason_code_counts(
    counts: tuple[tuple[str, int], ...],
) -> str:
    if not counts:
        return "none"
    return ",".join(
        f"{_safe_reason_code_for_cli(reason_code)}:{count}"
        for reason_code, count in counts
    )


def _format_safe_probability_selection_gate_reason_code_counts(
    rows: tuple[object, ...],
) -> str:
    if not rows:
        return "none"
    return ",".join(
        f"{_safe_reason_code_for_cli(row.reason_code)}:{row.report_count}"
        for row in rows
    )


def _format_probability_selection_history_reason_code_counts(
    counts: tuple[tuple[str, int], ...],
) -> str:
    if not counts:
        return "none"
    return ",".join(f"{reason_code}:{count}" for reason_code, count in counts)


def _safe_reason_codes_for_cli(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_safe_reason_code_for_cli(value) for value in values)


def _safe_reason_code_for_cli(value: str) -> str:
    if type(value) is not str:
        return "<redacted-reason-code>"
    if re.fullmatch(r"[a-z][a-z0-9_]*", value) is None:
        return "<redacted-reason-code>"
    if len(value) > 128 or re.fullmatch(r"[a-f0-9]{32,}", value) is not None:
        return "<redacted-reason-code>"
    normalized = value.lower().replace("_", "")
    forbidden_fragments = (
        "account",
        "apikey",
        "auth",
        "authorization",
        "condition",
        "conditionid",
        "credential",
        "description",
        "detail",
        "details",
        "hash",
        "marketdetails",
        "marketquestion",
        "marketslug",
        "order",
        "password",
        "payload",
        "payloadjson",
        "privatekey",
        "question",
        "reportsha256",
        "scorerows",
        "secret",
        "sha256",
        "title",
        "token",
        "wallet",
    )
    if any(fragment in normalized for fragment in forbidden_fragments):
        return "<redacted-reason-code>"
    return value


def _format_reason_code_counts(
    reason_code_counts: Counter[tuple[str, str]],
) -> str:
    if not reason_code_counts:
        return "none"
    ordered = sorted(
        reason_code_counts.items(),
        key=lambda item: (-item[1], item[0][0], item[0][1]),
    )
    return " ".join(
        f"{reason_code}[{source_status}]={count}"
        for (reason_code, source_status), count in ordered
    )


def _format_paper_probability_side_edge_reason_code_counts(
    reason_code_counts: Counter[str],
) -> str:
    if not reason_code_counts:
        return "none"
    ordered = sorted(reason_code_counts.items(), key=lambda item: (-item[1], item[0]))
    return " ".join(
        f"{reason_code}={count}" for reason_code, count in ordered
    )


def _format_paper_recommendation_risk_budget_reason_codes(
    reason_codes: tuple[str, ...],
) -> str:
    if not reason_codes:
        return "none"
    return " ".join(reason_codes)


def _format_reason_trend_transitions(
    transition_rows: tuple[PaperRecommendationTransitionTrendRow, ...],
) -> str:
    if not transition_rows:
        return "none"
    return " ".join(
        (
            f"{row.market_slug}:{row.side} "
            f"{row.from_status}->{row.to_status}={row.transition_count} "
            f"reasons={_csv_or_none(row.reason_codes)}"
        )
        for row in transition_rows
    )


def _print_selection_score_trend_metrics(metrics: dict[str, object]) -> None:
    metric_order = (
        "total_selected",
        "total_selected_count",
        "total_selected_notional",
        "latest_selected",
        "latest_selected_count",
        "latest_selected_notional",
        "first_recommendation_score",
        "latest_recommendation_score",
        "latest_selected_score",
    )
    parts = [
        f"{field_name}={metrics[field_name]}"
        for field_name in metric_order
        if field_name in metrics
    ]
    parts.extend(
        f"{field_name}={value}"
        for field_name, value in metrics.items()
        if field_name not in metric_order
    )
    if parts:
        print("  selection_score_trend: " + " ".join(parts))


def _print_strategy_evidence_summary(
    report: "PaperStrategyEvidenceSnapshotReport",
) -> None:
    print(
        "strategy-evidence: "
        f"status={report.status} "
        f"gaps={_csv_or_none(report.evidence_gap_names)} "
        f"cycles={report.cycle_count} "
        f"paper_trades={report.paper_trade_count} "
        f"nav_snapshots={report.nav_snapshot_count} "
        f"outcome_checked={_none_or_value(report.outcome_checked_count)} "
        f"outcome_resolved={_none_or_value(report.outcome_resolved_count)} "
        f"outcome_pending={_none_or_value(report.outcome_pending_count)} "
        f"strategy_audits={_none_or_value(report.audit_report_count)} "
        f"latest_audit_status={_none_or_value(report.latest_audit_status)} "
        "negative_cost_adjusted_edge="
        f"{report.negative_cost_adjusted_edge_count} "
        "unexecutable_open_positions="
        f"{report.unexecutable_open_position_count} "
        f"paper_only={report.paper_only} "
        f"report_only={report.report_only}",
    )


def _print_observability_trends_summary(
    report: LocalObservabilityTrendsReport,
    *,
    persisted: bool = False,
) -> None:
    strategy = report.strategy_evidence_trend
    outcome = report.outcome_freshness
    nav = report.nav_risk_trend
    cost = report.paper_trade_cost_trend
    print(
        "observability-trends: "
        f"strategy_evidence_status={strategy.latest_status} "
        f"strategy_evidence_snapshots={strategy.snapshot_report_count} "
        f"outcome_status={outcome.status} "
        f"outcome_reports={outcome.outcome_report_count} "
        f"nav_risk_status={nav.status} "
        f"nav_risk_reports={nav.nav_risk_report_count} "
        f"cost_status={cost.status} "
        f"cost_audit_reports={cost.cost_audit_report_count} "
        f"paper_only={report.paper_only} "
        f"report_only={report.report_only} "
        f"readonly={report.readonly} "
        f"persisted={persisted}",
    )
    print(
        "  strategy_evidence_latest_gaps="
        f"{_csv_or_none(strategy.latest_evidence_gap_names)}",
    )
    print(
        "  outcome_latest_age_seconds="
        f"{_none_or_value(outcome.latest_report_age_seconds)}",
    )
    print(
        "  nav_latest_exit_nav="
        f"{_none_or_value(nav.latest_exit_nav)}",
    )
    print(
        "  cost_latest_mean_edge_cost_drag="
        f"{_none_or_value(cost.latest_mean_edge_cost_drag)}",
    )


def _print_local_observability_trends_db_history_summary(
    report: LocalObservabilityTrendsDbHistoryReport,
) -> None:
    print(
        "local-observability-trends-db-history: "
        f"status={report.status} "
        f"report_count={report.report_count} "
        f"first_report_generated_at={_iso_or_none(report.first_report_generated_at)} "
        f"latest_report_generated_at={_iso_or_none(report.latest_report_generated_at)} "
        "latest_strategy_evidence_status="
        f"{_none_or_value(report.latest_strategy_evidence_status)} "
        f"latest_outcome_status={_none_or_value(report.latest_outcome_status)} "
        f"latest_nav_status={_none_or_value(report.latest_nav_status)} "
        f"latest_cost_status={_none_or_value(report.latest_cost_status)} "
        f"duplicate_generated_at_count={report.duplicate_generated_at_count} "
        f"consecutive_outcome_stale_count={report.consecutive_outcome_stale_count} "
        "consecutive_nav_warning_or_high_risk_count="
        f"{report.consecutive_nav_warning_or_high_risk_count} "
        "consecutive_cost_warning_or_critical_count="
        f"{report.consecutive_cost_warning_or_critical_count}",
    )
    print(
        "  status_rows: "
        "strategy_evidence="
        f"{_format_history_status_row_counts(report.strategy_evidence_status_rows)} "
        f"outcome={_format_history_status_row_counts(report.outcome_status_rows)} "
        f"nav={_format_history_status_row_counts(report.nav_status_rows)} "
        f"cost={_format_history_status_row_counts(report.cost_status_rows)}",
    )


def _print_outcome_tracking_db_history_summary(
    report: OutcomeFreshnessReport,
) -> None:
    print(
        "outcome-tracking-db-history: "
        f"status={report.status} "
        f"report_count={report.outcome_report_count} "
        f"first_report_generated_at={_iso_or_none(report.first_report_generated_at)} "
        f"latest_report_generated_at={_iso_or_none(report.latest_report_generated_at)} "
        f"latest_total_markets_checked={report.latest_total_markets_checked} "
        f"latest_resolved_count={report.latest_resolved_count} "
        f"latest_pending_count={report.latest_pending_count} "
        f"latest_resolved_ratio={_none_or_value(report.latest_resolved_ratio)} "
        f"latest_pending_ratio={_none_or_value(report.latest_pending_ratio)} "
        f"latest_report_age_seconds={_none_or_value(report.latest_report_age_seconds)} "
        f"consecutive_pending_count={report.consecutive_pending_count}",
    )
    print(
        "  status_rows: "
        f"{_format_outcome_freshness_status_row_counts(report.status_rows)}",
    )


def _print_nav_snapshot_db_trend_summary(
    report: PaperNavRiskTrendReport,
) -> None:
    print(
        "nav-snapshot-db-trend: "
        f"status={report.status} "
        f"report_count={report.nav_risk_report_count} "
        f"first_report_generated_at={_iso_or_none(report.first_report_generated_at)} "
        f"latest_report_generated_at={_iso_or_none(report.latest_report_generated_at)} "
        f"latest_exit_nav={_none_or_value(report.latest_exit_nav)} "
        f"latest_cumulative_return={_none_or_value(report.latest_cumulative_return)} "
        f"latest_max_drawdown={_none_or_value(report.latest_max_drawdown)} "
        f"latest_max_drawdown_pct={_none_or_value(report.latest_max_drawdown_pct)} "
        "latest_nav_return_volatility="
        f"{_none_or_value(report.latest_nav_return_volatility)} "
        f"latest_open_position_count={report.latest_open_position_count} "
        f"latest_fully_executable_count={report.latest_fully_executable_count} "
        f"latest_partially_executable_count={report.latest_partially_executable_count} "
        f"latest_no_exit_depth_count={report.latest_no_exit_depth_count} "
        "worst_observed_max_drawdown_pct="
        f"{_none_or_value(report.worst_observed_max_drawdown_pct)} "
        "consecutive_unexecutable_open_position_count="
        f"{report.consecutive_unexecutable_open_position_count}",
    )
    print(
        "  status_rows: "
        f"{_format_history_status_row_counts(report.status_rows)}",
    )


def _print_cost_audit_db_trend_summary(
    report: PaperTradeCostTrendReport,
) -> None:
    print(
        "cost-audit-db-trend: "
        f"status={report.status} "
        f"report_count={report.cost_audit_report_count} "
        f"first_report_generated_at={_iso_or_none(report.first_report_generated_at)} "
        f"latest_report_generated_at={_iso_or_none(report.latest_report_generated_at)} "
        f"latest_trade_count={report.latest_trade_count} "
        f"latest_fill_rate={_none_or_value(report.latest_fill_rate)} "
        "latest_mean_cost_adjusted_edge="
        f"{_none_or_value(report.latest_mean_cost_adjusted_edge)} "
        f"latest_mean_edge_cost_drag={_none_or_value(report.latest_mean_edge_cost_drag)} "
        "latest_negative_cost_adjusted_edge_count="
        f"{report.latest_negative_cost_adjusted_edge_count} "
        "worst_observed_mean_edge_cost_drag="
        f"{_none_or_value(report.worst_observed_mean_edge_cost_drag)} "
        "consecutive_negative_cost_adjusted_edge_count="
        f"{report.consecutive_negative_cost_adjusted_edge_count}",
    )
    print(
        "  status_rows: "
        f"{_format_cost_trend_status_row_counts(report.status_rows)}",
    )


def _print_cycle_snapshot_db_trend_summary(report: object) -> None:
    reason_code_counts = ",".join(
        f"{reason_code}:{count}" for reason_code, count in report.reason_code_counts
    )
    latest_reason_codes = ",".join(report.latest_reason_codes)
    print(
        "cycle-snapshot-db-trend: "
        f"snapshots={report.snapshot_count} "
        f"pass={report.pass_count} "
        f"watch={report.watch_count} "
        f"blocked={report.blocked_count} "
        f"latest_status={report.latest_status} "
        f"first={report.first_generated_at.isoformat()} "
        f"last={report.last_generated_at.isoformat()} "
        f"blocked_share={report.blocked_share} "
        f"watch_share={report.watch_share} "
        f"avg_stage_count={report.average_stage_count} "
        f"avg_artifact_count={report.average_artifact_count}",
    )
    print(f"trend_reason_codes: {reason_code_counts or 'none'}")
    print(f"latest_reason_codes: {latest_reason_codes or 'none'}")


def _print_cycle_snapshot_db_review_summary(report: object) -> None:
    reason_code_counts = ",".join(
        f"{row.reason_code}:{row.count}" for row in report.reason_code_counts
    )
    print(
        "paper-recommendation-cycle-review: "
        f"snapshots={report.snapshot_count} "
        f"pass={report.pass_snapshot_count} "
        f"watch={report.watch_snapshot_count} "
        f"blocked={report.blocked_snapshot_count} "
        f"latest_status={_none_or_value(report.latest_final_status)} "
        f"latest_generated_at={_iso_or_none(report.latest_generated_at)} "
        f"blocked_artifacts={report.blocked_artifact_count} "
        f"watch_artifacts={report.watch_artifact_count} "
        f"missing_required_artifacts="
        f"{_csv_or_none(report.missing_required_artifact_names)} "
        f"reason_codes={reason_code_counts or 'none'} "
        f"review_status={report.review_status} "
        f"stale_history={report.stale_history}",
    )


def _print_cycle_snapshot_db_action_gate_summary(report: object) -> None:
    reason_code_counts = ",".join(
        f"{row.reason_code}:{row.count}" for row in report.reason_code_counts
    )
    print(
        "paper-recommendation-cycle-action-gate: "
        f"review_status={report.review_status} "
        f"latest_status={_none_or_value(report.latest_final_status)} "
        f"action_status={report.action_status} "
        f"next_step={report.recommended_next_step} "
        f"missing_required_artifacts={report.missing_required_artifact_count} "
        f"blocked_reasons={report.blocked_reason_count} "
        f"watch_reasons={report.watch_reason_count} "
        f"reason_codes={reason_code_counts or 'none'}",
    )


def _print_action_gated_queue_decision_support_summary(
    priority_report: object,
    risk_report: object,
) -> None:
    print(
        "action-gated-queue-decision-support: "
        f"sources={priority_report.source_report_count} "
        f"priority_research_ready={priority_report.research_ready_count} "
        f"priority_watch={priority_report.watch_count} "
        f"priority_blocked={priority_report.blocked_count} "
        f"priority_total_ready_notional={priority_report.total_ready_notional} "
        f"top_priority_score={priority_report.top_research_priority_score} "
        f"average_priority_score={priority_report.average_research_priority_score} "
        f"risk_status={risk_report.status} "
        f"risk_next_step={risk_report.recommended_next_step} "
        f"risk_reasons={_csv_or_none(risk_report.reason_codes)}",
    )
    print(
        "queue_risk: "
        f"sources={risk_report.source_queue_count} "
        f"research_ready_sources={risk_report.research_ready_source_count} "
        f"watch_sources={risk_report.watch_source_count} "
        f"blocked_sources={risk_report.blocked_source_count} "
        f"candidates={risk_report.candidate_count} "
        f"ready={risk_report.ready_count} "
        f"watch={risk_report.watch_count} "
        f"blocked={risk_report.blocked_count} "
        f"blocked_reasons={risk_report.blocked_reason_count} "
        f"watch_reasons={risk_report.watch_reason_count} "
        f"total_ready_notional={risk_report.total_ready_notional} "
        f"largest_queue_ready_notional={risk_report.largest_queue_ready_notional} "
        f"total_ready_notional_utilization="
        f"{_none_or_value(risk_report.total_ready_notional_utilization)} "
        f"largest_queue_ready_notional_utilization="
        f"{_none_or_value(risk_report.largest_queue_ready_notional_utilization)} "
        f"source_config_versions="
        f"{_csv_or_none(risk_report.source_config_versions)}",
    )
    if not priority_report.priority_rows:
        print("top_priority: none")
        return

    top_row = priority_report.priority_rows[0]
    print(
        "top_priority: "
        f"rank={top_row.priority_rank} "
        f"source_generated_at={top_row.source_generated_at.isoformat()} "
        f"action_status={top_row.action_status} "
        f"research_priority={top_row.research_priority} "
        f"candidates={top_row.candidate_count} "
        f"ready={top_row.ready_count} "
        f"ready_notional={top_row.total_ready_notional} "
        f"priority_score={top_row.research_priority_score}",
    )


def _print_action_gated_queue_decision_support_trend_summary(
    report: object,
    *,
    persisted: bool,
) -> None:
    status_counts = dict(report.risk_status_counts)
    reason_code_counts = ",".join(
        f"{reason_code}:{count}"
        for reason_code, count in report.repeated_reason_code_counts
    )
    print(
        "action-gated-queue-decision-support-trend: "
        f"snapshots={report.source_snapshot_count} "
        f"first={_iso_or_none(report.first_generated_at)} "
        f"latest={_iso_or_none(report.latest_generated_at)} "
        f"latest_risk_status={_none_or_value(report.latest_risk_status)} "
        f"pass={status_counts.get('pass', 0)} "
        f"watch={status_counts.get('watch', 0)} "
        f"blocked={status_counts.get('blocked', 0)} "
        f"ready_notional_delta={_none_or_value(report.ready_notional_delta)} "
        f"top_priority_score_delta={_none_or_value(report.top_priority_score_delta)} "
        "average_priority_score_delta="
        f"{_none_or_value(report.average_priority_score_delta)} "
        f"duplicate_generated_at_count={report.duplicate_generated_at_count} "
        f"persisted={persisted}",
    )
    print(f"trend_reason_codes: {reason_code_counts or 'none'}")


def _print_action_gated_queue_decision_support_trend_db_history_summary(
    report: object,
) -> None:
    status_counts = dict(report.risk_status_counts)
    reason_code_counts = ",".join(
        f"{reason_code}:{count}"
        for reason_code, count in report.latest_reason_code_counts
    )
    print(
        "action-gated-queue-decision-support-trend-db-history: "
        f"trend_count={report.trend_count} "
        f"total_source_snapshot_count={report.total_source_snapshot_count} "
        "first_trend_generated_at="
        f"{_iso_or_none(report.first_trend_generated_at)} "
        "latest_trend_generated_at="
        f"{_iso_or_none(report.latest_trend_generated_at)} "
        f"latest_risk_status={_none_or_value(report.latest_risk_status)} "
        f"pass={status_counts.get('pass', 0)} "
        f"watch={status_counts.get('watch', 0)} "
        f"blocked={status_counts.get('blocked', 0)} "
        f"ready_notional_delta={_none_or_value(report.ready_notional_delta)} "
        f"top_priority_score_delta={_none_or_value(report.top_priority_score_delta)} "
        "average_priority_score_delta="
        f"{_none_or_value(report.average_priority_score_delta)} "
        f"source_queue_count_delta={_none_or_value(report.source_queue_count_delta)} "
        f"duplicate_generated_at_count={report.duplicate_generated_at_count} "
        "consecutive_latest_pass_count="
        f"{report.consecutive_latest_pass_count} "
        "consecutive_latest_watch_count="
        f"{report.consecutive_latest_watch_count} "
        "consecutive_latest_blocked_count="
        f"{report.consecutive_latest_blocked_count}",
    )
    print(f"latest_reason_codes: {reason_code_counts or 'none'}")


def _print_action_gated_queue_history_db_history_summary(report: object) -> None:
    status_counts = dict(report.action_status_counts)
    reason_code_counts = ",".join(
        f"{reason_code}:{count}" for reason_code, count in report.latest_reason_code_counts
    )
    print(
        "action-gated-queue-history-db-history: "
        f"history_report_count={report.history_report_count} "
        "first_history_generated_at="
        f"{_iso_or_none(report.first_history_generated_at)} "
        "latest_history_generated_at="
        f"{_iso_or_none(report.latest_history_generated_at)} "
        f"latest_source_report_count="
        f"{_none_or_value(report.latest_source_report_count)} "
        f"latest_action_status={_none_or_value(report.latest_action_status)} "
        "latest_recommended_next_step="
        f"{_none_or_value(report.latest_recommended_next_step)} "
        f"research_ready={status_counts.get('research_ready', 0)} "
        f"watch={status_counts.get('watch', 0)} "
        f"blocked={status_counts.get('blocked', 0)} "
        f"duplicate_generated_at_count={report.duplicate_generated_at_count} "
        "consecutive_latest_research_ready_count="
        f"{report.consecutive_latest_research_ready_count} "
        "consecutive_latest_watch_count="
        f"{report.consecutive_latest_watch_count} "
        "consecutive_latest_blocked_count="
        f"{report.consecutive_latest_blocked_count} "
        "latest_total_ready_notional="
        f"{_none_or_value(report.latest_total_ready_notional)} "
        "latest_ready_notional_delta="
        f"{_none_or_value(report.latest_ready_notional_delta)} "
        "latest_status_transition_count="
        f"{_none_or_value(report.latest_status_transition_count)}",
    )
    print(f"latest_reason_codes: {reason_code_counts or 'none'}")


def _print_action_gated_queue_history_summary(
    report: object,
    *,
    persisted: bool = False,
) -> None:
    latest_reason_code_counts = ",".join(
        f"{row.reason_code}={row.count}" for row in report.latest_reason_code_counts
    )
    print(
        "action-gated-queue-history: "
        f"source_report_count={report.source_report_count} "
        f"first_source_generated_at={_iso_or_none(report.first_source_generated_at)} "
        f"last_source_generated_at={_iso_or_none(report.last_source_generated_at)} "
        f"research_ready_count={report.research_ready_count} "
        f"watch_count={report.watch_count} "
        f"blocked_count={report.blocked_count} "
        f"total_ready_notional={report.total_ready_notional} "
        f"latest_action_status={_none_or_value(report.latest_action_status)} "
        "latest_recommended_next_step="
        f"{_none_or_value(report.latest_recommended_next_step)} "
        f"status_transition_count={report.status_transition_count} "
        f"ready_notional_delta={report.ready_notional_delta} "
        f"persisted={persisted} "
        f"latest_reason_code_counts={latest_reason_code_counts or 'none'}",
    )


def _print_strategy_candidate_research_queue_history_summary(
    report: object,
    *,
    persisted: bool = False,
) -> None:
    latest_primary_reason_code_counts = ",".join(
        f"{reason_code}={count}"
        for reason_code, count in report.latest_primary_reason_code_counts
    )
    latest_reason_codes = ",".join(report.latest_reason_codes)
    print(
        "strategy-candidate-research-queue-history: "
        f"source_report_count={report.source_report_count} "
        f"first_source_generated_at={_iso_or_none(report.first_source_generated_at)} "
        f"last_source_generated_at={_iso_or_none(report.last_source_generated_at)} "
        f"action_status_research_ready_count={report.action_status_research_ready_count} "
        f"action_status_watch_count={report.action_status_watch_count} "
        f"action_status_blocked_count={report.action_status_blocked_count} "
        f"research_status_ready_count={report.research_status_ready_count} "
        f"research_status_watch_count={report.research_status_watch_count} "
        f"research_status_blocked_count={report.research_status_blocked_count} "
        f"total_ready_notional={report.total_ready_notional} "
        f"total_selected_notional={report.total_selected_notional} "
        f"total_suggested_notional={report.total_suggested_notional} "
        f"latest_action_status={_none_or_value(report.latest_action_status)} "
        "latest_recommended_next_step="
        f"{_none_or_value(report.latest_recommended_next_step)} "
        f"latest_research_status={_none_or_value(report.latest_research_status)} "
        f"latest_top_research_priority_score={_none_or_value(report.latest_top_research_priority_score)} "
        "latest_average_research_ready_score="
        f"{_none_or_value(report.latest_average_research_ready_score)} "
        f"status_transition_count={report.status_transition_count} "
        f"ready_notional_delta={report.ready_notional_delta} "
        f"selected_notional_delta={report.selected_notional_delta} "
        f"latest_selected_count={report.latest_selected_count} "
        f"latest_skipped_count={report.latest_skipped_count} "
        f"latest_not_selected_count={report.latest_not_selected_count} "
        f"latest_primary_reason_code_counts={latest_primary_reason_code_counts or 'none'} "
        f"latest_reason_codes={latest_reason_codes or 'none'} "
        f"persisted={persisted}",
    )


def _print_paper_research_packet_operator_flow_summary(
    report: PaperResearchPacketOperatorFlowReport,
) -> None:
    print(
        "paper-research-packet-operator-flow: "
        f"packet_persisted={report.packet_persisted} "
        f"packet_row_count={report.packet_row_count} "
        f"quality_status={report.quality_status} "
        f"quality_persisted={report.quality_persisted} "
        f"history_status={report.history_status} "
        f"history_source_report_count={report.history_source_report_count}",
    )


def _print_paper_research_packet_summary(
    report: object,
    *,
    persisted: bool = False,
) -> None:
    print(
        "paper-research-packet: "
        f"generated_at={report.generated_at.isoformat()} "
        f"config_version={report.config_version} "
        f"input_row_count={report.input_row_count} "
        f"packet_row_count={report.packet_row_count} "
        f"included_count={report.included_count} "
        f"skipped_count={report.skipped_count} "
        f"high_priority_count={report.high_priority_count} "
        f"medium_priority_count={report.medium_priority_count} "
        f"low_priority_count={report.low_priority_count} "
        f"persisted={persisted}",
    )
    if not report.packet_rows:
        print("top_packet: none")
        return
    top_row = report.packet_rows[0]
    reason_codes = ",".join(top_row.reason_codes)
    print(
        "top_packet: "
        f"rank={top_row.packet_rank} "
        f"market_slug={top_row.market_slug} "
        f"side={top_row.side} "
        f"research_priority={top_row.research_priority} "
        f"recommendation_score={top_row.recommendation_score} "
        f"net_edge={top_row.net_edge} "
        f"allocated_notional={_none_or_value(top_row.allocated_notional)} "
        f"requested_notional={_none_or_value(top_row.requested_notional)} "
        f"reason_codes={reason_codes or 'none'}",
    )


def _print_paper_research_packet_quality_summary(
    report: object,
    *,
    persisted: bool = False,
) -> None:
    print(
        "paper-research-packet-quality: "
        f"generated_at={report.generated_at.isoformat()} "
        f"quality_status={report.quality_status} "
        f"source_generated_at={report.source_generated_at.isoformat()} "
        f"source_age_seconds={report.source_age_seconds} "
        f"included_share={_none_or_value(report.included_share)} "
        f"skipped_share={_none_or_value(report.skipped_share)} "
        f"check_count={report.check_count} "
        f"pass_count={report.pass_count} "
        f"watch_count={report.watch_count} "
        f"blocked_count={report.blocked_count} "
        f"persisted={persisted}",
    )
    checks = " ".join(
        f"{row.check_name}={row.status}" for row in report.check_rows
    )
    print(f"checks: {checks or 'none'}")
    top_reasons = " ".join(
        f"{row.reason_code}={row.count}" for row in report.reason_code_counts[:5]
    )
    print(f"top_reason_codes: {top_reasons or 'none'}")


def _print_paper_research_packet_quality_db_history_summary(report: object) -> None:
    print(
        "paper-research-packet-quality-db-history: "
        f"history_status={report.history_status} "
        f"source_report_count={report.source_report_count} "
        "first_source_generated_at="
        f"{_iso_or_none(report.first_source_generated_at)} "
        "latest_source_generated_at="
        f"{_iso_or_none(report.latest_source_generated_at)} "
        f"latest_quality_status={_none_or_value(report.latest_quality_status)} "
        f"latest_source_age_seconds={_none_or_value(report.latest_source_age_seconds)} "
        f"latest_included_share={_none_or_value(report.latest_included_share)} "
        f"latest_skipped_share={_none_or_value(report.latest_skipped_share)} "
        f"duplicate_generated_at_count={report.duplicate_generated_at_count}",
    )
    print(
        "status_rows: "
        f"{_format_quality_history_status_row_counts(report.quality_status_rows) or 'none'}",
    )
    latest_checks = " ".join(
        f"{row.check_name}={row.status}"
        for row in report.latest_check_rows
    )
    print(f"latest_checks: {latest_checks or 'none'}")
    recurring_reason_rows = " ".join(
        f"{row.check_status}:{row.reason_code}={row.report_count}"
        for row in report.recurring_reason_code_rows
    )
    print(f"recurring_reason_rows: {recurring_reason_rows or 'none'}")
    reason_codes = " ".join(report.reason_codes)
    print(f"reason_codes: {reason_codes or 'none'}")


def _print_paper_research_packet_operator_flow_db_history_summary(
    report: object,
) -> None:
    status_counts = _operator_flow_history_status_counts(report.flow_status_rows)
    print(
        "paper-research-packet-operator-flow-db-history: "
        f"history_status={report.history_status} "
        f"report_count={report.report_count} "
        "first_report_generated_at="
        f"{_iso_or_none(report.first_report_generated_at)} "
        "latest_report_generated_at="
        f"{_iso_or_none(report.latest_report_generated_at)} "
        f"latest_flow_status={_none_or_value(report.latest_flow_status)} "
        f"latest_packet_row_count={_none_or_value(report.latest_packet_row_count)} "
        f"latest_quality_status={_none_or_value(report.latest_quality_status)} "
        f"latest_history_status={_none_or_value(report.latest_history_status)} "
        f"pass={status_counts['pass']} "
        f"watch={status_counts['watch']} "
        f"blocked={status_counts['blocked']} "
        f"duplicate_generated_at_count={report.duplicate_generated_at_count} "
        f"consecutive_latest_pass_count={report.consecutive_latest_pass_count} "
        f"consecutive_latest_watch_count={report.consecutive_latest_watch_count} "
        f"consecutive_latest_blocked_count={report.consecutive_latest_blocked_count}",
    )
    print(
        "flow_status_rows: "
        f"{_format_operator_flow_history_status_row_counts(report.flow_status_rows) or 'none'}",
    )
    latest_reason_codes = " ".join(report.latest_reason_codes)
    print(f"latest_reason_codes: {latest_reason_codes or 'none'}")
    reason_code_rows = " ".join(
        f"{row.reason_code}={row.report_count}"
        for row in report.reason_code_rows
    )
    print(f"reason_code_rows: {reason_code_rows or 'none'}")
    reason_codes = " ".join(report.reason_codes)
    print(f"reason_codes: {reason_codes or 'none'}")


def _print_paper_autonomous_allocation_proposal_db_history_summary(
    report: object,
) -> None:
    status_counts = _allocation_proposal_history_status_counts(
        report.proposal_status_rows,
    )
    print(
        "paper-autonomous-allocation-proposal-db-history: "
        f"history_status={report.history_status} "
        f"report_count={report.report_count} "
        "first_report_generated_at="
        f"{_iso_or_none(report.first_report_generated_at)} "
        "latest_report_generated_at="
        f"{_iso_or_none(report.latest_report_generated_at)} "
        f"latest_proposal_status={_none_or_value(report.latest_proposal_status)} "
        "latest_screening_gate_status="
        f"{_none_or_value(report.latest_screening_gate_status)} "
        f"latest_queue_risk_status={_none_or_value(report.latest_queue_risk_status)} "
        "latest_allocation_input_count="
        f"{_none_or_value(report.latest_allocation_input_count)} "
        "latest_allocation_row_count="
        f"{_none_or_value(report.latest_allocation_row_count)} "
        f"latest_allocated_count={_none_or_value(report.latest_allocated_count)} "
        "latest_total_allocated_paper_notional="
        f"{_none_or_value(report.latest_total_allocated_paper_notional)} "
        f"pass={status_counts['pass']} "
        f"watch={status_counts['watch']} "
        f"blocked={status_counts['blocked']} "
        f"duplicate_generated_at_count={report.duplicate_generated_at_count} "
        f"consecutive_latest_pass_count={report.consecutive_latest_pass_count} "
        f"consecutive_latest_watch_count={report.consecutive_latest_watch_count} "
        f"consecutive_latest_blocked_count={report.consecutive_latest_blocked_count}",
    )
    print(
        "proposal_status_rows: "
        f"{_format_allocation_proposal_history_status_row_counts(report.proposal_status_rows) or 'none'}",
    )
    latest_reason_codes = " ".join(report.latest_reason_codes)
    print(f"latest_reason_codes: {latest_reason_codes or 'none'}")
    reason_code_rows = " ".join(
        f"{row.reason_code}={row.report_count}"
        for row in report.reason_code_rows
    )
    print(f"reason_code_rows: {reason_code_rows or 'none'}")
    reason_codes = " ".join(report.reason_codes)
    print(f"reason_codes: {reason_codes or 'none'}")


def _print_paper_autonomous_allocation_proposal_db_history_gate_summary(
    report: object,
) -> None:
    print(
        "paper-autonomous-allocation-proposal-db-history-gate: "
        f"gate_status={report.gate_status} "
        f"recommended_next_step={report.recommended_next_step} "
        f"source_report_count={report.source_report_count} "
        f"source_history_status={report.source_history_status} "
        f"latest_proposal_status={_none_or_value(report.latest_proposal_status)} "
        "latest_screening_gate_status="
        f"{_none_or_value(report.latest_screening_gate_status)} "
        f"latest_queue_risk_status={_none_or_value(report.latest_queue_risk_status)} "
        "latest_allocation_input_count="
        f"{_none_or_value(report.latest_allocation_input_count)} "
        "latest_allocation_row_count="
        f"{_none_or_value(report.latest_allocation_row_count)} "
        f"latest_allocated_count={_none_or_value(report.latest_allocated_count)} "
        "latest_total_allocated_paper_notional="
        f"{_none_or_value(report.latest_total_allocated_paper_notional)} "
        f"duplicate_generated_at_count={report.duplicate_generated_at_count} "
        f"latest_source_age_seconds={_none_or_value(report.latest_source_age_seconds)}",
    )
    reason_code_counts = " ".join(
        f"{row.reason_code}={row.report_count}"
        for row in report.reason_code_counts
    )
    print(f"reason_code_counts: {reason_code_counts or 'none'}")


def _print_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_summary(
    report: object,
) -> None:
    top_reason_codes = "none"
    if getattr(report, "diagnostics", None) is not None and getattr(
        report.diagnostics, "top_reason_codes", None
    ):
        top_reason_codes = ",".join(report.diagnostics.top_reason_codes)
    largest_concentration_group_type = "none"
    largest_concentration_share = "none"
    if getattr(report, "diagnostics", None) is not None:
        largest_concentration_group_type = _none_or_value(
            report.diagnostics.largest_concentration_group_type,
        )
        largest_concentration_share = _none_or_value(
            report.diagnostics.largest_concentration_share,
        )
    summary_parts = [
        "paper-autonomous-allocation-proposal-db-history-metrics-evaluation:",
        f"evaluation_status={report.evaluation_status}",
        f"recommended_next_step={report.recommended_next_step}",
        f"source_report_count={report.source_report_count}",
        f"latest_report_generated_at={_none_or_value(report.latest_report_generated_at)}",
        f"top_reason_codes={top_reason_codes}",
        f"top_reason_code_limit={report.diagnostics.top_reason_code_limit}",
        f"evaluated_budget_utilization={report.diagnostics.evaluated_budget_utilization}",
        f"evaluated_requested_fill_ratio={report.diagnostics.evaluated_requested_fill_ratio}",
        f"evaluated_concentration={report.diagnostics.evaluated_concentration}",
        f"evaluated_churn={report.diagnostics.evaluated_churn}",
        f"evaluated_edge_coverage={report.diagnostics.evaluated_edge_coverage}",
        f"evaluated_edge_quality={report.diagnostics.evaluated_edge_quality}",
        f"largest_concentration_group_type={largest_concentration_group_type}",
        f"largest_concentration_share={largest_concentration_share}",
    ]
    print(" ".join(summary_parts))


def _print_paper_autonomous_allocation_proposal_db_history_metrics_summary(
    report: object,
) -> None:
    latest_largest_market_share = None
    for row in report.latest_largest_concentration_rows:
        if getattr(row, "group_type", getattr(row, "kind", None)) == "market":
            latest_largest_market_share = getattr(
                row,
                "allocated_paper_notional_share",
                getattr(row, "share", None),
            )
            break
    summary_parts = [
        "paper-autonomous-allocation-proposal-db-history-metrics:",
        f"source_report_count={report.source_report_count}",
        f"latest_proposal_status={_none_or_value(report.latest_proposal_status)}",
        f"latest_budget_utilization={_none_or_value(report.latest_budget_utilization)}",
        f"latest_requested_fill_ratio={_none_or_value(report.latest_requested_fill_ratio)}",
        "latest_total_allocated_paper_notional="
        f"{_none_or_value(report.latest_total_allocated_paper_notional)}",
        f"latest_largest_market_share={_none_or_value(latest_largest_market_share)}",
        "latest_added_market_side_count="
        f"{_none_or_value(report.latest_added_market_side_count)}",
        "latest_removed_market_side_count="
        f"{_none_or_value(report.latest_removed_market_side_count)}",
        f"latest_notional_turnover={_none_or_value(report.latest_notional_turnover)}",
        f"latest_allocated_edge_share={_none_or_value(report.latest_allocated_edge_share)}",
        f"latest_expected_edge_notional={_none_or_value(report.latest_expected_edge_notional)}",
    ]
    print(" ".join(summary_parts))


def _print_paper_autonomous_allocation_proposal_db_history_health_summary(
    report: object,
) -> None:
    summary_parts = [
        "paper-autonomous-allocation-proposal-db-history-health:",
        f"health_status={report.health_status}",
        f"recommended_next_step={report.recommended_next_step}",
        f"history_report_count={report.history_report_count}",
        f"latest_history_status={_none_or_value(report.latest_history_status)}",
        f"latest_allocated_count={_none_or_value(report.latest_allocated_count)}",
        "latest_total_allocated_paper_notional="
        f"{_none_or_value(report.latest_total_allocated_paper_notional)}",
        f"latest_source_age_seconds={_none_or_value(report.latest_source_age_seconds)}",
        f"max_source_age_seconds={_none_or_value(report.max_source_age_seconds)}",
        f"pass_report_count={report.pass_report_count}",
        f"watch_report_count={report.watch_report_count}",
        f"blocked_report_count={report.blocked_report_count}",
        "duplicate_latest_report_generated_at_count="
        f"{report.duplicate_latest_report_generated_at_count}",
    ]
    print(" ".join(summary_parts))
    reason_code_counts = " ".join(
        f"{row.reason_code}={_reason_code_report_count(row)}"
        for row in report.reason_code_counts
    )
    print(f"reason_code_counts: {reason_code_counts or 'none'}")


def _print_paper_autonomous_allocation_proposal_db_history_health_trend_summary(
    report: object,
) -> None:
    latest_reason_code_counts = ",".join(
        f"{reason_code}={count}" for reason_code, count in report.latest_reason_code_counts
    )
    summary_parts = [
        "paper-autonomous-allocation-proposal-db-history-health-trend:",
        f"trend_count={report.source_health_report_count}",
        f"latest_health_status={_none_or_value(report.latest_health_status)}",
        "history_report_count_delta="
        f"{_none_or_value(report.history_report_count_delta)}",
        f"pass_report_count_delta={_none_or_value(report.pass_report_count_delta)}",
        f"watch_report_count_delta={_none_or_value(report.watch_report_count_delta)}",
        "blocked_report_count_delta="
        f"{_none_or_value(report.blocked_report_count_delta)}",
        "latest_allocated_count_delta="
        f"{_none_or_value(report.latest_allocated_count_delta)}",
        "latest_total_allocated_paper_notional_delta="
        f"{_none_or_value(report.latest_total_allocated_paper_notional_delta)}",
        f"duplicate_generated_at_count={report.duplicate_generated_at_count}",
        "consecutive_latest_watch_count="
        f"{report.consecutive_latest_watch_count}",
        "consecutive_latest_blocked_count="
        f"{report.consecutive_latest_blocked_count}",
        "latest_reason_code_counts="
        f"{latest_reason_code_counts or 'none'}",
    ]
    print(" ".join(summary_parts))


def _print_paper_autonomous_allocation_proposal_db_history_health_trend_gate_summary(
    report: object,
) -> None:
    reason_code_counts = " ".join(
        f"{row.reason_code}={_reason_code_report_count(row)}"
        for row in report.reason_code_counts
    )
    summary_parts = [
        "paper-autonomous-allocation-proposal-db-history-health-trend-gate:",
        f"gate_status={report.gate_status}",
        f"recommended_next_step={report.recommended_next_step}",
        f"source_health_report_count={report.source_health_report_count}",
        f"latest_health_status={_none_or_value(report.latest_health_status)}",
        f"latest_source_age_seconds={_none_or_value(report.latest_source_age_seconds)}",
        f"duplicate_generated_at_count={report.duplicate_generated_at_count}",
        "consecutive_latest_watch_count="
        f"{report.consecutive_latest_watch_count}",
        "consecutive_latest_blocked_count="
        f"{report.consecutive_latest_blocked_count}",
        f"watch_report_count_delta={_none_or_value(report.watch_report_count_delta)}",
        "blocked_report_count_delta="
        f"{_none_or_value(report.blocked_report_count_delta)}",
        f"reason_code_counts={reason_code_counts or 'none'}",
    ]
    print(" ".join(summary_parts))


def _print_paper_research_packet_operator_flow_db_history_gate_summary(
    report: object,
) -> None:
    print(
        "paper-research-packet-operator-flow-db-history-gate: "
        f"gate_status={report.gate_status} "
        f"recommended_next_step={report.recommended_next_step} "
        f"source_report_count={report.source_report_count} "
        f"source_history_status={report.source_history_status} "
        f"latest_flow_status={_none_or_value(report.latest_flow_status)} "
        f"duplicate_generated_at_count={report.duplicate_generated_at_count} "
        f"latest_source_age_seconds={_none_or_value(report.latest_source_age_seconds)}",
    )
    reason_code_counts = " ".join(
        f"{row.reason_code}={row.report_count}"
        for row in report.reason_code_counts
    )
    print(f"reason_code_counts: {reason_code_counts or 'none'}")



def _run_paper_execution_pipeline(
    *,
    screening_gate_dsn: str,
    screening_gate_table_name: str,
    limit: int,
) -> object:
    """Run the full paper-only execution pipeline.

    Reads the latest screening gate report from DB, then runs:
    proposal -> risk gate -> broker -> order lifecycle
    """
    import psycopg

    from polymarket_alpha_lab.paper_autonomous_proposal import (
        build_paper_autonomous_proposal_report,
    )
    from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate import (
        build_paper_autonomous_proposal_risk_gate_report,
    )
    from polymarket_alpha_lab.paper_broker import (
        build_paper_broker_execution_record,
    )
    from polymarket_alpha_lab.paper_autonomous_investment_ledger import (
        build_paper_autonomous_investment_ledger_report,
    )
    from polymarket_alpha_lab.paper_order_lifecycle import (
        build_paper_order_lifecycle_record,
    )
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_store import (
        load_paper_autonomous_screening_decision_support_gate_reports,
    )

    with psycopg.connect(screening_gate_dsn, autocommit=True) as conn:
        gate_reports = load_paper_autonomous_screening_decision_support_gate_reports(
            conn,
            table_name=screening_gate_table_name,
            limit=limit,
        )
    if not gate_reports:
        raise ValueError("no screening gate reports found")

    gate_report = gate_reports[0]  # loader returns newest first
    generated_at = gate_report.generated_at

    proposal_report = build_paper_autonomous_proposal_report(
        gate_report=gate_report,
        generated_at=generated_at,
    )
    risk_gate_report = build_paper_autonomous_proposal_risk_gate_report(
        proposal_report=proposal_report,
        generated_at=generated_at,
    )
    broker_record = build_paper_broker_execution_record(
        risk_gate_report=risk_gate_report,
        generated_at=generated_at,
    )
    lifecycle_record = build_paper_order_lifecycle_record(
        broker_record=broker_record,
        generated_at=generated_at,
    )
    investment_ledger_report = build_paper_autonomous_investment_ledger_report(
        broker_execution_records=(broker_record,),
        generated_at=generated_at,
    )

    return {
        "gate_report": gate_report,
        "proposal_report": proposal_report,
        "risk_gate_report": risk_gate_report,
        "broker_record": broker_record,
        "lifecycle_record": lifecycle_record,
        "investment_ledger_report": investment_ledger_report,
    }


def _persist_paper_execution_pipeline(
    *,
    pipeline_report: object,
    dsn: str,
    table_name: str,
    broker_dsn: str | None = None,
    broker_table_name: str | None = None,
    ledger_dsn: str | None = None,
    ledger_table_name: str | None = None,
) -> None:
    """Persist paper execution pipeline records to DB."""
    from polymarket_alpha_lab.paper_order_lifecycle_psycopg import (
        insert_paper_order_lifecycle_record_with_psycopg,
    )
    from polymarket_alpha_lab.paper_broker_psycopg import (
        insert_paper_broker_execution_record_with_psycopg,
    )
    from polymarket_alpha_lab.paper_autonomous_investment_ledger_psycopg import (
        insert_paper_autonomous_investment_ledger_report_with_psycopg,
    )

    lifecycle_record = pipeline_report["lifecycle_record"]
    insert_paper_order_lifecycle_record_with_psycopg(
        dsn=dsn,
        record=lifecycle_record,
        table_name=table_name,
    )
    persisted_parts = [f"lifecycle status={lifecycle_record.lifecycle_status}"]
    if broker_dsn is not None and broker_table_name is not None:
        broker_record = pipeline_report["broker_record"]
        insert_paper_broker_execution_record_with_psycopg(
            dsn=broker_dsn,
            record=broker_record,
            table_name=broker_table_name,
        )
        persisted_parts.append(f"broker status={broker_record.execution_status}")
    if ledger_dsn is not None and ledger_table_name is not None:
        ledger_report = pipeline_report["investment_ledger_report"]
        insert_paper_autonomous_investment_ledger_report_with_psycopg(
            dsn=ledger_dsn,
            report=ledger_report,
            table_name=ledger_table_name,
        )
        persisted_parts.append(f"ledger status={ledger_report.ledger_status}")
    print(f"paper-execution-pipeline: persisted {' '.join(persisted_parts)}")


def _load_paper_execution_pipeline_db_history(
    *,
    dsn: str,
    table_name: str,
    limit: int,
) -> object:
    """Load paper execution pipeline history from DB."""
    import psycopg

    from polymarket_alpha_lab.paper_order_lifecycle_store import (
        load_paper_order_lifecycle_records,
    )

    with psycopg.connect(dsn, autocommit=True) as conn:
        records = load_paper_order_lifecycle_records(
            conn,
            table_name=table_name,
            limit=limit,
        )
    return records


def _load_paper_autonomous_investment_ledger_from_broker_db(
    *,
    broker_dsn: str,
    broker_table_name: str,
    limit: int,
    source_config_version: str | None = None,
    execution_status: str | None = None,
    source_gate_status: str | None = None,
    max_latest_source_age_seconds: int = 86_400,
    generated_at: datetime | None = None,
) -> object:
    """Build a paper investment ledger from persisted broker execution records."""
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError("limit must be positive")
    from polymarket_alpha_lab.paper_autonomous_investment_ledger import (
        PaperAutonomousInvestmentLedgerConfig,
        build_paper_autonomous_investment_ledger_report,
    )
    from polymarket_alpha_lab.paper_broker_psycopg import (
        load_paper_broker_execution_records_with_psycopg,
    )

    broker_records = load_paper_broker_execution_records_with_psycopg(
        dsn=broker_dsn,
        table_name=broker_table_name,
        limit=limit,
        config_version=source_config_version,
        execution_status=execution_status,
        source_gate_status=source_gate_status,
    )
    config = PaperAutonomousInvestmentLedgerConfig(
        max_latest_source_age_seconds=max_latest_source_age_seconds,
    )
    return build_paper_autonomous_investment_ledger_report(
        broker_execution_records=tuple(broker_records),
        config=config,
        generated_at=datetime.now(UTC) if generated_at is None else generated_at,
    )


def _persist_paper_autonomous_investment_ledger_report(
    *,
    dsn: str,
    report: object,
    table_name: str,
) -> object:
    """Persist a paper investment ledger report through the psycopg adapter."""
    from polymarket_alpha_lab.paper_autonomous_investment_ledger_psycopg import (
        insert_paper_autonomous_investment_ledger_report_with_psycopg,
    )

    return insert_paper_autonomous_investment_ledger_report_with_psycopg(
        dsn=dsn,
        report=report,
        table_name=table_name,
    )


def _load_paper_autonomous_investment_ledger_db_history(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    config_version: str | None = None,
    ledger_status: str | None = None,
) -> object:
    """Load persisted paper investment ledger reports from the ledger DB."""
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError("limit must be positive")
    from polymarket_alpha_lab.paper_autonomous_investment_ledger_psycopg import (
        load_paper_autonomous_investment_ledger_reports_with_psycopg,
    )

    return load_paper_autonomous_investment_ledger_reports_with_psycopg(
        dsn=dsn,
        table_name=table_name,
        limit=limit,
        config_version=config_version,
        ledger_status=ledger_status,
    )


def _paper_autonomous_investment_ledger_db_config_from_env(
    command_name: str,
) -> tuple[str, str]:
    ledger_db_config = from_paper_autonomous_investment_ledger_db_env()
    if not ledger_db_config.enabled:
        raise ValueError(
            f"{command_name} requires paper autonomous investment ledger "
            "DB to be enabled",
        )
    ledger_dsn = ledger_db_config.dsn
    if ledger_dsn is None:
        raise ValueError(
            f"{command_name} requires a paper autonomous investment "
            "ledger DB DSN",
        )
    ledger_table_name = ledger_db_config.table_name
    if ledger_table_name is None:
        raise ValueError(
            f"{command_name} requires a paper autonomous investment "
            "ledger DB table",
        )
    return ledger_dsn, ledger_table_name


def _paper_autonomous_investment_ledger_db_history_health_config_from_env(
    command_name: str,
) -> tuple[str, str]:
    health_db_config = (
        from_paper_autonomous_investment_ledger_db_history_health_db_env()
    )
    if not health_db_config.enabled:
        raise ValueError(
            f"{command_name} requires paper autonomous investment ledger "
            "DB-history health DB to be enabled",
        )
    health_dsn = health_db_config.dsn
    if health_dsn is None:
        raise ValueError(
            f"{command_name} requires a paper autonomous investment ledger "
            "DB-history health DB DSN",
        )
    return health_dsn, health_db_config.table_name


def _run_paper_autonomous_investment_ledger_db_history_health(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: PaperAutonomousInvestmentLedgerDbHistoryHealthRunner | None = None,
) -> object:
    command_name = "paper-autonomous-investment-ledger-db-history-health"
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError(f"{command_name} limit must be positive")
    generated_at = datetime.now(UTC)

    from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health import (
        PaperAutonomousInvestmentLedgerDbHistoryHealthConfig,
    )

    config = PaperAutonomousInvestmentLedgerDbHistoryHealthConfig()
    if runner is not None:
        return runner(
            dsn=dsn,
            table_name=table_name,
            limit=limit,
            config=config,
            generated_at=generated_at,
        )

    from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_load import (
        load_paper_autonomous_investment_ledger_db_history_health_report,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper autonomous investment ledger "
            "DB history health read adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper autonomous investment ledger database",
        ) from None
    try:
        return load_paper_autonomous_investment_ledger_db_history_health_report(
            connection,
            limit=limit,
            table_name=table_name,
            config=config,
            generated_at=generated_at,
        )
    except Exception as exc:
        raise _redacted_paper_autonomous_investment_ledger_error(
            exc,
            broker_dsn=dsn,
            broker_table_name=table_name,
        ) from None
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _run_paper_autonomous_investment_ledger_db_history_health_trend(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: (
        PaperAutonomousInvestmentLedgerDbHistoryHealthTrendRunner | None
    ) = None,
) -> object:
    command_name = "paper-autonomous-investment-ledger-db-history-health-trend"
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError(f"{command_name} limit must be positive")
    generated_at = datetime.now(UTC)

    from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health import (
        PaperAutonomousInvestmentLedgerDbHistoryHealthConfig,
    )
    from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_trend import (
        PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig,
    )

    health_config = PaperAutonomousInvestmentLedgerDbHistoryHealthConfig()
    trend_config = PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig()
    if runner is not None:
        try:
            return runner(
                dsn=dsn,
                table_name=table_name,
                limit=limit,
                health_config=health_config,
                trend_config=trend_config,
                generated_at=generated_at,
            )
        except Exception as exc:
            raise _redacted_paper_autonomous_investment_ledger_error(
                exc,
                broker_dsn=dsn,
                broker_table_name=table_name,
            ) from None

    from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_trend_load import (
        load_paper_autonomous_investment_ledger_db_history_health_trend_report,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper autonomous investment ledger "
            "DB history health trend read adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper autonomous investment ledger "
            "DB-history health report database",
        ) from None
    try:
        return load_paper_autonomous_investment_ledger_db_history_health_trend_report(
            connection,
            limit=limit,
            table_name=table_name,
            health_config=health_config,
            trend_config=trend_config,
            generated_at=generated_at,
        )
    except Exception as exc:
        raise _redacted_paper_autonomous_investment_ledger_error(
            exc,
            broker_dsn=dsn,
            broker_table_name=table_name,
        ) from None
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _run_paper_autonomous_investment_ledger_db_history_health_trend_gate(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: (
        PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateRunner | None
    ) = None,
) -> object:
    command_name = "paper-autonomous-investment-ledger-db-history-health-trend-gate"
    if isinstance(limit, bool) or type(limit) is not int or limit < 1:
        raise ValueError(f"{command_name} limit must be positive")
    generated_at = datetime.now(UTC)

    from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health import (
        PaperAutonomousInvestmentLedgerDbHistoryHealthConfig,
    )
    from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_trend import (
        PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig,
    )
    from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_trend_gate import (
        PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig,
    )

    health_config = PaperAutonomousInvestmentLedgerDbHistoryHealthConfig()
    trend_config = PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig()
    gate_config = PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig()
    if runner is not None:
        try:
            return runner(
                dsn=dsn,
                table_name=table_name,
                limit=limit,
                health_config=health_config,
                trend_config=trend_config,
                gate_config=gate_config,
                generated_at=generated_at,
            )
        except Exception as exc:
            raise _redacted_paper_autonomous_investment_ledger_error(
                exc,
                broker_dsn=dsn,
                broker_table_name=table_name,
            ) from None

    from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_trend_gate_load import (
        load_paper_autonomous_investment_ledger_db_history_health_trend_gate_report,
    )

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper autonomous investment ledger "
            "DB history health trend gate read adapter; install the postgres extra.",
        ) from exc
    try:
        connection = psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper autonomous investment ledger "
            "DB-history health report database",
        ) from None
    try:
        return load_paper_autonomous_investment_ledger_db_history_health_trend_gate_report(
            connection,
            limit=limit,
            table_name=table_name,
            health_config=health_config,
            trend_config=trend_config,
            gate_config=gate_config,
            generated_at=generated_at,
        )
    except Exception as exc:
        raise _redacted_paper_autonomous_investment_ledger_error(
            exc,
            broker_dsn=dsn,
            broker_table_name=table_name,
        ) from None
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _print_paper_execution_pipeline_summary(pipeline_report: object) -> None:
    """Print summary of paper execution pipeline results."""
    lifecycle = pipeline_report["lifecycle_record"]
    proposal = pipeline_report["proposal_report"]
    broker = pipeline_report["broker_record"]
    investment_ledger = pipeline_report.get("investment_ledger_report")

    print("paper-execution-pipeline:")
    print(f"  proposal_status={proposal.proposal_status}")
    print(f"  proposal_count={proposal.proposal_count}")
    print(f"  broker_execution_status={broker.execution_status}")
    print(f"  broker_execution_notional={broker.execution_notional}")
    print(f"  lifecycle_status={lifecycle.lifecycle_status}")
    print(f"  lifecycle_is_terminal={lifecycle.is_terminal}")
    print(f"  lifecycle_fill_notional={lifecycle.fill_notional}")
    if investment_ledger is not None:
        print(f"  investment_ledger_status={investment_ledger.ledger_status}")
        print(
            "  investment_ledger_next_step="
            f"{investment_ledger.recommended_next_step}",
        )


def _print_paper_execution_pipeline_history_summary(records: object) -> None:
    """Print summary of paper execution pipeline history."""
    if not records:
        print("paper-execution-pipeline-db-history: no records found")
        return

    print(f"paper-execution-pipeline-db-history: {len(records)} records")
    for i, record in enumerate(records[:5]):  # show first 5
        print(f"  [{i+1}] status={record.lifecycle_status} notional={record.fill_notional} terminal={record.is_terminal}")
    if len(records) > 5:
        print(f"  ... and {len(records) - 5} more")


def _print_paper_autonomous_investment_ledger_summary(report: object) -> None:
    print("paper-autonomous-investment-ledger:")
    print(f"  ledger_status={report.ledger_status}")
    print(f"  recommended_next_step={report.recommended_next_step}")
    print(f"  source_record_count={report.source_record_count}")
    print(f"  submitted_count={report.submitted_count}")
    print(f"  held_count={report.held_count}")
    print(f"  blocked_count={report.blocked_count}")
    print(f"  held_zero_notional_count={report.held_zero_notional_count}")
    print(f"  blocked_zero_notional_count={report.blocked_zero_notional_count}")
    print(f"  total_submitted_notional={report.total_submitted_notional}")
    latest_generated_at = report.latest_generated_at
    if latest_generated_at is None:
        print("  latest_generated_at=none")
    else:
        print(f"  latest_generated_at={latest_generated_at.isoformat()}")
    print(f"  latest_age_seconds={report.latest_age_seconds}")
    reason_code_counts = " ".join(
        f"{row.reason_code}={row.source_record_count}"
        for row in report.reason_code_counts
    )
    print(f"reason_code_counts: {reason_code_counts or 'none'}")


def _print_paper_autonomous_investment_ledger_db_history_summary(
    reports: object,
) -> None:
    command_name = "paper-autonomous-investment-ledger-db-history"
    if not reports:
        print(f"{command_name}: no reports found")
        return
    report_tuple = tuple(reports)
    print(f"{command_name}: {len(report_tuple)} reports")
    for index, report in enumerate(report_tuple[:5], start=1):
        print(
            f"  [{index}] generated_at={report.generated_at.isoformat()} "
            f"ledger_status={report.ledger_status} "
            f"source_record_count={report.source_record_count} "
            f"submitted_count={report.submitted_count} "
            f"held_count={report.held_count} "
            f"blocked_count={report.blocked_count} "
            f"total_submitted_notional={report.total_submitted_notional} "
            f"latest_age_seconds={report.latest_age_seconds}",
        )
        reason_code_counts = " ".join(
            f"{row.reason_code}={row.source_record_count}"
            for row in report.reason_code_counts
        )
        print(f"  reason_code_counts: {reason_code_counts or 'none'}")
    if len(report_tuple) > 5:
        print(f"  ... and {len(report_tuple) - 5} more")


def _print_paper_autonomous_investment_ledger_db_history_health_summary(
    report: object,
) -> None:
    command_name = "paper-autonomous-investment-ledger-db-history-health"
    print(
        f"{command_name}: health_status={report.health_status} "
        f"recommended_next_step={report.recommended_next_step} "
        f"ledger_report_count={report.ledger_report_count} "
        f"latest_ledger_status={_none_or_value(report.latest_ledger_status)} "
        "latest_source_record_count="
        f"{_none_or_value(report.latest_source_record_count)} "
        f"latest_submitted_count={_none_or_value(report.latest_submitted_count)} "
        f"latest_held_count={_none_or_value(report.latest_held_count)} "
        f"latest_blocked_count={_none_or_value(report.latest_blocked_count)} "
        "latest_total_submitted_notional="
        f"{_none_or_value(report.latest_total_submitted_notional)} "
        "latest_source_generated_at="
        f"{_iso_or_none(report.latest_source_generated_at)} "
        f"latest_source_age_seconds={_none_or_value(report.latest_source_age_seconds)} "
        f"max_source_age_seconds={_none_or_value(report.max_source_age_seconds)} "
        f"pass_ledger_report_count={report.pass_ledger_report_count} "
        f"watch_ledger_report_count={report.watch_ledger_report_count} "
        f"blocked_ledger_report_count={report.blocked_ledger_report_count} "
        "duplicate_latest_generated_at_count="
        f"{report.duplicate_latest_generated_at_count}",
    )
    reason_code_counts = " ".join(
        f"{row.reason_code}={_reason_code_report_count(row)}"
        for row in report.reason_code_counts
    )
    print(f"reason_code_counts: {reason_code_counts or 'none'}")


def _print_paper_autonomous_investment_ledger_db_history_health_trend_summary(
    report: object,
) -> None:
    latest_reason_code_counts = ",".join(
        f"{reason_code}={count}" for reason_code, count in report.latest_reason_code_counts
    )
    summary_parts = [
        "paper-autonomous-investment-ledger-db-history-health-trend:",
        f"trend_count={report.source_health_report_count}",
        f"latest_health_status={_none_or_value(report.latest_health_status)}",
        "ledger_report_count_delta="
        f"{_none_or_value(report.ledger_report_count_delta)}",
        "pass_ledger_report_count_delta="
        f"{_none_or_value(report.pass_ledger_report_count_delta)}",
        "watch_ledger_report_count_delta="
        f"{_none_or_value(report.watch_ledger_report_count_delta)}",
        "blocked_ledger_report_count_delta="
        f"{_none_or_value(report.blocked_ledger_report_count_delta)}",
        "latest_source_record_count_delta="
        f"{_none_or_value(report.latest_source_record_count_delta)}",
        "latest_submitted_count_delta="
        f"{_none_or_value(report.latest_submitted_count_delta)}",
        f"latest_held_count_delta={_none_or_value(report.latest_held_count_delta)}",
        "latest_blocked_count_delta="
        f"{_none_or_value(report.latest_blocked_count_delta)}",
        "latest_total_submitted_notional_delta="
        f"{_none_or_value(report.latest_total_submitted_notional_delta)}",
        "latest_source_generated_at_delta_seconds="
        f"{_none_or_value(report.latest_source_generated_at_delta_seconds)}",
        "latest_source_age_seconds_delta="
        f"{_none_or_value(report.latest_source_age_seconds_delta)}",
        "max_source_age_seconds_delta="
        f"{_none_or_value(report.max_source_age_seconds_delta)}",
        "duplicate_latest_generated_at_count_delta="
        f"{_none_or_value(report.duplicate_latest_generated_at_count_delta)}",
        f"duplicate_generated_at_count={report.duplicate_generated_at_count}",
        "consecutive_latest_watch_count="
        f"{report.consecutive_latest_watch_count}",
        "consecutive_latest_blocked_count="
        f"{report.consecutive_latest_blocked_count}",
        "latest_reason_code_counts="
        f"{latest_reason_code_counts or 'none'}",
    ]
    print(" ".join(summary_parts))


def _print_paper_autonomous_investment_ledger_db_history_health_trend_gate_summary(
    report: object,
) -> None:
    reason_code_counts = " ".join(
        f"{row.reason_code}={_reason_code_report_count(row)}"
        for row in report.reason_code_counts
    )
    summary_parts = [
        "paper-autonomous-investment-ledger-db-history-health-trend-gate:",
        f"gate_status={report.gate_status}",
        f"recommended_next_step={report.recommended_next_step}",
        f"source_health_report_count={report.source_health_report_count}",
        f"latest_health_status={_none_or_value(report.latest_health_status)}",
        f"latest_source_age_seconds={_none_or_value(report.latest_source_age_seconds)}",
        f"duplicate_generated_at_count={report.duplicate_generated_at_count}",
        "consecutive_latest_watch_count="
        f"{report.consecutive_latest_watch_count}",
        "consecutive_latest_blocked_count="
        f"{report.consecutive_latest_blocked_count}",
        "watch_ledger_report_count_delta="
        f"{_none_or_value(report.watch_ledger_report_count_delta)}",
        "blocked_ledger_report_count_delta="
        f"{_none_or_value(report.blocked_ledger_report_count_delta)}",
        "latest_source_record_count_delta="
        f"{_none_or_value(report.latest_source_record_count_delta)}",
        "latest_submitted_count_delta="
        f"{_none_or_value(report.latest_submitted_count_delta)}",
        f"latest_held_count_delta={_none_or_value(report.latest_held_count_delta)}",
        "latest_blocked_count_delta="
        f"{_none_or_value(report.latest_blocked_count_delta)}",
        "latest_total_submitted_notional_delta="
        f"{_none_or_value(report.latest_total_submitted_notional_delta)}",
        "latest_source_generated_at_delta_seconds="
        f"{_none_or_value(report.latest_source_generated_at_delta_seconds)}",
        "latest_source_age_seconds_delta="
        f"{_none_or_value(report.latest_source_age_seconds_delta)}",
        "max_source_age_seconds_delta="
        f"{_none_or_value(report.max_source_age_seconds_delta)}",
        "duplicate_latest_generated_at_count_delta="
        f"{_none_or_value(report.duplicate_latest_generated_at_count_delta)}",
        f"reason_code_counts={reason_code_counts or 'none'}",
    ]
    print(" ".join(summary_parts))


def _print_paper_autonomous_readiness_digest_summary(report: object) -> None:
    print(
        "paper-autonomous-readiness-digest: "
        f"digest_status={report.digest_status} "
        "recommended_next_review_action="
        f"{report.recommended_next_review_action} "
        f"evidence_count={len(tuple(report.evidence))}",
    )
    evidence_statuses = " ".join(
        f"{row.source_name}={row.status}"
        for row in report.evidence
    )
    print(f"evidence_statuses: {evidence_statuses or 'none'}")
    reason_code_counts = " ".join(
        f"{_safe_reason_code_for_cli(row.reason_code)}:"
        f"{_reason_code_report_count(row)}"
        for row in report.reason_code_counts
    )
    print(f"reason_code_counts: {reason_code_counts or 'none'}")


def _print_paper_autonomous_screening_decision_support_gate_summary(
    report: object,
) -> None:
    summary_parts = [
        "paper-autonomous-screening-decision-support-gate:",
        f"gate_status={report.gate_status}",
        f"recommended_next_step={report.recommended_next_step}",
    ]
    if hasattr(report, "queue_source_report_count"):
        summary_parts.append(
            f"source_report_count={report.queue_source_report_count}",
        )
    elif hasattr(report, "source_report_count"):
        summary_parts.append(f"source_report_count={report.source_report_count}")
    if hasattr(report, "operator_flow_gate_status"):
        summary_parts.append(
            f"operator_flow_gate_status={report.operator_flow_gate_status}",
        )
    if hasattr(report, "queue_risk_status"):
        summary_parts.append(f"queue_risk_status={report.queue_risk_status}")
    if hasattr(report, "queue_research_ready_count"):
        summary_parts.append(
            f"queue_research_ready_count={report.queue_research_ready_count}",
        )
    summary_parts.append(f"trend_present={_autonomous_gate_trend_present(report)}")
    summary_parts.append(
        f"rank_stability_present={_autonomous_gate_rank_present(report)}",
    )
    print(
        " ".join(summary_parts),
    )
    gate_signal_counts = _format_autonomous_screening_gate_signal_counts(report)
    print(f"gate_signal_counts: {gate_signal_counts or 'none'}")
    reason_code_counts = " ".join(
        f"{row.reason_code}={row.report_count}"
        for row in report.reason_code_counts
    )
    print(f"reason_code_counts: {reason_code_counts or 'none'}")


def _print_paper_autonomous_allocation_proposal_summary(
    report: object,
    *,
    command_name: str = "paper-autonomous-allocation-proposal",
) -> None:
    allocation_report = getattr(report, "allocation_report", None)
    summary_parts = [
        f"{command_name}:",
        f"proposal_status={getattr(report, 'proposal_status')}",
        f"recommended_next_step={getattr(report, 'recommended_next_step')}",
    ]
    for field_name in (
        "source_queue_count",
        "screening_gate_status",
        "queue_risk_status",
    ):
        if hasattr(report, field_name):
            summary_parts.append(f"{field_name}={getattr(report, field_name)}")
    if allocation_report is not None:
        for field_name in (
            "input_count",
            "row_count",
            "allocated_count",
            "capped_count",
            "no_budget_count",
            "non_recommend_count",
            "skipped_count",
            "total_allocated_paper_notional",
            "remaining_paper_budget",
        ):
            if hasattr(allocation_report, field_name):
                summary_parts.append(
                    f"{field_name}={getattr(allocation_report, field_name)}",
                )
    print(" ".join(summary_parts))
    reason_code_counts = " ".join(
        f"{row.reason_code}={_reason_code_report_count(row)}"
        for row in getattr(report, "reason_code_counts", ())
    )
    print(f"reason_code_counts: {reason_code_counts or 'none'}")


def _reason_code_report_count(row: object) -> object:
    if hasattr(row, "report_count"):
        return getattr(row, "report_count")
    return getattr(row, "count")


def _format_autonomous_screening_gate_signal_counts(report: object) -> str:
    if hasattr(report, "gate_signal_counts"):
        return " ".join(
            f"{row.gate_signal}={row.report_count}"
            for row in report.gate_signal_counts
        )
    counts: Counter[str] = Counter()
    for status in (
        getattr(report, "operator_flow_gate_status", None),
        getattr(report, "queue_risk_status", None),
        getattr(report, "trend_latest_risk_status", None),
    ):
        if status is not None:
            counts[str(status)] += 1
    rank_status = getattr(report, "rank_stability_status", None)
    if rank_status is not None:
        counts["pass" if rank_status == "stable" else str(rank_status)] += 1
    return " ".join(
        f"{status}={counts[status]}"
        for status in ("pass", "watch", "blocked")
        if counts[status] > 0
    )


def _autonomous_gate_trend_present(report: object) -> bool:
    return any(
        getattr(report, field_name, None) is not None
        for field_name in (
            "trend_source_snapshot_count",
            "trend_latest_risk_status",
            "trend_consecutive_latest_watch_count",
            "trend_consecutive_latest_blocked_count",
            "trend_duplicate_generated_at_count",
        )
    )


def _autonomous_gate_rank_present(report: object) -> bool:
    return any(
        getattr(report, field_name, None) is not None
        for field_name in (
            "rank_stability_status",
            "rank_stable_ready_count",
            "rank_unstable_ready_count",
            "rank_blocked_count",
        )
    )


def _print_paper_research_packet_db_history_summary(report: object) -> None:
    print(
        "paper-research-packet-db-history: "
        f"report_count={report.report_count} "
        "first_report_generated_at="
        f"{_iso_or_none(report.first_report_generated_at)} "
        "latest_report_generated_at="
        f"{_iso_or_none(report.latest_report_generated_at)} "
        f"duplicate_generated_at_count={report.duplicate_generated_at_count} "
        f"latest_packet_config_version={_none_or_value(report.latest_packet_config_version)} "
        f"latest_input_row_count={_none_or_value(report.latest_input_row_count)} "
        f"latest_packet_row_count={_none_or_value(report.latest_packet_row_count)} "
        f"latest_included_count={_none_or_value(report.latest_included_count)} "
        f"latest_skipped_count={_none_or_value(report.latest_skipped_count)} "
        f"latest_high_priority_count={_none_or_value(report.latest_high_priority_count)} "
        f"latest_medium_priority_count={_none_or_value(report.latest_medium_priority_count)} "
        f"latest_low_priority_count={_none_or_value(report.latest_low_priority_count)}",
    )
    if report.latest_top_packet_rank is None:
        print("top_packet: none")
        return
    reason_codes = ",".join(report.latest_top_packet_reason_codes or ())
    print(
        "top_packet: "
        f"rank={report.latest_top_packet_rank} "
        f"market_slug={report.latest_top_packet_market_slug} "
        f"side={report.latest_top_packet_side} "
        f"research_priority={report.latest_top_packet_research_priority} "
        f"recommendation_score={report.latest_top_packet_recommendation_score} "
        f"net_edge={report.latest_top_packet_net_edge} "
        f"allocated_notional={_none_or_value(report.latest_top_packet_allocated_notional)} "
        f"requested_notional={_none_or_value(report.latest_top_packet_requested_notional)} "
        f"reason_codes={reason_codes or 'none'}",
    )


def _iso_or_none(value: datetime | None) -> str:
    return "none" if value is None else value.isoformat()


def _csv_or_none(values: tuple[str, ...]) -> str:
    return "none" if not values else ",".join(values)


def _none_or_value(value: object | None) -> str:
    return "none" if value is None else str(value)


def _format_history_status_row_counts(rows: tuple[object, ...]) -> str:
    return ",".join(
        f"{row.status}:{row.report_count}"
        for row in rows
    )


def _format_quality_history_status_row_counts(rows: tuple[object, ...]) -> str:
    return " ".join(
        f"{row.quality_status}={row.status_count}"
        for row in rows
    )


def _operator_flow_history_status_counts(rows: tuple[object, ...]) -> dict[str, int]:
    counts = {"pass": 0, "watch": 0, "blocked": 0}
    for row in rows:
        flow_status = row.flow_status
        if flow_status in counts:
            counts[flow_status] = row.status_count
    return counts


def _format_operator_flow_history_status_row_counts(rows: tuple[object, ...]) -> str:
    counts = _operator_flow_history_status_counts(rows)
    return " ".join(
        f"{flow_status}={counts[flow_status]}"
        for flow_status in ("pass", "watch", "blocked")
    )


def _allocation_proposal_history_status_counts(rows: tuple[object, ...]) -> dict[str, int]:
    counts = {"pass": 0, "watch": 0, "blocked": 0}
    for row in rows:
        proposal_status = row.proposal_status
        if proposal_status in counts:
            counts[proposal_status] = row.status_count
    return counts


def _format_allocation_proposal_history_status_row_counts(rows: tuple[object, ...]) -> str:
    counts = _allocation_proposal_history_status_counts(rows)
    return " ".join(
        f"{proposal_status}={counts[proposal_status]}"
        for proposal_status in ("pass", "watch", "blocked")
    )


def _format_outcome_freshness_status_row_counts(rows: tuple[object, ...]) -> str:
    return ",".join(
        f"{row.status}:{row.outcome_report_count}"
        for row in rows
    )


def _format_cost_trend_status_row_counts(rows: tuple[object, ...]) -> str:
    return ",".join(
        f"{row.status}:{row.status_count}"
        for row in rows
    )


def _print_run_loop_summary(summary: RunLoopSummary) -> None:
    cycle_reports_text = ""
    if hasattr(summary, "cycle_reports_persisted"):
        cycle_reports_text = (
            f" cycle_reports_persisted={summary.cycle_reports_persisted}"
        )
    cycle_snapshots_text = ""
    if hasattr(summary, "cycle_snapshots_persisted"):
        cycle_snapshots_text = (
            f" cycle_snapshots_persisted={summary.cycle_snapshots_persisted}"
        )
    action_gated_queues_text = ""
    if hasattr(summary, "action_gated_queues_persisted"):
        action_gated_queues_text = (
            f" action_gated_queues_persisted="
            f"{summary.action_gated_queues_persisted}"
        )
    print(
        "run: "
        f"completed={summary.iterations_completed} "
        f"failed={summary.iterations_failed} "
        f"nav_skipped={summary.nav_marks_skipped}"
        f"{cycle_reports_text}"
        f"{cycle_snapshots_text}"
        f"{action_gated_queues_text} "
        f"span={summary.first_iteration_at.isoformat()} "
        f"to {summary.last_iteration_at.isoformat()}",
    )
    if summary.last_error is not None:
        print(f"  last_error={summary.last_error}")


def _print_outcome_tracking_summary(report: OutcomeTrackingReport) -> None:
    """Print a human-readable outcome-tracking summary to stdout."""

    print(
        "check-outcomes: "
        f"checked={report.total_markets_checked} "
        f"resolved={report.resolved_count} "
        f"pending={report.pending_count} "
        f"observations={len(report.observations)}",
    )
    evidence = report.forecast_evidence_report
    if evidence is None:
        print("  forecast_evidence: none (no resolved observations yet)")
        return
    print(
        "  forecast_evidence: "
        f"status={evidence.status} "
        f"observation_count={evidence.observation_count} "
        f"unique_markets={evidence.unique_market_count}",
    )
    if evidence.mean_probability_loss is not None:
        print(f"  mean_probability_loss={evidence.mean_probability_loss}")
    if evidence.worst_bucket_error is not None:
        print(f"  worst_bucket_error={evidence.worst_bucket_error}")


if __name__ == "__main__":  # pragma: no cover - thin entry shim
    import sys as _sys

    _sys.exit(main())
