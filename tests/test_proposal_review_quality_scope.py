import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROPOSAL_REVIEW_QUALITY_PATH = (
    REPO_ROOT / "src" / "polymarket_alpha_lab" / "proposal_review_quality.py"
)
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"


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
EXPECTED_LEVEL_2_ARTIFACT_EXPORTS = (
    EXPECTED_LEVEL_2_PROPOSAL_PACKET_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_SUMMARY_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_QUALITY_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_DIAGNOSTIC_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_COVERAGE_EXPORTS
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
}

EXPECTED_FIRST_PARTY_IMPORTS = {
    "polymarket_alpha_lab.proposal_review_summary": {
        "TradeProposalReviewBucketSummary",
        "TradeProposalReviewReasonCodeSummary",
        "TradeProposalReviewSummaryReport",
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

FORBIDDEN_NAME_FRAGMENTS = (
    "privatekey",
    "privkey",
    "apikey",
    "secret",
    "credentialrequest",
    "credentialworkflow",
    "credentialstore",
    "credentialmanager",
    "credentialprovider",
    "credentialloader",
    "password",
    "mnemonic",
    "seedphrase",
    "accountaction",
    "accountauthentication",
    "accountlogin",
    "accountsession",
    "accountstate",
    "accountposition",
    "accountbalance",
    "bearertoken",
    "jwttoken",
    "walletsignature",
    "walletsigner",
    "walletclient",
    "signedorder",
    "signorder",
    "signmessage",
    "signtransaction",
    "placeorder",
    "createorder",
    "cancelorder",
    "submitorder",
    "sendorder",
    "orderinstruction",
    "orderrequest",
    "orderpayload",
    "orderplacement",
    "orderlifecycle",
    "ordermanager",
    "orderrouter",
    "tradeinstruction",
    "executionclient",
    "executiondecision",
    "executionengine",
    "executionqueue",
    "executionrequest",
    "executionrouter",
    "executionworkflow",
    "liveexecution",
    "approvalworkflow",
    "approvalqueue",
    "approvalrouter",
    "approvalbroker",
    "approvalstatus",
    "approvedby",
    "approvedat",
    "autoapproval",
    "autoapprove",
    "automaticapproval",
    "unattendedapproval",
    "approver",
    "brokerclient",
    "brokerrequest",
    "tradingbroker",
    "tradingclient",
    "transportclient",
    "transportrequest",
    "httpclient",
    "marketclient",
    "requestpayload",
    "requestbody",
    "requestparams",
    "responsebody",
    "urlopen",
    "getjson",
    "fetchmarket",
    "fetchorderbook",
    "fetchpricehistory",
    "fetchoutcome",
    "fetchaccount",
    "websocket",
    "heartbeat",
    "reconciler",
    "reconciliation",
    "exchangeaccount",
    "clobclient",
    "tradesdk",
    "settlement",
    "settle",
    "manualexecution",
    "manualexecutionimport",
    "resolvedoutcome",
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
    "compliance",
    "legal",
    "jurisdiction",
    "geofence",
    "geographic",
    "geoblock",
    "kyc",
    "aml",
    "sanction",
)

FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS = (
    "privatekey",
    "privkey",
    "apikey",
    "credentialrequest",
    "credentialworkflow",
    "accountaction",
    "accountauthentication",
    "walletsignature",
    "walletsigner",
    "signedorder",
    "placeorder",
    "createorder",
    "cancelorder",
    "submitorder",
    "orderinstruction",
    "orderrequest",
    "orderlifecycle",
    "ordermanager",
    "orderrouter",
    "tradeinstruction",
    "executionclient",
    "executiondecision",
    "executionrequest",
    "liveexecution",
    "approvalworkflow",
    "approvalqueue",
    "approvalrouter",
    "approvalbroker",
    "approvalstatus",
    "autoapproval",
    "autoapprove",
    "automaticapproval",
    "unattendedapproval",
    "brokerclient",
    "brokerrequest",
    "tradingclient",
    "transportclient",
    "transportrequest",
    "requestpayload",
    "websocket",
    "heartbeat",
    "reconciliation",
    "settlement",
    "manualexecution",
    "resolvedoutcome",
    "dashboard",
    "compliance",
    "legal",
    "jurisdiction",
    "geofence",
    "geographic",
)


def parse_proposal_review_quality():
    return ast.parse(PROPOSAL_REVIEW_QUALITY_PATH.read_text(encoding="utf-8"))


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
        if (
            isinstance(node, ast.ImportFrom)
            and node.module in EXPECTED_FIRST_PARTY_IMPORTS
        ):
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


def test_proposal_review_quality_module_imports_only_allowed_dependencies():
    tree = parse_proposal_review_quality()
    for module_name in imported_modules(tree):
        assert any(
            module_name == allowed or module_name.startswith(f"{allowed}.")
            for allowed in ALLOWED_IMPORT_PREFIXES
        ), module_name


def test_proposal_review_quality_module_does_not_import_forbidden_surfaces():
    tree = parse_proposal_review_quality()
    for module_name in imported_modules(tree):
        assert not any(
            module_name == forbidden or module_name.startswith(f"{forbidden}.")
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_proposal_review_quality_module_uses_only_allowed_first_party_symbols():
    tree = parse_proposal_review_quality()
    assert imported_first_party_symbols(tree) == EXPECTED_FIRST_PARTY_IMPORTS


def test_proposal_review_quality_module_does_not_define_forbidden_live_or_workflow_names():
    tree = parse_proposal_review_quality()
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


def test_trade_proposal_review_quality_public_exports_are_report_only():
    tree = parse_proposal_review_quality()
    assigned_exports = module_exports(tree)
    assert set(assigned_exports) == EXPECTED_PROPOSAL_REVIEW_QUALITY_EXPORTS
    for name in assigned_exports:
        assert name.startswith("TradeProposalReviewQuality") or name == (
            "build_trade_proposal_review_quality_report"
        )
        normalized_name = normalize_identifier(name)
        assert not any(
            fragment in normalized_name
            for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS
        )


def test_package_root_exports_do_not_leak_forbidden_level_2_node_4_surfaces():
    tree = ast.parse(PACKAGE_ROOT_PATH.read_text(encoding="utf-8"))
    assigned_exports = module_exports(tree)
    for name in assigned_exports:
        normalized_name = normalize_identifier(name)
        if any(
            fragment in normalized_name for fragment in ("proposal", "tradeproposal")
        ):
            assert name in EXPECTED_LEVEL_2_ARTIFACT_EXPORTS
            continue
        assert not any(
            fragment in normalized_name
            for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS
        )
