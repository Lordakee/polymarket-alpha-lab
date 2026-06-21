from __future__ import annotations

import ast
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = (
    REPO_ROOT / "src" / "polymarket_alpha_lab" / "paper_trade_cost_audit_db_row.py",
    REPO_ROOT / "src" / "polymarket_alpha_lab" / "paper_trade_cost_audit_store.py",
    REPO_ROOT / "src" / "polymarket_alpha_lab" / "paper_trade_cost_audit_psycopg.py",
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "supabase_paper_trade_cost_audit_config.py",
)
CLI_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "cli.py"
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260620000006_paper_trade_cost_audit_reports.sql"
)

ALLOWED_IMPORT_MODULES = {
    "__future__",
    "collections.abc",
    "dataclasses",
    "datetime",
    "decimal",
    "hashlib",
    "json",
    "os",
    "polymarket_alpha_lab.json_recovery",
    "polymarket_alpha_lab.paper_trade_cost_audit",
    "polymarket_alpha_lab.paper_trade_cost_audit_db_row",
    "polymarket_alpha_lab.paper_trade_cost_audit_store",
    "re",
    "typing",
}
ALLOWED_IMPORT_MODULES_BY_FILE = {
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "paper_trade_cost_audit_psycopg.py": {
        "psycopg",
        "psycopg.types.json",
    },
}
FORBIDDEN_IMPORT_PREFIXES = {
    "aiohttp",
    "clob_client",
    "eth_account",
    "eth_keys",
    "httpx",
    "polymarket",
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.paper_execution",
    "py_clob_client",
    "requests",
    "web3",
}
FORBIDDEN_NAME_FRAGMENTS = {
    "account",
    "auth",
    "cancel",
    "client",
    "credential",
    "exchange",
    "execution",
    "mutate",
    "mutation",
    "order",
    "place",
    "private",
    "privatekey",
    "replace",
    "secret",
    "sign",
    "submit",
    "tradeinstruction",
    "wallet",
}
ALLOWED_FORBIDDEN_NAME_MATCHES = {
    "loadpapertradecostauditreportswithpsycopg",
    "loadpapertradecostauditreports",
    "papertradecostauditreportdbrow",
    "papertradecostauditreports",
    "papertradecostauditreportfromdbrow",
    "papertradecostauditreporttodbrow",
    "replace",
    "report",
    "reports",
}


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def compact(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().lower())


