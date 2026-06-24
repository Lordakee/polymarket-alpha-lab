import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROPOSAL_REVIEW_DOSSIER_PATH = (
    REPO_ROOT / "src" / "polymarket_alpha_lab" / "proposal_review_dossier.py"
)
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"
README_PATH = REPO_ROOT / "README.md"


EXPECTED_PROPOSAL_REVIEW_DOSSIER_EXPORTS = {
    "TradeProposalReviewDossierConfig",
    "TradeProposalReviewDossierFindingRow",
    "TradeProposalReviewDossierGateResult",
    "TradeProposalReviewDossierLog",
    "TradeProposalReviewDossierReport",
    "TradeProposalReviewDossierSourceRow",
    "build_trade_proposal_review_dossier_report",
}
EXPECTED_PROPOSAL_REVIEW_DOSSIER_BATCH_EXPORTS = {
    "TradeProposalReviewDossierBatchConfig",
    "TradeProposalReviewDossierBatchGateResult",
    "TradeProposalReviewDossierBatchConfigVersionSummary",
    "TradeProposalReviewDossierBatchDuplicateSummary",
    "TradeProposalReviewDossierBatchFindingSummary",
    "TradeProposalReviewDossierBatchSourceSummary",
    "TradeProposalReviewDossierBatchReport",
    "TradeProposalReviewDossierBatchLog",
    "build_trade_proposal_review_dossier_batch_report",
}
EXPECTED_LEVEL_2_PROPOSAL_PACKET_EXPORTS = {
    "TradeProposalPacket",
    "TradeProposalPacketConfig",
    "TradeProposalPacketLog",
    "build_trade_proposal_packet",
}
EXPECTED_PROPOSAL_REVIEW_EXPORTS = {
    "TradeProposalReviewConfig",
    "TradeProposalReviewRecord",
    "TradeProposalReviewLog",
    "build_trade_proposal_review_record",
}
EXPECTED_PROPOSAL_REVIEW_SUMMARY_EXPORTS = {
    "TradeProposalReviewBucketSummary",
    "TradeProposalReviewReasonCodeSummary",
    "TradeProposalReviewSummaryConfig",
    "TradeProposalReviewSummaryLog",
    "TradeProposalReviewSummaryReport",
    "build_trade_proposal_review_summary_report",
}
EXPECTED_PROPOSAL_REVIEW_QUALITY_EXPORTS = {
    "TradeProposalReviewQualityConfig",
    "TradeProposalReviewQualityGateResult",
    "TradeProposalReviewQualityLog",
    "TradeProposalReviewQualityReasonTrend",
    "TradeProposalReviewQualityReport",
    "build_trade_proposal_review_quality_report",
}
EXPECTED_PROPOSAL_REVIEW_DIAGNOSTIC_EXPORTS = {
    "TradeProposalReviewDiagnosticBucketRow",
    "TradeProposalReviewDiagnosticConfig",
    "TradeProposalReviewDiagnosticLog",
    "TradeProposalReviewDiagnosticReasonRow",
    "TradeProposalReviewDiagnosticReport",
    "TradeProposalReviewDiagnosticSourceRow",
    "build_trade_proposal_review_diagnostic_report",
}
EXPECTED_PROPOSAL_REVIEW_COVERAGE_EXPORTS = {
    "TradeProposalReviewCoverageBucketRow",
    "TradeProposalReviewCoverageConfig",
    "TradeProposalReviewCoverageGateResult",
    "TradeProposalReviewCoverageLog",
    "TradeProposalReviewCoveragePacketRow",
    "TradeProposalReviewCoverageReport",
    "build_trade_proposal_review_coverage_report",
}
EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_EXPORTS = {
    "TradeProposalEvidenceComparisonConfig",
    "TradeProposalEvidenceComparisonGateResult",
    "TradeProposalEvidenceComparisonSourceRow",
    "TradeProposalEvidenceComparisonMetricRow",
    "TradeProposalEvidenceComparisonFindingRow",
    "TradeProposalEvidenceComparisonReport",
    "TradeProposalEvidenceComparisonLog",
    "build_trade_proposal_evidence_comparison_report",
}
EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_ARTIFACT_REGISTRY_EXPORTS = {
    "PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS",
    "ProposalEvidenceComparisonArtifactDefinition",
    "get_proposal_evidence_comparison_artifact",
    "list_proposal_evidence_comparison_artifacts",
}
EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_EXPORTS = {
    "TradeProposalEvidenceComparisonHistoryConfig",
    "TradeProposalEvidenceComparisonHistoryGateResult",
    "TradeProposalEvidenceComparisonHistoryStatusRow",
    "TradeProposalEvidenceComparisonHistoryFindingSummary",
    "TradeProposalEvidenceComparisonHistoryConfigVersionSummary",
    "TradeProposalEvidenceComparisonHistorySourceTransition",
    "TradeProposalEvidenceComparisonHistoryReport",
    "TradeProposalEvidenceComparisonHistoryLog",
    "build_trade_proposal_evidence_comparison_history_report",
}
EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_EXPORTS = {
    "TradeProposalEvidenceComparisonHistoryBatchHealthConfig",
    "TradeProposalEvidenceComparisonHistoryBatchHealthGateResult",
    "TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow",
    "TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthReport",
    "TradeProposalEvidenceComparisonHistoryBatchHealthLog",
    "build_trade_proposal_evidence_comparison_history_batch_health_report",
}
EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_EXPORTS = {
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog",
    "build_trade_proposal_evidence_comparison_history_batch_health_trend_report",
}
EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_EXPORTS = {
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfig",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfigVersionSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateFingerprintSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchLog",
    "build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report",
}
EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_EXPORTS = {
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog",
    "build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report",
}
EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_TREND_EXPORTS = {
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateResult",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendStatusRow",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfigVersionSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateStatusSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateGeneratedAtSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateFingerprintSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendReport",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog",
    "build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report",
}
EXPECTED_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_EXPORTS = {
    "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_CONFIG_VERSION",
    "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_CONFIG_VERSION",
    "PaperAutonomousAllocationProposalConfig",
    "PaperAutonomousAllocationProposalDbHistoryConfig",
    "PaperAutonomousAllocationProposalDbHistoryGateConfig",
    "PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount",
    "PaperAutonomousAllocationProposalDbHistoryGateReport",
    "PaperAutonomousAllocationProposalDbHistoryHealthConfig",
    "PaperAutonomousAllocationProposalDbHistoryHealthReasonCodeCount",
    "PaperAutonomousAllocationProposalDbHistoryHealthReport",
    "PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig",
    "PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow",
    "PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary",
    "PaperAutonomousAllocationProposalDbHistoryHealthTrendReport",
    "PaperAutonomousAllocationProposalDbHistoryReasonCodeRow",
    "PaperAutonomousAllocationProposalDbHistoryReport",
    "PaperAutonomousAllocationProposalDbHistoryStatusRow",
    "PaperAutonomousAllocationProposalReasonCodeCount",
    "PaperAutonomousAllocationProposalReport",
    "PaperAutonomousAllocationProposalSourceQueueSummary",
    "build_paper_autonomous_allocation_proposal_report",
    "build_paper_autonomous_allocation_proposal_db_history_gate_report",
    "build_paper_autonomous_allocation_proposal_db_history_health_report",
    "build_paper_autonomous_allocation_proposal_db_history_health_trend_report",
    "build_paper_autonomous_allocation_proposal_db_history_report",
}
EXPECTED_LEVEL_2_ARTIFACT_EXPORTS = (
    EXPECTED_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_EXPORTS
    | EXPECTED_LEVEL_2_PROPOSAL_PACKET_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_SUMMARY_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_QUALITY_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_DIAGNOSTIC_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_COVERAGE_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_DOSSIER_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_DOSSIER_BATCH_EXPORTS
    | EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_EXPORTS
    | EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_ARTIFACT_REGISTRY_EXPORTS
    | EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_EXPORTS
    | EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_EXPORTS
    | EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_EXPORTS
    | EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_EXPORTS
    | EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_EXPORTS
    | EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_TREND_EXPORTS
)

