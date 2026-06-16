import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TREND_BATCH_HEALTH_TREND_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py"
)
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"
README_PATH = REPO_ROOT / "README.md"


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

ALLOWED_IMPORT_PREFIXES = {
    "__future__",
    "collections.abc",
    "json",
    "dataclasses",
    "datetime",
    "decimal",
    "pathlib",
    "typing",
    "polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health",
}

EXPECTED_FIRST_PARTY_IMPORTS = {
    "polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health": {
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow",
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
    "polymarket_alpha_lab.proposal_evidence_comparison",
    "polymarket_alpha_lab.proposal_evidence_comparison_history",
    "polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health",
    "polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend",
    "polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch",
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
    "accountautomation",
    "accountclient",
    "apikey",
    "apiclient",
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
    "financialadvice",
    "fromfile",
    "fromlog",
    "geographicaccessanalysis",
    "geographicanalysis",
    "geoanalysis",
    "glob",
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
    "logreader",
    "logreaders",
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
    "profitable",
    "profitabilityanalysis",
    "profitablestatus",
    "promotablestatus",
    "proposalapproval",
    "rankinvestments",
    "rawobservation",
    "rawproposal",
    "rawreview",
    "readlog",
    "readlogs",
    "readjsonl",
    "readjsonlhistory",
    "readyforlivetrading",
    "realizedfalsepositiveanalysis",
    "recommendtrade",
    "reconcileexchangeaccounts",
    "reconciliationprocess",
    "reconciliationstatus",
    "replay",
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


def parse_trend_batch_health_trend_module():
    return ast.parse(TREND_BATCH_HEALTH_TREND_PATH.read_text(encoding="utf-8"))


def normalize_identifier(value):
    return "".join(character for character in value.lower() if character.isalnum())


def module_matches_prefix(module_name, prefix):
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def public_export_fragment_matches(example):
    normalized = normalize_identifier(example)
    return any(
        normalize_identifier(fragment) in normalized
        for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS
    )


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


def test_trend_batch_health_trend_module_imports_only_allowed_dependencies():
    tree = parse_trend_batch_health_trend_module()
    for module_name in imported_modules(tree):
        assert any(
            module_matches_prefix(module_name, allowed)
            for allowed in ALLOWED_IMPORT_PREFIXES
        ), module_name


def test_trend_batch_health_trend_module_does_not_import_forbidden_surfaces():
    tree = parse_trend_batch_health_trend_module()
    for module_name in imported_modules(tree):
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_trend_batch_health_trend_uses_only_allowed_first_party_symbols():
    tree = parse_trend_batch_health_trend_module()
    assert imported_first_party_symbols(tree) == EXPECTED_FIRST_PARTY_IMPORTS


def test_trend_batch_health_trend_does_not_import_first_party_modules_wholesale():
    tree = parse_trend_batch_health_trend_module()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Import):
            continue
        for alias in node.names:
            assert alias.name not in EXPECTED_FIRST_PARTY_IMPORTS, alias.name


def test_trend_batch_health_trend_does_not_define_forbidden_names():
    tree = parse_trend_batch_health_trend_module()
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


def test_trend_batch_health_trend_public_exports_are_report_only():
    tree = parse_trend_batch_health_trend_module()
    assigned_exports = module_exports(tree)
    assert (
        set(assigned_exports)
        == EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_TREND_EXPORTS
    )
    for name in assigned_exports:
        assert name.startswith(
            "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrend",
        ) or (
            name
            == "build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report"
        )
        assert not public_export_fragment_matches(name), name

    boundary_constant = (
        "DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_TREND_BOUNDARY_STATEMENT"
    )
    assert boundary_constant not in assigned_exports


def test_package_root_exports_batch_health_trend_batch_health_trend_names_only_for_node_15():
    tree = ast.parse(PACKAGE_ROOT_PATH.read_text(encoding="utf-8"))
    assigned_exports = module_exports(tree)
    for name in (
        EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_TREND_EXPORTS
    ):
        assert name in assigned_exports
        assert not public_export_fragment_matches(name), name

    for name in assigned_exports:
        if name.startswith(
            "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrend",
        ) or (
            name
            == "build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report"
        ):
            assert (
                name
                in EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_TREND_EXPORTS
            )

    boundary_constant = (
        "DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_TREND_BOUNDARY_STATEMENT"
    )
    assert boundary_constant not in assigned_exports


def test_readme_level_2_node_15_section_keeps_report_only_boundaries():
    readme = README_PATH.read_text(encoding="utf-8")
    start = readme.index("## Level 2 Node 15 Status")
    python_api_start = readme.index("## Level 2 Node 15 Python API", start)
    end = readme.index("## Automation Roadmap", python_api_start)
    status_normalized = normalize_identifier(readme[start:python_api_start])
    api_normalized = normalize_identifier(readme[python_api_start:end])
    required_status_fragments = (
        "level2node15status",
        "addsreportonlyproposalevidencecomparisonhistorybatchhealthtrendbatchhealthtrendartifactsoversupplied",
        "suppliedtradeproposalevidencecomparisonhistorybatchhealthtrendbatchhealthreport",
        "trendbatchhealthstatusfrequencies",
        "node14gatestatusfrequencies",
        "duplicategeneratedat",
        "duplicatefingerprint",
        "forauditonly",
        "supportsappendonlyjsonlpersistence",
    )
    no_scope_fragments = (
        "noread",
        "nofetch",
        "noscrape",
        "nobrowserautomation",
        "noaccountautomation",
        "noapiclients",
        "nooutcome",
        "nosettlement",
        "noreconciliation",
        "noranking",
        "norecommendation",
        "nofinancialadvice",
        "noapproval",
        "noexecution",
        "noorderplacement",
        "nojsonlreaders",
        "noexternalloaders",
    )
    report_only_boundary_fragments = (
        "thisisnoreadnofetchnoscrapenobrowserautomationnoaccountautomationnoapiclients",
        "nooutcomenosettlementnoreconciliationnorankingnorecommendationnofinancialadvice",
        "noapprovalnoexecutionnoorderplacementnojsonlreadersandnoexternalloadersscope",
        "itisnotanapprovalworkflowproposalapprovalstepapprovedproposalselector",
        "latestdecisionselectordecisionresolutionprocessinvestmentrankingtraderecommendation",
        "strategypromotionsignaltradeinstructionorderinstructionbrokerrequestorderrequest",
        "accountactioncredentialworkflowprivatekeyhandlingexternalhistoryloaderjsonlreader",
        "scrapingworkflowoutcomeloadersettlementreviewreconciliationprocess",
        "compliancelegalgeographicanalysisrealizedfalsepositiveanalysisprofitabilityanalysis",
        "automaticorderplacementauthorizationorliveexecutionsignal",
        "itdoesnotfetchdatareadlogsscrapeusebrowserautomationuseaccountautomation",
        "authenticatehandlecredentialsprivatekeysplaceorcancelordersopenwebsockets",
        "runheartbeatlogicusetradingsdkbrokerexecutionclientsbuildrequestpayloads",
        "approveproposalsselectlatestdecisionsresolveconflictsrankinvestments",
        "recommendtradesperformoutcomesettlementreconciliationprofitabilityanalysis",
        "importmanualexecutionsorperformcompliancelegalgeographicanalysis",
    )

    for fragment in required_status_fragments:
        assert fragment in status_normalized, fragment

    for fragment in no_scope_fragments:
        assert fragment in status_normalized, fragment

    for fragment in report_only_boundary_fragments:
        assert fragment in status_normalized, fragment

    assert "level2node15pythonapi" in api_normalized


def test_readme_repository_layout_lists_level_2_node_15_artifacts():
    readme = README_PATH.read_text(encoding="utf-8")
    for expected_path in (
        "2026-06-15-level-2-proposal-evidence-comparison-history-batch-health-trend-batch-health-trend.md",
        "proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py",
        "test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py",
        "test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_scope.py",
    ):
        assert expected_path in readme
