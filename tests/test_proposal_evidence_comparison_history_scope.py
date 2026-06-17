import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROPOSAL_EVIDENCE_COMPARISON_HISTORY_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "proposal_evidence_comparison_history.py"
)
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"
README_PATH = REPO_ROOT / "README.md"


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
EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_ARTIFACT_REGISTRY_EXPORTS = {
    "PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS",
    "ProposalEvidenceComparisonArtifactDefinition",
    "get_proposal_evidence_comparison_artifact",
    "list_proposal_evidence_comparison_artifacts",
}
EXPECTED_LEVEL_2_ARTIFACT_EXPORTS = (
    EXPECTED_LEVEL_2_PROPOSAL_PACKET_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_SUMMARY_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_QUALITY_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_DIAGNOSTIC_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_COVERAGE_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_DOSSIER_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_DOSSIER_BATCH_EXPORTS
    | EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_EXPORTS
    | EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_EXPORTS
    | EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_EXPORTS
    | EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_EXPORTS
    | EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_EXPORTS
    | EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_EXPORTS
    | EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_TREND_EXPORTS
    | EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_ARTIFACT_REGISTRY_EXPORTS
)
EXPECTED_NON_LEVEL_2_PACKAGE_ROOT_EXPORTS_WITH_NODE_10_TERMS = {
    "MarketScore",
    "MarketSnapshot",
    "NormalizedMarket",
    "PaperCostAwareEventMarketSnapshot",
    "build_paper_cost_aware_event_market_snapshot",
    "polymarket_default_cost_assumptions",
    "PaperExecutionConfig",
    "PaperExecutionResult",
    "PaperExecutionLog",
    "execute_paper_trade_from_screening",
    "OrderBookLevel",
    "OrderBookSnapshot",
    "OutcomeToken",
    "PaperOrder",
    "PaperTradeJournal",
    "PaperTradeRecord",
    "simulate_order_book_fill",
    "OutcomeTrackingConfig",
    "OutcomeTrackingLog",
    "OutcomeTrackingReport",
    "check_outcomes",
    "polymarket_default_cost_assumptions",
}

ALLOWED_IMPORT_PREFIXES = {
    "__future__",
    "collections.abc",
    "json",
    "dataclasses",
    "datetime",
    "decimal",
    "pathlib",
    "typing",
    "polymarket_alpha_lab.proposal_evidence_comparison",
}

