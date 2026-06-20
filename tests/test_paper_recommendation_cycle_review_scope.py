import ast
import inspect


def test_cycle_review_has_no_db_cli_network_auth_wallet_or_order_imports():
    from polymarket_alpha_lab import paper_recommendation_cycle_review as module

    tree = ast.parse(inspect.getsource(module))
    forbidden_import_roots = {
        "aiohttp",
        "argparse",
        "click",
        "eth_account",
        "httpx",
        "polymarket",
        "polymarket_clob_client",
        "psycopg",
        "py_clob_client",
        "requests",
        "supabase",
        "typer",
        "web3",
        "websocket",
        "websockets",
    }
    forbidden_name_fragments = (
        "account",
        "api",
        "auth",
        "cancel",
        "client",
        "connect",
        "cursor",
        "dsn",
        "execute",
        "login",
        "network",
        "order",
        "private_key",
        "psycopg",
        "request",
        "session",
        "sign",
        "submit",
        "supabase",
        "wallet",
    )

    imported_roots: set[str] = set()
    called_names: set[str] = set()
    identifiers: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(
                alias.name.split(".", maxsplit=1)[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)
        elif isinstance(node, ast.Name):
            identifiers.add(node.id)
        elif isinstance(node, ast.Attribute):
            identifiers.add(node.attr)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            identifiers.add(node.name)

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert not any(
        fragment in name.lower()
        for fragment in forbidden_name_fragments
        for name in called_names
    )
    assert not any(
        fragment in name.lower()
        for fragment in forbidden_name_fragments
        for name in identifiers
    )