ALLOWED_IMPORT_PREFIXES = {
    "__future__",
    "json",
    "collections.abc",
    "dataclasses",
    "datetime",
    "decimal",
    "pathlib",
    "typing",
    "polymarket_alpha_lab.proposal_review_summary",
    "polymarket_alpha_lab.proposal_review_quality",
    "polymarket_alpha_lab.proposal_review_diagnostics",
    "polymarket_alpha_lab.proposal_review_coverage",
}

EXPECTED_FIRST_PARTY_IMPORTS = {
    "polymarket_alpha_lab.proposal_review_summary": {
        "TradeProposalReviewBucketSummary",
        "TradeProposalReviewReasonCodeSummary",
        "TradeProposalReviewSummaryReport",
    },
    "polymarket_alpha_lab.proposal_review_quality": {
        "TradeProposalReviewQualityGateResult",
        "TradeProposalReviewQualityReasonTrend",
        "TradeProposalReviewQualityReport",
    },
    "polymarket_alpha_lab.proposal_review_diagnostics": {
        "TradeProposalReviewDiagnosticBucketRow",
        "TradeProposalReviewDiagnosticReasonRow",
        "TradeProposalReviewDiagnosticReport",
        "TradeProposalReviewDiagnosticSourceRow",
    },
    "polymarket_alpha_lab.proposal_review_coverage": {
        "TradeProposalReviewCoverageBucketRow",
        "TradeProposalReviewCoverageGateResult",
        "TradeProposalReviewCoveragePacketRow",
        "TradeProposalReviewCoverageReport",
    },
}

