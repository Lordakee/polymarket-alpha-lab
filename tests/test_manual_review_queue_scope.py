import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MANUAL_REVIEW_QUEUE_PATH = (
    REPO_ROOT / "src" / "polymarket_alpha_lab" / "manual_review_queue.py"
)
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"


EXPECTED_MANUAL_REVIEW_QUEUE_EXPORTS = {
    "PaperManualReviewCandidate",
    "PaperManualReviewConfig",
    "PaperManualReviewLog",
    "PaperManualReviewQueue",
    "PaperManualReviewQueueItem",
    "build_paper_manual_review_queue",
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
    "PaperAutonomousAllocationProposalConfig",
    "PaperAutonomousAllocationProposalReasonCodeCount",
    "PaperAutonomousAllocationProposalReport",
    "PaperAutonomousAllocationProposalSourceQueueSummary",
    "build_paper_autonomous_allocation_proposal_report",
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
    "json",
    "collections.abc",
    "dataclasses",
    "datetime",
    "decimal",
    "pathlib",
    "typing",
    "polymarket_alpha_lab.domain",
    "polymarket_alpha_lab.analytics_history",
    "polymarket_alpha_lab.forecast_evidence",
}

EXPECTED_FIRST_PARTY_IMPORTS = {
    "polymarket_alpha_lab.domain": {"MarketScore"},
    "polymarket_alpha_lab.analytics_history": {"PaperAnalyticsHistoryReport"},
    "polymarket_alpha_lab.forecast_evidence": {"PaperForecastEvidenceReport"},
}

FORBIDDEN_IMPORT_PREFIXES = {
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.archive",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.analytics",
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.normalize",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.pipeline",
    "polymarket_alpha_lab.positions",
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

FORBIDDEN_NAME_FRAGMENTS = (
    "privatekey",
    "privkey",
    "apikey",
    "secret",
    "credential",
    "password",
    "mnemonic",
    "seedphrase",
    "auth",
    "authentication",
    "bearer",
    "jwt",
    "wallet",
    "signer",
    "signature",
    "signedorder",
    "signorder",
    "signmessage",
    "signtransaction",
    "placeorder",
    "createorder",
    "cancelorder",
    "submitorder",
    "sendorder",
    "orderlifecycle",
    "ordermanager",
    "orderrouter",
    "executiondecision",
    "liveexecution",
    "client",
    "transport",
    "fetch",
    "request",
    "response",
    "session",
    "urlopen",
    "getjson",
    "websocket",
    "heartbeat",
    "proposal",
    "tradeproposal",
    "approval",
    "broker",
    "reconciler",
    "reconciliation",
    "exchangeaccount",
    "accountstate",
    "accountposition",
    "accountbalance",
    "compliance",
    "legal",
    "jurisdiction",
    "geofence",
    "geographic",
    "geoblock",
    "kyc",
    "aml",
    "sanction",
    "simulateorderbookfill",
    "clobclient",
    "tradesdk",
    "settlement",
    "settle",
    "resolvedoutcome",
    "brier",
    "calibration",
    "edgedecay",
    "holdingperiod",
    "promotionpacket",
    "strategypromotion",
    "dashboard",
    "historicalloader",
    "externalhistory",
    "pricehistoryapi",
    "backfill",
    "download",
    "readjsonl",
    "loadjsonl",
    "scrape",
    "crawler",
    "captcha",
    "antibot",
    "bypass",
    "browserautomation",
)

FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS = (
    "broker",
    "proposal",
    "tradeproposal",
    "execution",
    "credential",
    "wallet",
    "reconciliation",
    "compliance",
    "auth",
    "privatekey",
    "apikey",
    "signer",
    "signature",
    "placeorder",
    "createorder",
    "cancelorder",
    "submitorder",
    "signedorder",
    "orderlifecycle",
    "ordermanager",
    "orderrouter",
    "client",
    "transport",
    "fetch",
    "request",
    "session",
    "websocket",
    "heartbeat",
    "settlement",
    "resolvedoutcome",
    "brier",
    "calibration",
    "dashboard",
    "legal",
    "jurisdiction",
    "geofence",
    "geographic",
)


def parse_manual_review_queue():
    return ast.parse(MANUAL_REVIEW_QUEUE_PATH.read_text(encoding="utf-8"))


def normalize_identifier(value):
    return "".join(character for character in value.lower() if character.isalnum())


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


def test_manual_review_queue_module_imports_only_allowed_dependencies():
    tree = parse_manual_review_queue()
    for module_name in imported_modules(tree):
        assert any(
            module_name == allowed or module_name.startswith(f"{allowed}.")
            for allowed in ALLOWED_IMPORT_PREFIXES
        ), module_name


def test_manual_review_queue_module_does_not_import_forbidden_surfaces():
    tree = parse_manual_review_queue()
    for module_name in imported_modules(tree):
        assert not any(
            module_name == forbidden or module_name.startswith(f"{forbidden}.")
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_manual_review_queue_module_uses_only_allowed_first_party_symbols():
    tree = parse_manual_review_queue()
    assert imported_first_party_symbols(tree) == EXPECTED_FIRST_PARTY_IMPORTS


def test_manual_review_queue_module_does_not_define_forbidden_names():
    tree = parse_manual_review_queue()
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

    lowered = {normalize_identifier(name) for name in names}
    for fragment in FORBIDDEN_NAME_FRAGMENTS:
        assert not any(fragment in name for name in lowered), fragment


def test_manual_review_queue_public_exports_are_paper_review_only():
    tree = parse_manual_review_queue()
    assigned_exports = module_exports(tree)
    assert set(assigned_exports) == EXPECTED_MANUAL_REVIEW_QUEUE_EXPORTS
    for name in assigned_exports:
        assert name.startswith("PaperManualReview") or name.startswith(
            "build_paper_manual_review"
        )
        normalized_name = normalize_identifier(name)
        assert not any(
            fragment in normalized_name for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS
        )


def test_package_root_exports_do_not_leak_forbidden_manual_review_surfaces():
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
            fragment in normalized_name for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS
        )