EXPECTED_FIRST_PARTY_IMPORTS = {
    "polymarket_alpha_lab.proposal_evidence_comparison": {
        "TradeProposalEvidenceComparisonFindingRow",
        "TradeProposalEvidenceComparisonGateResult",
        "TradeProposalEvidenceComparisonMetricRow",
        "TradeProposalEvidenceComparisonReport",
        "TradeProposalEvidenceComparisonSourceRow",
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
    "polymarket_alpha_lab.proposal_review_coverage",
    "polymarket_alpha_lab.proposal_review_diagnostics",
    "polymarket_alpha_lab.proposal_review_dossier",
    "polymarket_alpha_lab.proposal_review_dossier_batch",
    "polymarket_alpha_lab.proposal_review_quality",
    "polymarket_alpha_lab.proposal_review_summary",
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
    "approvedproposalselector",
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
    "conflictreviewer",
    "conflictresolver",
    "credentialloader",
    "credentialmanager",
    "credentialpath",
    "credentialprovider",
    "credentialstore",
    "credentialworkflow",
    "credentials",
    "crawler",
    "decisionresolution",
    "decisionresolver",
    "downloadhistory",
    "executionclient",
    "executionengine",
    "executionreadiness",
    "externalhistoryloader",
    "fetchmarket",
    "fetchorderbook",
    "fetchpricehistory",
    "fetchsummaryreport",
    "fromfile",
    "fromlog",
    "geographicaccessanalysis",
    "geographicanalysis",
    "geoanalysis",
    "globjsonl",
    "goliveready",
    "heartbeat",
    "historyloader",
    "historicalloader",
    "httpclient",
    "identitydata",
    "investmentranking",
    "jsonlloader",
    "jsonlreader",
    "jurisdictioncheck",
    "latestdecisionselector",
    "legalreview",
    "liveclient",
    "liveexecution",
    "liveexecutionclient",
    "liveexecutionsignal",
    "liveloader",
    "livemarket",
    "liveorder",
    "liverequest",
    "loadhistory",
    "loadjsonl",
    "manualexecution",
    "manualexecutionimport",
    "marketclient",
    "marketloader",
    "marketpayload",
    "marketreader",
    "marketrequest",
    "marketscore",
    "orderbookclient",
    "orderbookloader",
    "orderbookpayload",
    "orderbookreader",
    "orderbookrequest",
    "orderclient",
    "orderinstruction",
    "orderloader",
    "orderpayload",
    "orderplacement",
    "orderreader",
    "orderrequest",
    "outcomeclient",
    "outcomehistoryloader",
    "outcomeloader",
    "outcomepayload",
    "outcomereader",
    "outcomerequest",
    "paperforecastevidenceobservation",
    "password",
    "privatekey",
    "privatekeypath",
    "profitabilityanalysis",
    "profitable",
    "profitablestatus",
    "promotablestatus",
    "proposalapproval",
    "rankinvestments",
    "rawobservation",
    "rawproposal",
    "rawreview",
    "readjsonl",
    "readjsonlhistory",
    "readyforlivetrading",
    "realizedfalsepositiveanalysis",
    "recommendtrade",
    "reconcileexchangeaccounts",
    "reconciliationprocess",
    "reconciliationstatus",
    "replayjsonl",
    "requestclient",
    "requestloader",
    "requestpayload",
    "requestreader",
    "requestsession",
    "scrape",
    "scrapehtml",
    "scrapewebsites",
    "scrapingevidenceloader",
    "secret",
    "seleniumdriver",
    "settlementreview",
    "strategypromotion",
    "strategypromotionsignal",
    "submitorder",
    "tradeinstruction",
    "tradeproposalpacket",
    "tradeproposalreviewrecord",
    "traderecommendation",
    "tradingclient",
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
    "auth",
    "authentication",
    "broker",
    "browser",
    "client",
    "compliance",
    "crawler",
    "credential",
    "execution",
    "fromfile",
    "geo",
    "geographic",
    "glob",
    "jurisdiction",
    "legal",
    "heartbeat",
    "jsonl",
    "loader",
    "live",
    "liveexecution",
    "manualexecution",
    "manualexecutionimport",
    "market",
    "order",
    "orderbook",
    "outcome",
    "privatekey",
    "profit",
    "profitability",
    "promotion",
    "ranking",
    "reader",
    "recommendation",
    "reconciliation",
    "replay",
    "request",
    "session",
    "scraping",
    "settlement",
    "tradeinstruction",
    "wallet",
    "websocket",
}


def parse_proposal_evidence_comparison_history():
    return ast.parse(
        PROPOSAL_EVIDENCE_COMPARISON_HISTORY_PATH.read_text(encoding="utf-8")
    )


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
            symbols.setdefault(node.module, set()).update(alias.name for alias in node.names)
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


def test_forbidden_name_fragments_cover_level_2_node_10_scope_variants():
    examples = (
        "external_history_loader",
        "historical_loader",
        "history_loader",
        "jsonl_reader",
        "jsonl_loader",
        "read_jsonl_history",
        "load_jsonl",
        "load_history",
        "replay_jsonl",
        "glob_jsonl",
        "from_file",
        "from_log",
        "outcome_loader",
        "outcomeloader",
        "outcome_history_loader",
        "outcome_client",
        "outcome_reader",
        "outcome_request",
        "outcome_payload",
        "realized_false_positive_analysis",
        "realizedfalsepositiveanalysis",
        "profitability_analysis",
        "profitabilityanalysis",
        "paper_forecast_evidence_observation",
        "trade_proposal_packet",
        "trade_proposal_review_record",
        "approval_workflow",
        "proposal_approval",
        "approved_proposal_selector",
        "latest_decision_selector",
        "decision_resolution",
        "investment_ranking",
        "rank_investments",
        "trade_recommendation",
        "recommend_trade",
        "strategy_promotion",
        "settlement_review",
        "reconcile_exchange_accounts",
        "reconciliation_status",
        "manual_execution_import",
        "trading_sdk",
        "broker_request",
        "order_request",
        "order_loader",
        "order_reader",
        "order_book_reader",
        "orderbookreader",
        "order_book_loader",
        "order_book_request",
        "order_book_payload",
        "account_action",
        "live_execution_signal",
        "live_client",
        "live_loader",
        "live_market",
        "live_order",
        "live_request",
        "manual_execution",
        "manual_execution_import",
        "compliance_review",
        "legal_review",
        "jurisdiction_check",
        "geo_analysis",
        "geographic_access_analysis",
        "market_loader",
        "market_request",
        "market_reader",
        "market_payload",
        "request_client",
        "request_loader",
        "request_reader",
        "private_key_path",
        "credentials",
        "websocket_session",
        "heartbeat",
        "scrape_websites",
    )

    for example in examples:
        assert forbidden_fragment_matches(example), example


def test_forbidden_name_fragments_allow_required_history_audit_identifiers():
    for allowed in (
        "TradeProposalEvidenceComparisonHistoryReport",
        "proposal_evidence_comparison_history_ready",
        "comparison_sample",
        "incomplete_comparison_rate",
        "divergent_comparison_rate",
        "unstable_comparison_rate",
        "source_transitions",
        "append",
    ):
        assert not forbidden_fragment_matches(allowed)


def test_forbidden_public_export_fragments_cover_level_2_node_10_public_surfaces():
    examples = (
        "AuthSession",
        "CredentialLoader",
        "FromFileReport",
        "GlobJsonlReader",
        "Order",
        "OrderBook",
        "OrderBookReader",
        "Outcome",
        "Market",
        "Heartbeat",
        "ReplayJsonlHistory",
        "Request",
        "RequestSession",
        "TradeInstruction",
        "LiveExecution",
        "Live",
        "ManualExecution",
        "ManualExecutionImport",
        "ProfitabilityAnalysis",
        "SettlementReview",
        "ComplianceReview",
        "LegalReview",
        "GeographicAnalysis",
    )

    for example in examples:
        assert public_export_fragment_matches(example), example


def test_expected_level_2_public_exports_do_not_hide_forbidden_surfaces():
    for name in EXPECTED_LEVEL_2_ARTIFACT_EXPORTS:
        assert not public_export_fragment_matches(name), name


def test_proposal_evidence_comparison_history_module_imports_only_allowed_dependencies():
    tree = parse_proposal_evidence_comparison_history()
    for module_name in imported_modules(tree):
        assert any(
            module_matches_prefix(module_name, allowed)
            for allowed in ALLOWED_IMPORT_PREFIXES
        ), module_name


def test_proposal_evidence_comparison_history_module_does_not_import_forbidden_surfaces():
    tree = parse_proposal_evidence_comparison_history()
    for module_name in imported_modules(tree):
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_proposal_evidence_comparison_history_uses_only_allowed_first_party_symbols():
    tree = parse_proposal_evidence_comparison_history()
    assert imported_first_party_symbols(tree) == EXPECTED_FIRST_PARTY_IMPORTS


def test_proposal_evidence_comparison_history_does_not_import_first_party_modules_wholesale():
    tree = parse_proposal_evidence_comparison_history()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Import):
            continue
        for alias in node.names:
            assert alias.name not in EXPECTED_FIRST_PARTY_IMPORTS, alias.name