FORBIDDEN_IMPORT_PREFIXES = {
    "polymarket_alpha_lab.analytics",
    "polymarket_alpha_lab.analytics_history",
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.archive",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.domain",
    "polymarket_alpha_lab.forecast_evidence",
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.manual_review_queue",
    "polymarket_alpha_lab.normalize",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.pipeline",
    "polymarket_alpha_lab.positions",
    "polymarket_alpha_lab.proposal_packet",
    "polymarket_alpha_lab.proposal_review",
    "polymarket_alpha_lab.rejections",
    "polymarket_alpha_lab.research",
    "polymarket_alpha_lab.risk",
    "polymarket_alpha_lab.scoring",
    "urllib",
    "urllib3",
    "http",
    "socket",
    "ssl",
    "websocket",
    "websockets",
    "requests",
    "httpx",
    "aiohttp",
    "importlib",
    "runpy",
    "subprocess",
    "py_clob_client",
    "clob_client",
    "web3",
    "eth_account",
    "eth_keys",
    "eth_utils",
    "selenium",
    "playwright",
    "bs4",
    "scrapy",
    "requests_html",
    "mechanize",
    "cloudscraper",
    "curl_cffi",
    "csv",
    "sqlite3",
    "pandas",
    "polars",
    "duckdb",
    "os",
}

FORBIDDEN_NAME_FRAGMENTS = {
    "accountaction",
    "accountauthentication",
    "accountclient",
    "apikey",
    "apitoken",
    "authtoken",
    "approvalat",
    "approvalby",
    "approvalgate",
    "approvalready",
    "approvalworkflow",
    "approvedat",
    "approvedby",
    "approvedpacketselector",
    "authenticationclient",
    "brokerclient",
    "brokerrequest",
    "brokersession",
    "browserautomation",
    "browsersession",
    "clientsession",
    "cloudscraper",
    "compliancecheck",
    "compliancereview",
    "cancelorder",
    "createorder",
    "credentials",
    "credentialloader",
    "credentialmanager",
    "crawler",
    "credentialpath",
    "credentialprovider",
    "credentialstore",
    "credentialworkflow",
    "downloadhistory",
    "externalhistory",
    "executionclient",
    "executionengine",
    "executionreadiness",
    "fetchmarket",
    "fetchorderbook",
    "fetchpricehistory",
    "fetchsummaryreport",
    "historicalloader",
    "httpclient",
    "geographicaccessanalysis",
    "geographicanalysis",
    "geoanalysis",
    "goliveready",
    "heartbeat",
    "identitydata",
    "investmentranking",
    "jurisdictioncheck",
    "latestdecisionselector",
    "legalreview",
    "liveexecution",
    "liveexecutionsignal",
    "loadjsonl",
    "marketclient",
    "manualexecutionimport",
    "orderclient",
    "orderinstruction",
    "orderplacement",
    "orderpayload",
    "orderrequest",
    "password",
    "placeorder",
    "playwrightbrowser",
    "privatekey",
    "privatekeypath",
    "profitable",
    "profitablestatus",
    "promotionready",
    "promotablestatus",
    "rankinvestments",
    "readjsonl",
    "readjsonlhistory",
    "readyforlivetrading",
    "recommendtrade",
    "reconcileexchangeaccounts",
    "reconciliationprocess",
    "reconciliationstatus",
    "requestsession",
    "requestpayload",
    "scrape",
    "scrapehtml",
    "scrapewebsites",
    "scrapingevidenceloader",
    "secret",
    "sendorder",
    "seleniumdriver",
    "settlementreview",
    "signorder",
    "strategypromotion",
    "strategypromotionsignal",
    "submitorder",
    "tradeinstruction",
    "tradingclient",
    "traderecommendation",
    "tradingsdk",
    "transportclient",
    "walletsignature",
    "websocketclient",
    "websocketsession",
    "winningdecision",
}

FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS = {
    "account",
    "api",
    "approval",
    "authentication",
    "broker",
    "browser",
    "client",
    "compliance",
    "crawler",
    "credential",
    "execution",
    "geo",
    "jurisdiction",
    "legal",
    "privatekey",
    "profit",
    "promotion",
    "ranking",
    "recommendation",
    "reconciliation",
    "scraping",
    "settlement",
    "wallet",
    "websocket",
}


def parse_proposal_review_dossier():
    return ast.parse(PROPOSAL_REVIEW_DOSSIER_PATH.read_text(encoding="utf-8"))


def normalize_identifier(value):
    return "".join(character for character in value.lower() if character.isalnum())


def forbidden_fragment_matches(example):
    normalized = normalize_identifier(example)
    return any(
        normalize_identifier(fragment) in normalized
        for fragment in FORBIDDEN_NAME_FRAGMENTS
    )


def public_export_fragment_matches(example):
    normalized = normalize_identifier(example)
    return any(
        normalize_identifier(fragment) in normalized
        for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS
    )


def module_matches_prefix(module_name, prefix):
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def imported_modules(tree):
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
            modules.extend(alias.asname for alias in node.names if alias.asname)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)
            modules.extend(alias.asname for alias in node.names if alias.asname)
    return modules


def imported_first_party_symbols(tree):
    symbols = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in EXPECTED_FIRST_PARTY_IMPORTS:
            symbols.setdefault(node.module, set()).update(
                alias.name for alias in node.names
            )
    return symbols


def module_exports(tree):
    assigned_exports = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    assigned_exports = ast.literal_eval(node.value)
    assert assigned_exports is not None
    return tuple(assigned_exports)


def test_forbidden_name_fragments_cover_level_2_node_7_scope_variants():
    examples = (
        "account_action",
        "account_authentication",
        "credential_path",
        "private_key_path",
        "api_token",
        "auth_token",
        "secret",
        "password",
        "credential_loader",
        "credential_manager",
        "client_session",
        "order_client",
        "order_payload",
        "place_order",
        "submit_order",
        "create_order",
        "cancel_order",
        "send_order",
        "sign_order",
        "execution_client",
        "execution_engine",
        "websocket_session",
        "broker_session",
        "request_session",
        "request_payload",
        "http_client",
        "market_client",
        "trading_client",
        "browser_session",
        "browser_automation",
        "playwright_browser",
        "selenium_driver",
        "crawler",
        "credentials",
        "heartbeat",
        "scraping_evidence_loader",
        "scrape_websites",
        "fetch_summary_report",
        "fetch_market",
        "fetch_orderbook",
        "fetch_price_history",
        "read_jsonl",
        "load_jsonl",
        "read_jsonl_history",
        "external_history_loader",
        "historical_loader",
        "download_history",
        "scrape_html",
        "scrape",
        "approval_ready",
        "approval_gate",
        "approval_workflow",
        "approved_packet_selector",
        "latest_decision_selector",
        "winning_decision",
        "promotion_ready",
        "promotable_status",
        "profitable_status",
        "execution_readiness",
        "go_live_ready",
        "ready_for_live_trading",
        "trade_recommendation",
        "recommend_trade",
        "investment_ranking",
        "rank_investments",
        "settlement_review",
        "reconcile_exchange_accounts",
        "reconciliation_status",
        "manual_execution_import",
        "trading_sdk",
        "compliance_review",
        "legal_review",
        "jurisdiction_check",
        "geo_analysis",
        "geographic_access_analysis",
    )

    for example in examples:
        assert forbidden_fragment_matches(example), example


def test_forbidden_name_fragments_allow_required_dossier_audit_identifiers():
    for allowed in (
        "approved_decision_count",
        "rejected_decision_count",
        "proposal_review_dossier_complete",
    ):
        assert not forbidden_fragment_matches(allowed)


