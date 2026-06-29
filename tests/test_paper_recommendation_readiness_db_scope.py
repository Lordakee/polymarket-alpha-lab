from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = REPO_ROOT / "src" / "polymarket_alpha_lab"
DB_ROW_PATH = MODULE_DIR / "paper_recommendation_readiness_db_row.py"
STORE_PATH = MODULE_DIR / "paper_recommendation_readiness_store.py"
PSYCOPG_PATH = MODULE_DIR / "paper_recommendation_readiness_psycopg.py"
CONFIG_PATH = MODULE_DIR / "supabase_paper_recommendation_readiness_config.py"

ALLOWED_IMPORTS = {
    DB_ROW_PATH.name: {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "re",
        "typing",
        "polymarket_alpha_lab.json_recovery",
        "polymarket_alpha_lab.paper_recommendation_readiness",
    },
    STORE_PATH.name: {
        "__future__",
        "polymarket_alpha_lab.paper_recommendation_readiness",
        "re",
        "typing",
        "polymarket_alpha_lab.paper_recommendation_readiness_db_row",
    },
    PSYCOPG_PATH.name: {
        "__future__",
        "collections.abc",
        "dataclasses",
        "psycopg",
        "psycopg.types.json",
        "typing",
        "polymarket_alpha_lab.paper_recommendation_readiness_store",
    },
    CONFIG_PATH.name: {
        "__future__",
        "dataclasses",
        "os",
        "polymarket_alpha_lab.supabase_local_dsn",
        "re",
        "typing",
    },
}

FORBIDDEN_IMPORT_PREFIXES = {
    "aiohttp",
    "asyncio",
    "bs4",
    "clob_client",
    "cloudscraper",
    "curl_cffi",
    "eth_account",
    "eth_keys",
    "http",
    "httpx",
    "mechanize",
    "pathlib",
    "playwright",
    "polymarket",
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.archive",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.paper_autonomous_readiness_gate",
    "polymarket_alpha_lab.paper_execution",
    "polymarket_alpha_lab.positions",
    "polymarket_alpha_lab.runner",
    "py_clob_client",
    "requests",
    "requests_html",
    "scrapy",
    "selenium",
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
    "account",
    "apikey",
    "apitoken",
    "auth",
    "authenticate",
    "broker",
    "browser",
    "cancelorder",
    "client",
    "credential",
    "executionclient",
    "fetch",
    "golive",
    "http",
    "liveclient",
    "network",
    "orderclient",
    "orderconstruction",
    "orderinstruction",
    "orderpayload",
    "orderplacement",
    "orderrequest",
    "placeorder",
    "privatekey",
    "routeorder",
    "sdk",
    "sign",
    "signorder",
    "submitorder",
    "transport",
    "wallet",
    "websocket",
}

FORBIDDEN_CALL_NAMES = {
    "__import__",
    "compile",
    "eval",
    "exec",
    "input",
    "open",
    "print",
}

ALLOWED_FORBIDDEN_NAME_MATCHES = {
    "defaultpaperrecommendationreadinesstable",
    "defaultpaperrecommendationreadinessdbtable",
    "fetchall",
    "insertpaperrecommendationreadinessreport",
    "insertpaperrecommendationreadinessreportwithpsycopg",
    "loadpaperrecommendationreadinessreports",
    "loadpaperrecommendationreadinessreportswithpsycopg",
    "paperrecommendationreadinessdbdsnenvvar",
    "paperrecommendationreadinessdbenabledenvvar",
    "paperrecommendationreadinessdbrow",
    "paperrecommendationreadinessdbtableenvvar",
    "paperrecommendationreadinessfromdbrow",
    "paperrecommendationreadinessreportfromdbrow",
    "paperrecommendationreadinessreporttodbrow",
    "paperrecommendationreadinesstodbrow",
    "readonly",
    "supabasepaperrecommendationreadinessconfig",
}

LOCAL_POSTGRES_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"
LOCAL_SECRET_POSTGRES_DSN = (
    "postgresql://sensitive-token:postgres@localhost:54322/postgres"
)


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def module_matches_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def parse_module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def imported_modules(tree: ast.Module) -> list[str]:
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return modules


def collected_names(tree: ast.Module) -> set[str]:
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


@pytest.mark.parametrize("path", (DB_ROW_PATH, STORE_PATH, PSYCOPG_PATH, CONFIG_PATH))
def test_readiness_db_modules_import_only_allowed_dependencies(path: Path) -> None:
    tree = parse_module(path)
    for module_name in imported_modules(tree):
        assert module_name in ALLOWED_IMPORTS[path.name], (path.name, module_name)


@pytest.mark.parametrize("path", (DB_ROW_PATH, STORE_PATH, PSYCOPG_PATH, CONFIG_PATH))
def test_readiness_db_modules_do_not_import_mutation_surfaces(path: Path) -> None:
    tree = parse_module(path)
    for module_name in imported_modules(tree):
        if module_name in {
            "polymarket_alpha_lab.paper_recommendation_readiness",
            "polymarket_alpha_lab.paper_recommendation_readiness_db_row",
            "polymarket_alpha_lab.paper_recommendation_readiness_store",
        }:
            continue
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), (path.name, module_name)


@pytest.mark.parametrize("path", (DB_ROW_PATH, STORE_PATH, PSYCOPG_PATH, CONFIG_PATH))
def test_readiness_db_modules_do_not_define_forbidden_surfaces(path: Path) -> None:
    tree = parse_module(path)
    normalized_names = {
        normalize_identifier(name)
        for name in collected_names(tree)
        if normalize_identifier(name) not in ALLOWED_FORBIDDEN_NAME_MATCHES
    }

    for fragment in FORBIDDEN_NAME_FRAGMENTS:
        assert not any(
            normalize_identifier(fragment) in name for name in normalized_names
        ), (
            path.name,
            fragment,
            normalized_names,
        )