def table_body(sql: str) -> str:
    match = re.search(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.paper_trade_cost_audit_reports\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match, "migration must create public.paper_trade_cost_audit_reports"
    return compact(match.group(1))


def parse_module(path: Path) -> ast.Module:
    assert path.exists(), f"missing source file: {path}"
    return ast.parse(path.read_text(encoding="utf-8"))


def imported_modules(tree: ast.Module) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return tuple(modules)


def module_matches_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def defined_or_referenced_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
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


def migration_sql() -> str:
    assert MIGRATION.exists(), f"missing migration: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def test_db_foundation_imports_only_storage_boundary_dependencies() -> None:
    for source_file in SOURCE_FILES:
        tree = parse_module(source_file)
        allowed_import_modules = ALLOWED_IMPORT_MODULES | ALLOWED_IMPORT_MODULES_BY_FILE.get(
            source_file,
            set(),
        )
        for module_name in imported_modules(tree):
            assert module_name in allowed_import_modules, (source_file, module_name)
            assert not any(
                module_matches_prefix(module_name, forbidden)
                for forbidden in FORBIDDEN_IMPORT_PREFIXES
            ), (source_file, module_name)


def test_db_foundation_does_not_define_live_auth_wallet_or_order_surfaces() -> None:
    for source_file in SOURCE_FILES:
        tree = parse_module(source_file)
        lowered = {
            normalize_identifier(name)
            for name in defined_or_referenced_names(tree)
            if normalize_identifier(name) not in ALLOWED_FORBIDDEN_NAME_MATCHES
        }
        for fragment in FORBIDDEN_NAME_FRAGMENTS:
            assert not any(normalize_identifier(fragment) in name for name in lowered), (
                source_file,
                fragment,
                lowered,
            )


def test_cli_has_no_paper_trade_cost_audit_db_wiring_or_dsn_flags() -> None:
    cli_text = CLI_PATH.read_text(encoding="utf-8").lower()

    forbidden_cli_fragments = (
        "paper-trade-cost-audit-db",
        "paper_trade_cost_audit_db",
        "paper-trade-cost-audit-dsn",
        "paper-trade-cost-audit-table",
        "paper_trade_cost_audit_psycopg",
        "supabase_paper_trade_cost_audit_config",
        "insert_paper_trade_cost_audit_report",
        "load_paper_trade_cost_audit_reports",
    )
    for fragment in forbidden_cli_fragments:
        assert fragment not in cli_text, fragment


def test_migration_creates_cost_audit_table_with_required_columns() -> None:
    body = table_body(migration_sql())

    required_columns = (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "config_version text not null",
        "trade_count integer not null",
        "total_filled_size numeric not null",
        "total_requested_size numeric not null",
        "fill_rate numeric",
        "mean_theoretical_edge numeric",
        "mean_cost_adjusted_edge numeric",
        "mean_edge_cost_drag numeric",
        "total_edge_cost_drag numeric",
        "mean_research_slippage numeric",
        "mean_fill_slippage numeric",
        "partial_fill_count integer not null",
        "negative_cost_adjusted_edge_count integer not null",
        "largest_single_trade_cost_drag numeric",
        "payload_json jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    )
    for column in required_columns:
        assert column in body


def test_migration_enforces_cost_audit_invariants_with_hard_checks() -> None:
    body = table_body(migration_sql())

    expected_checks = (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (trade_count >= 0)",
        "check (total_filled_size >= 0)",
        "check (total_requested_size >= 0)",
        "check (fill_rate is null or (fill_rate >= 0 and fill_rate <= 1))",
        "check (mean_edge_cost_drag is null or mean_edge_cost_drag >= 0)",
        "check (total_edge_cost_drag is null or total_edge_cost_drag >= 0)",
        "check (mean_research_slippage is null or mean_research_slippage >= 0)",
        "check (mean_fill_slippage is null or mean_fill_slippage >= 0)",
        "check (partial_fill_count >= 0)",
        "check (negative_cost_adjusted_edge_count >= 0)",
        "check (largest_single_trade_cost_drag is null or largest_single_trade_cost_drag >= 0)",
        "check (total_filled_size <= total_requested_size)",
        "check (partial_fill_count <= trade_count)",
        "check (negative_cost_adjusted_edge_count <= trade_count)",
        "check ((trade_count = 0 and total_filled_size = 0 and total_requested_size = 0 and fill_rate is null and mean_theoretical_edge is null and mean_cost_adjusted_edge is null and mean_edge_cost_drag is null and total_edge_cost_drag is null and mean_research_slippage is null and mean_fill_slippage is null and largest_single_trade_cost_drag is null and partial_fill_count = 0 and negative_cost_adjusted_edge_count = 0) or trade_count > 0)",
        "check (jsonb_typeof(payload_json) = 'object')",
        "check (payload_json ? 'paper_only' and payload_json -> 'paper_only' = 'true'::jsonb)",
        "check (payload_json ? 'report_only' and payload_json -> 'report_only' = 'true'::jsonb)",
        "check (payload_json ? 'readonly' and payload_json -> 'readonly' = 'true'::jsonb)",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
    )
    for check in expected_checks:
        assert check in body


def test_migration_enforces_cost_audit_payload_scalar_parity() -> None:
    body = table_body(migration_sql())

    expected_checks = (
        "check (payload_json ? 'generated_at' and jsonb_typeof(payload_json -> 'generated_at') = 'string' and (payload_json ->> 'generated_at')::timestamptz = generated_at)",
        "check (payload_json ? 'config_version' and jsonb_typeof(payload_json -> 'config_version') = 'string' and payload_json ->> 'config_version' = config_version)",
        "check (payload_json ? 'trade_count' and jsonb_typeof(payload_json -> 'trade_count') = 'number' and (payload_json ->> 'trade_count')::integer = trade_count)",
        "check (payload_json ? 'total_filled_size' and jsonb_typeof(payload_json -> 'total_filled_size') = 'string' and (payload_json ->> 'total_filled_size')::numeric = total_filled_size)",
        "check (payload_json ? 'total_requested_size' and jsonb_typeof(payload_json -> 'total_requested_size') = 'string' and (payload_json ->> 'total_requested_size')::numeric = total_requested_size)",
        "check (payload_json ? 'fill_rate' and ((fill_rate is null and payload_json -> 'fill_rate' = 'null'::jsonb) or (jsonb_typeof(payload_json -> 'fill_rate') = 'string' and (payload_json ->> 'fill_rate')::numeric = fill_rate)))",
        "check (payload_json ? 'mean_theoretical_edge' and ((mean_theoretical_edge is null and payload_json -> 'mean_theoretical_edge' = 'null'::jsonb) or (jsonb_typeof(payload_json -> 'mean_theoretical_edge') = 'string' and (payload_json ->> 'mean_theoretical_edge')::numeric = mean_theoretical_edge)))",
        "check (payload_json ? 'mean_cost_adjusted_edge' and ((mean_cost_adjusted_edge is null and payload_json -> 'mean_cost_adjusted_edge' = 'null'::jsonb) or (jsonb_typeof(payload_json -> 'mean_cost_adjusted_edge') = 'string' and (payload_json ->> 'mean_cost_adjusted_edge')::numeric = mean_cost_adjusted_edge)))",
        "check (payload_json ? 'mean_edge_cost_drag' and ((mean_edge_cost_drag is null and payload_json -> 'mean_edge_cost_drag' = 'null'::jsonb) or (jsonb_typeof(payload_json -> 'mean_edge_cost_drag') = 'string' and (payload_json ->> 'mean_edge_cost_drag')::numeric = mean_edge_cost_drag)))",
        "check (payload_json ? 'total_edge_cost_drag' and ((total_edge_cost_drag is null and payload_json -> 'total_edge_cost_drag' = 'null'::jsonb) or (jsonb_typeof(payload_json -> 'total_edge_cost_drag') = 'string' and (payload_json ->> 'total_edge_cost_drag')::numeric = total_edge_cost_drag)))",
        "check (payload_json ? 'mean_research_slippage' and ((mean_research_slippage is null and payload_json -> 'mean_research_slippage' = 'null'::jsonb) or (jsonb_typeof(payload_json -> 'mean_research_slippage') = 'string' and (payload_json ->> 'mean_research_slippage')::numeric = mean_research_slippage)))",
        "check (payload_json ? 'mean_fill_slippage' and ((mean_fill_slippage is null and payload_json -> 'mean_fill_slippage' = 'null'::jsonb) or (jsonb_typeof(payload_json -> 'mean_fill_slippage') = 'string' and (payload_json ->> 'mean_fill_slippage')::numeric = mean_fill_slippage)))",
        "check (payload_json ? 'partial_fill_count' and jsonb_typeof(payload_json -> 'partial_fill_count') = 'number' and (payload_json ->> 'partial_fill_count')::integer = partial_fill_count)",
        "check (payload_json ? 'negative_cost_adjusted_edge_count' and jsonb_typeof(payload_json -> 'negative_cost_adjusted_edge_count') = 'number' and (payload_json ->> 'negative_cost_adjusted_edge_count')::integer = negative_cost_adjusted_edge_count)",
        "check (payload_json ? 'largest_single_trade_cost_drag' and ((largest_single_trade_cost_drag is null and payload_json -> 'largest_single_trade_cost_drag' = 'null'::jsonb) or (jsonb_typeof(payload_json -> 'largest_single_trade_cost_drag') = 'string' and (payload_json ->> 'largest_single_trade_cost_drag')::numeric = largest_single_trade_cost_drag)))",
    )
    for check in expected_checks:
        assert check in body


def test_migration_adds_cost_audit_lookup_indexes() -> None:
    sql = compact(migration_sql())

    assert "report_sha256 text primary key" in sql
    assert (
        "create unique index if not exists idx_ptcar_report_sha256 on "
        "public.paper_trade_cost_audit_reports (report_sha256);"
        not in sql
    )

    expected_indexes = (
        "create index if not exists idx_ptcar_generated_inserted_report on public.paper_trade_cost_audit_reports (generated_at desc, inserted_at desc, report_sha256 desc);",
        "create index if not exists idx_ptcar_config_generated on public.paper_trade_cost_audit_reports (config_version, generated_at desc);",
        "create index if not exists idx_ptcar_payload_json_gin on public.paper_trade_cost_audit_reports using gin (payload_json jsonb_path_ops);",
    )
    for index in expected_indexes:
        assert index in sql


def test_migration_does_not_include_live_auth_wallet_private_or_order_terms() -> None:
    sql = migration_sql().lower()

    forbidden_patterns = (
        r"\bauth\b",
        r"\bwallet\b",
        r"\bprivate[_ -]?key\b",
        r"\bexchange\b",
        r"\bclient\b",
        r"\border[_ -]?(request|payload|instruction|placement|submission)\b",
        r"\bsign\b",
        r"\bsubmit\b",
        r"\bcancel\b",
        r"\breplace\b",
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, sql), pattern
