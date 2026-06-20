import ast
import importlib
import inspect


def test_strategy_cycle_action_gated_queue_source_has_only_pure_imports_and_calls():
    module = importlib.import_module(
        "polymarket_alpha_lab.strategy_cycle_action_gated_queue_source",
    )

    source = inspect.getsource(module)
    tree = ast.parse(source)
    forbidden_import_roots = {
        "aiohttp",
        "asyncpg",
        "dotenv",
        "eth_account",
        "httpx",
        "os",
        "polymarket",
        "polymarket_clob_client",
        "psycopg",
        "py_clob_client",
        "requests",
        "socket",
        "sqlalchemy",
        "supabase",
        "urllib",
        "web3",
        "websocket",
        "websockets",
    }
    forbidden_polymarket_modules = {
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_db_row",
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_store",
        "polymarket_alpha_lab.api",
        "polymarket_alpha_lab.cli",
        "polymarket_alpha_lab.journal",
        "polymarket_alpha_lab.paper",
        "polymarket_alpha_lab.paper_execution",
        "polymarket_alpha_lab.positions",
        "polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_config",
    }
    forbidden_call_names = {
        "authenticate",
        "cancel_order",
        "connect",
        "create_order",
        "delete",
        "getenv",
        "login",
        "patch",
        "post",
        "put",
        "request",
        "sign",
        "sign_message",
        "submit_order",
    }
    forbidden_fragments = {
        "account",
        "auth",
        "cancel_order",
        "create_order",
        "live",
        "order_submission",
        "private-key",
        "private_key",
        "psycopg",
        "submit_order",
        "supabase",
        "wallet",
    }

    imported_roots: set[str] = set()
    imported_modules: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
                imported_roots.add(alias.name.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
            imported_roots.add(node.module.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert all(
        imported_module != forbidden_module
        and not imported_module.startswith(f"{forbidden_module}.")
        for imported_module in imported_modules
        for forbidden_module in forbidden_polymarket_modules
    )
    assert called_names.isdisjoint(forbidden_call_names)
    assert all(fragment not in source.lower() for fragment in forbidden_fragments)