@pytest.mark.parametrize("path", (DB_ROW_PATH, STORE_PATH, PSYCOPG_PATH, CONFIG_PATH))
def test_readiness_db_modules_do_not_perform_file_io_or_dynamic_execution(path: Path) -> None:
    tree = parse_module(path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in FORBIDDEN_CALL_NAMES, (path.name, node.func.id)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (
                node.func.attr == "compile"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "re"
            ):
                continue
            assert node.func.attr not in FORBIDDEN_CALL_NAMES, (path.name, node.func.attr)


def _config_module():
    from polymarket_alpha_lab import supabase_paper_recommendation_readiness_config

    return supabase_paper_recommendation_readiness_config


def test_public_config_constants_match_expected_env_surface() -> None:
    module = _config_module()

    assert module.PAPER_RECOMMENDATION_READINESS_DB_ENABLED_ENV_VAR == (
        "POLYMARKET_ALPHA_LAB_PAPER_RECOMMENDATION_READINESS_DB_ENABLED"
    )
    assert module.PAPER_RECOMMENDATION_READINESS_DB_DSN_ENV_VAR == (
        "POLYMARKET_ALPHA_LAB_PAPER_RECOMMENDATION_READINESS_DB_DSN"
    )
    assert module.PAPER_RECOMMENDATION_READINESS_DB_TABLE_ENV_VAR == (
        "POLYMARKET_ALPHA_LAB_PAPER_RECOMMENDATION_READINESS_DB_TABLE"
    )
    assert (
        module.DEFAULT_PAPER_RECOMMENDATION_READINESS_DB_TABLE
        == "paper_recommendation_readiness_reports"
    )
    assert "SupabasePaperRecommendationReadinessConfig" in module.__all__
    assert "from_paper_recommendation_readiness_db_env" in module.__all__


def test_disabled_env_config_accepts_missing_dsn() -> None:
    module = _config_module()

    config = module.from_paper_recommendation_readiness_db_env({})

    assert config == module.SupabasePaperRecommendationReadinessConfig(
        enabled=False,
        dsn=None,
        table_name=module.DEFAULT_PAPER_RECOMMENDATION_READINESS_DB_TABLE,
    )


def test_enabled_env_config_requires_dsn_without_echoing_secret() -> None:
    module = _config_module()
    secret_dsn = "postgresql://sensitive-token.example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.from_paper_recommendation_readiness_db_env(
            {
                module.PAPER_RECOMMENDATION_READINESS_DB_ENABLED_ENV_VAR: "true",
                module.PAPER_RECOMMENDATION_READINESS_DB_DSN_ENV_VAR: " ",
                "UNRELATED_SECRET": secret_dsn,
            },
        )

    message = str(exc_info.value)
    assert module.PAPER_RECOMMENDATION_READINESS_DB_DSN_ENV_VAR in message
    assert secret_dsn not in message
    assert "secret" not in message.lower()


def test_enabled_env_config_reads_explicit_dsn_at_process_edge() -> None:
    module = _config_module()
    dsn = LOCAL_POSTGRES_DSN

    config = module.from_paper_recommendation_readiness_db_env(
        {
            module.PAPER_RECOMMENDATION_READINESS_DB_ENABLED_ENV_VAR: "1",
            module.PAPER_RECOMMENDATION_READINESS_DB_DSN_ENV_VAR: dsn,
            module.PAPER_RECOMMENDATION_READINESS_DB_TABLE_ENV_VAR: "paper_readiness_reports",
        },
    )

    assert config.enabled is True
    assert config.dsn == dsn
    assert config.table_name == "paper_readiness_reports"


def test_config_is_frozen_and_masks_dsn_in_repr() -> None:
    module = _config_module()
    config = module.SupabasePaperRecommendationReadinessConfig(
        enabled=True,
        dsn=LOCAL_SECRET_POSTGRES_DSN,
        table_name=module.DEFAULT_PAPER_RECOMMENDATION_READINESS_DB_TABLE,
    )

    with pytest.raises(FrozenInstanceError):
        config.enabled = False  # type: ignore[misc]

    rendered = repr(config)
    assert "sensitive-token" not in rendered
    assert LOCAL_SECRET_POSTGRES_DSN not in rendered
    assert "dsn=<redacted>" in rendered


def test_config_rejects_remote_dsn_without_echoing_secret() -> None:
    module = _config_module()
    dsn = "postgresql://sensitive-token@example.invalid/postgres"

    with pytest.raises(ValueError) as exc_info:
        module.SupabasePaperRecommendationReadinessConfig(
            enabled=False,
            dsn=dsn,
            table_name=module.DEFAULT_PAPER_RECOMMENDATION_READINESS_DB_TABLE,
        )

    message = str(exc_info.value)
    assert module.PAPER_RECOMMENDATION_READINESS_DB_DSN_ENV_VAR in message
    assert "local Postgres/Supabase" in message
    assert dsn not in message
    assert "sensitive-token" not in message


@pytest.mark.parametrize(
    "table_name",
    [
        "PaperReports",
        "paper-reports",
        "paper.reports",
        "_paper_reports",
        "paper_reports_",
        "",
    ],
)
def test_config_table_name_must_match_store_simple_lowercase_identifier(
    table_name: str,
) -> None:
    module = _config_module()

    with pytest.raises(ValueError, match="table_name must be a simple lowercase identifier"):
        module.SupabasePaperRecommendationReadinessConfig(
            enabled=False,
            dsn=None,
            table_name=table_name,
        )