def test_proposal_review_dossier_module_imports_only_allowed_dependencies():
    tree = parse_proposal_review_dossier()
    for module_name in imported_modules(tree):
        assert any(
            module_matches_prefix(module_name, allowed)
            for allowed in ALLOWED_IMPORT_PREFIXES
        ), module_name


def test_proposal_review_dossier_module_does_not_import_forbidden_surfaces():
    tree = parse_proposal_review_dossier()
    for module_name in imported_modules(tree):
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_proposal_review_dossier_module_uses_only_allowed_first_party_symbols():
    tree = parse_proposal_review_dossier()
    assert imported_first_party_symbols(tree) == EXPECTED_FIRST_PARTY_IMPORTS


def test_proposal_review_dossier_module_does_not_import_first_party_modules_wholesale():
    tree = parse_proposal_review_dossier()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Import):
            continue
        for alias in node.names:
            assert alias.name not in EXPECTED_FIRST_PARTY_IMPORTS, alias.name


def test_proposal_review_dossier_module_does_not_define_forbidden_live_or_workflow_names():
    tree = parse_proposal_review_dossier()
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg is not None:
            names.add(node.arg)
        elif isinstance(node, ast.alias):
            names.add(node.name)
            if node.asname is not None:
                names.add(node.asname)

    lowered = {normalize_identifier(name) for name in names}
    for fragment in FORBIDDEN_NAME_FRAGMENTS:
        assert not any(normalize_identifier(fragment) in name for name in lowered), (
            fragment,
            lowered,
        )


def test_trade_proposal_review_dossier_public_exports_are_report_only():
    tree = parse_proposal_review_dossier()
    assigned_exports = module_exports(tree)
    assert set(assigned_exports) == EXPECTED_PROPOSAL_REVIEW_DOSSIER_EXPORTS
    for name in assigned_exports:
        assert name.startswith("TradeProposalReviewDossier") or name == (
            "build_trade_proposal_review_dossier_report"
        )
        assert not public_export_fragment_matches(name), name

    for export_name in EXPECTED_PROPOSAL_REVIEW_DOSSIER_EXPORTS:
        assert not public_export_fragment_matches(export_name), export_name


def test_package_root_exports_do_not_leak_forbidden_level_2_node_7_surfaces():
    tree = ast.parse(PACKAGE_ROOT_PATH.read_text(encoding="utf-8"))
    assigned_exports = module_exports(tree)
    for name in assigned_exports:
        normalized_name = normalize_identifier(name)
        if normalized_name in {
            "paperexecutionconfig",
            "paperexecutionresult",
            "paperexecutionlog",
            "executepapertradefromscreening",
        }:
            # Legitimate paper-execution public API (validated by
            # test_paper_execution_scope); not a forbidden-surface leak.
            continue
        if any(
            fragment in normalized_name for fragment in ("proposal", "tradeproposal")
        ):
            assert name in EXPECTED_LEVEL_2_ARTIFACT_EXPORTS
            continue
        assert not any(
            fragment in normalized_name
            for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS
        )


def test_readme_level_2_node_7_section_keeps_report_only_boundaries():
    readme = README_PATH.read_text(encoding="utf-8")
    start = readme.index("## Level 2 Node 7 Status")
    end = readme.index("## Level 2 Node 8 Status", start)
    normalized = normalize_identifier(readme[start:end])
    required_fragments = (
        "level2node7status",
        "level2node7pythonapi",
        "reportonlyproposalreviewdossierartifacts",
        "notanapprovalworkflowtradeinstructionorderinstructionbrokerrequestorderrequestaccountaction",
        "strategypromotionsignal",
        "liveexecutionsignal",
        "credentials",
        "scrapewebsites",
        "tradingsdk",
        "brokerclient",
        "executionclient",
        "settlement",
        "reconciliation",
        "approvalworkflows",
        "rankinvestments",
        "recommendtrades",
        "compliancelegalgeographicanalysis",
    )

    for fragment in required_fragments:
        assert fragment in normalized, fragment


def test_readme_repository_layout_lists_level_2_node_7_artifacts():
    readme = README_PATH.read_text(encoding="utf-8")
    for expected_path in (
        "2026-06-15-level-2-proposal-review-dossier.md",
        "proposal_review_dossier.py",
        "test_proposal_review_dossier.py",
        "test_proposal_review_dossier_scope.py",
    ):
        assert expected_path in readme
