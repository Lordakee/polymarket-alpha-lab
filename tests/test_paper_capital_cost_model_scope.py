import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "paper_capital_cost_model.py"

EXPECTED_EXPORTS = (
    "PaperCapitalCostAssumptions",
    "PaperCapitalCostModelConfig",
    "PaperCapitalCostReport",
    "build_paper_capital_cost_report",
)

ALLOWED_IMPORT_MODULES = {
    "__future__",
    "dataclasses",
    "datetime",
    "decimal",
}

FORBIDDEN_IMPORT_PREFIXES = {
    "aiohttp",
    "clob_client",
    "cloudscraper",
    "curl_cffi",
    "eth_account",
    "eth_keys",
    "http",
    "httpx",
    "os",
    "polymarket",
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.archive",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.paper_execution",
    "polymarket_alpha_lab.positions",
    "py_clob_client",
    "requests",
    "socket",
    "ssl",
    "subprocess",
    "urllib",
    "urllib3",
    "web3",
    "websocket",
    "websockets",
}

FORBIDDEN_NAME_FRAGMENTS = {
    "api",
    "auth",
    "authenticate",
    "client",
    "credential",
    "http",
    "order",
    "privatekey",
    "requests",
    "sign",
    "submit",
    "tradepayload",
    "transport",
    "urllib",
    "wallet",
}

FORBIDDEN_EXACT_NAMES = {
    "open",
    "read",
    "write",
}

ALLOWED_FORBIDDEN_NAME_MATCHES = {
    "buildpapercapitalcostreport",
    "papercapitalcostassumptions",
    "papercapitalcostmodelconfig",
    "papercapitalcostreport",
    "readonly",
}


def normalize_identifier(value):
    return "".join(character for character in value.lower() if character.isalnum())


def module_matches_prefix(module_name, prefix):
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def parse_module(path=MODULE_PATH):
    return ast.parse(path.read_text(encoding="utf-8"))


def imported_modules(tree):
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return modules


def module_exports(tree):
    assigned_exports = None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                assigned_exports = ast.literal_eval(node.value)
    assert assigned_exports is not None
    return tuple(assigned_exports)


def collected_names(tree):
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
    return names


def test_paper_capital_cost_model_imports_only_allowed_dependencies():
    tree = parse_module()

    for module_name in imported_modules(tree):
        assert module_name in ALLOWED_IMPORT_MODULES, module_name


def test_paper_capital_cost_model_does_not_import_live_network_or_exchange_surfaces():
    tree = parse_module()

    for module_name in imported_modules(tree):
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_paper_capital_cost_model_public_exports_exactly_report_api():
    tree = parse_module()
    assigned_exports = module_exports(tree)

    assert assigned_exports == EXPECTED_EXPORTS
    for name in assigned_exports:
        normalized = normalize_identifier(name)
        assert "order" not in normalized
        assert "client" not in normalized
        assert "auth" not in normalized
        assert "wallet" not in normalized
        assert "privatekey" not in normalized


def test_paper_capital_cost_model_defines_no_forbidden_live_names():
    tree = parse_module()
    normalized_names = {
        normalize_identifier(name)
        for name in collected_names(tree)
        if normalize_identifier(name) not in ALLOWED_FORBIDDEN_NAME_MATCHES
    }

    for fragment in FORBIDDEN_NAME_FRAGMENTS:
        assert not any(
            normalize_identifier(fragment) in name for name in normalized_names
        ), (
            fragment,
            normalized_names,
        )


def test_paper_capital_cost_model_defines_no_file_operation_primitives():
    tree = parse_module()
    names = {name.lower() for name in collected_names(tree)}

    for exact_name in FORBIDDEN_EXACT_NAMES:
        assert exact_name not in names