def test_proposal_evidence_comparison_history_does_not_define_forbidden_names():
    tree = parse_proposal_evidence_comparison_history()
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


def test_trade_proposal_evidence_comparison_history_public_exports_are_report_only():
    tree = parse_proposal_evidence_comparison_history()
    assigned_exports = module_exports(tree)
    assert set(assigned_exports) == EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_EXPORTS
    for name in assigned_exports:
        assert name.startswith("TradeProposalEvidenceComparisonHistory") or name == (
            "build_trade_proposal_evidence_comparison_history_report"
        )
        assert not public_export_fragment_matches(name), name

    for export_name in EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_EXPORTS:
        assert not public_export_fragment_matches(export_name), export_name


def test_package_root_exports_do_not_leak_forbidden_level_2_node_10_surfaces():
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
        if name in EXPECTED_NON_LEVEL_2_PACKAGE_ROOT_EXPORTS_WITH_NODE_10_TERMS:
            continue
        if any(
            fragment in normalized_name for fragment in ("proposal", "tradeproposal")
        ):
            assert name in EXPECTED_LEVEL_2_ARTIFACT_EXPORTS
            assert not public_export_fragment_matches(name), name
            continue
        assert not public_export_fragment_matches(name), name


def test_readme_level_2_node_10_section_keeps_report_only_boundaries():
    readme = README_PATH.read_text(encoding="utf-8")
    start = readme.index("## Level 2 Node 10 Status")
    end = readme.index("## Automation Roadmap", start)
    normalized = normalize_identifier(readme[start:end])
    required_fragments = (
        "level2node10status",
        "level2node10pythonapi",
        "reportonlyproposalevidencecomparisonhistorysummaries",
        "supplied",
        "tradeproposalevidencecomparisonreportvalues",
        "divergenceproxy",
        "appendalreadybuiltcomparisonhistorysnapshots",
        "thereisnojsonlreaderloaderreplayorfromfileapi",
        "notanapprovalworkflow",
        "proposalapproval",
        "approvedproposalselector",
        "latestdecisionselector",
        "decisionresolution",
        "investmentranking",
        "traderecommendation",
        "strategypromotionsignal",
        "tradeinstruction",
        "orderinstruction",
        "brokerrequest",
        "orderrequest",
        "accountaction",
        "outcomeloader",
        "realizedfalsepositiveanalysis",
        "profitabilityanalysis",
        "liveexecutionsignal",
        "doesnotfetchmarketorderbookpricehistoryoutcomeaccountcredentialidentityorsettlementdata",
        "readexternalhistoryorjsonllogs",
        "scrapewebsites",
        "authenticate",
        "walletscredentialsorprivatekeys",
        "placesubmitsignsendcreateorcancelorders",
        "openuserwebsockets",
        "heartbeat",
        "tradingsdkbrokerexecutiontransportclients",
        "brokerororderrequestpayloads",
        "reconcileexchangeaccounts",
        "reconciliation",
        "settlement",
        "importmanualexecutions",
        "approveproposals",
        "selectlatestdecisions",
        "resolveconflictingreviews",
        "rankinvestments",
        "recommendtrades",
        "compliancelegalgeographicanalysis",
    )

    for fragment in required_fragments:
        assert fragment in normalized, fragment


def test_readme_repository_layout_lists_level_2_node_10_artifacts():
    readme = README_PATH.read_text(encoding="utf-8")
    for expected_path in (
        "2026-06-15-level-2-proposal-evidence-comparison-history.md",
        "proposal_evidence_comparison_history.py",
        "test_proposal_evidence_comparison_history.py",
        "test_proposal_evidence_comparison_history_scope.py",
    ):
        assert expected_path in readme
