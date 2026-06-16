import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "proposal_evidence_comparison_artifact_registry.py"
)
README_PATH = REPO_ROOT / "README.md"

FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp",
    "ccxt",
    "httpx",
    "playwright",
    "polymarket",
    "py_clob_client",
    "requests",
    "selenium",
    "web3",
    "websocket",
    "websockets",
}

FORBIDDEN_PUBLIC_NAME_FRAGMENTS = (
    "account",
    "api_client",
    "approve",
    "authenticate",
    "browser",
    "cancel_order",
    "credential",
    "execute",
    "fetch",
    "financial_advice",
    "glob",
    "http",
    "load",
    "place_order",
    "rank",
    "read",
    "recommend",
    "replay",
    "scrape",
    "session",
    "sign",
    "submit",
    "trade",
    "wallet",
    "websocket",
)


def normalize_identifier(value: str) -> str:
    return "".join(character.lower() for character in value if character.isalnum())


def parse_module() -> ast.Module:
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


def test_registry_module_uses_only_dataclasses_imports():
    tree = parse_module()
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]

    for node in imports:
        if isinstance(node, ast.Import):
            assert {alias.name for alias in node.names} <= {"dataclasses"}
        else:
            root = (node.module or "").split(".")[0]
            assert root not in FORBIDDEN_IMPORT_ROOTS
            assert node.module in {"__future__", "dataclasses"}


def test_registry_public_api_does_not_expose_loader_or_execution_names():
    tree = parse_module()
    assigned_exports: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets)
            and isinstance(node.value, ast.Tuple)
        ):
            for item in node.value.elts:
                assert isinstance(item, ast.Constant)
                assert isinstance(item.value, str)
                assigned_exports.add(item.value)

    assert assigned_exports == {
        "PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS",
        "REPORT_ONLY_FORBIDDEN_SURFACES",
        "ProposalEvidenceComparisonArtifactDefinition",
        "get_proposal_evidence_comparison_artifact",
        "list_proposal_evidence_comparison_artifacts",
    }
    normalized_exports = {normalize_identifier(name) for name in assigned_exports}
    for forbidden in FORBIDDEN_PUBLIC_NAME_FRAGMENTS:
        normalized_forbidden = normalize_identifier(forbidden)
        assert all(normalized_forbidden not in name for name in normalized_exports)


def test_registry_readme_section_keeps_report_only_boundaries():
    readme = README_PATH.read_text(encoding="utf-8")
    start = readme.index("## Proposal Evidence Comparison Artifact Registry")
    end = readme.index("## Automation Roadmap", start)
    normalized = normalize_identifier(readme[start:end])

    for fragment in (
        "staticreportonlyregistry",
        "stringmetadataonly",
        "doesnotimportartifactimplementationmodules",
        "doesnotfetch",
        "doesnotreadjsonl",
        "doesnotload",
        "doesnotreplay",
        "doesnotscrape",
        "doesnotusebrowserautomation",
        "doesnotuseaccountautomation",
        "doesnotuseapiclients",
        "doesnotplaceorders",
        "doesnotrank",
        "doesnotrecommend",
        "doesnotprovidefinancialadvice",
    ):
        assert fragment in normalized, fragment
