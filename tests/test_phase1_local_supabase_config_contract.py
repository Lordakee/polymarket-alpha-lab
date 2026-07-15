from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_CONFIG_PATH = REPO_ROOT / "strategy.example.phase1-screening.json"
SCREENING_SCHEMA_DOC = REPO_ROOT / "docs" / "config" / "phase-1-strategy-screening-schema.md"
LOCAL_SUPABASE_DOC = REPO_ROOT / "docs" / "supabase" / "local-supabase-operations.md"
PHASE1_SUPABASE_DOC = (
    REPO_ROOT
    / "docs"
    / "phase1"
    / "probability-event-readonly-supabase-principles.md"
)
STRATEGY_PIPELINE_DOC = REPO_ROOT / "docs" / "strategy_pipeline.md"

EXPECTED_STORAGE_TABLES = {
    "candidate_research_queue": "strategy_candidate_research_queue_reports",
    "team_routes": "team_market_routes",
    "team_memory": "team_memory_readiness_digest_reports",
    "screening_reports": "phase1_strategy_screening_reports",
}
APPROVED_LOCAL_DSN_ENV_VAR = "POLYMARKET_ALPHA_LAB_LOCAL_SUPABASE_DSN"
APPROVED_LOCAL_DSN_PLACEHOLDER = (
    "postgresql://postgres:<password>@127.0.0.1:54322/postgres"
)
LOCAL_DSN_HOSTS = {"localhost", "127.0.0.1", "::1"}
SECRET_LIKE_PATTERNS = (
    re.compile(r"sbp_[a-z0-9_]{8,}", re.IGNORECASE),
    re.compile(r"eyJ[a-z0-9_-]{20,}", re.IGNORECASE),
    re.compile(r"sk-[a-z0-9_-]{16,}", re.IGNORECASE),
    re.compile(r"service[_-]?role", re.IGNORECASE),
    re.compile(r"anon[_-]?key", re.IGNORECASE),
)
FORBIDDEN_CONFIG_FIELD_FAMILIES = (
    "live_",
    "wallet_",
    "account_",
    "auth_",
    "order_",
    "submit_",
    "cancel_",
    "replace_",
    "execute_",
)
FORBIDDEN_CONFIG_FIELD_NAMES = {
    "private_key",
    "seed_phrase",
    "signature",
}
FORBIDDEN_DURABLE_FALLBACK_TOKENS = (
    "jsonl",
    "sqlite",
    "sqlite3",
    "duckdb",
    "redis",
    "mongo",
    "mongodb",
    "sqlalchemy",
    "hosted",
    "pooler.supabase.com",
    "supabase.co",
)

EXPECTED_FORECAST_CONTEXT_MINIMUMS = {
    "default_min_source_count": 2,
    "default_min_source_family_count": 2,
    "microstructure_min_source_count": 1,
    "microstructure_min_source_family_count": 1,
    "superforecaster_min_source_count": 3,
    "superforecaster_min_source_family_count": 3,
}
EXPECTED_FORECAST_CONTEXT_BLOCK_REASONS = {
    "source_count_below_minimum",
    "source_family_count_below_minimum",
}
EXPECTED_MANUAL_REVIEW_REASON_CODES = [
    "manual_review_not_required",
    "manual_review_completed",
    "manual_review_required",
]
EXPECTED_DSN_READINESS_CONTRACT = {
    "required_check_count": "4.000000",
    "ready_status_counts": {
        "ready_check_count": "4.000000",
        "blocker_count": "0.000000",
    },
    "blocker_status_counts": {
        "ready_check_count": "3.000000",
        "blocker_count": "1.000000",
    },
    "reason_codes": {
        "ready": ["local_supabase_postgres_dsn_ready"],
        "invalid": ["local_supabase_postgres_dsn_invalid_blocker"],
        "hosted": [
            "hosted_database_dsn_rejected_blocker",
            "local_supabase_postgres_dsn_invalid_blocker",
        ],
        "jsonl": [
            "jsonl_file_dsn_rejected_blocker",
            "local_supabase_postgres_dsn_invalid_blocker",
        ],
        "sqlite": [
            "sqlite_dsn_rejected_blocker",
            "local_supabase_postgres_dsn_invalid_blocker",
        ],
    },
}


def _strategy_config() -> dict[str, object]:
    return json.loads(STRATEGY_CONFIG_PATH.read_text(encoding="utf-8"))


def _walk_keys(value: object) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(str(key))
            keys.extend(_walk_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_keys(item))
    return tuple(keys)


def _walk_strings(value: object) -> tuple[str, ...]:
    strings: list[str] = []
    if isinstance(value, str):
        strings.append(value)
    elif isinstance(value, dict):
        for item in value.values():
            strings.extend(_walk_strings(item))
    elif isinstance(value, list):
        for item in value:
            strings.extend(_walk_strings(item))
    return tuple(strings)


def _doc_text(path: Path) -> str:
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8").lower())


def test_phase1_strategy_screening_config_uses_local_supabase_postgres_storage() -> None:
    config = _strategy_config()
    storage = config["storage"]

    assert config["paper_only"] is True
    assert config["report_only"] is True
    assert config["readonly"] is True
    assert isinstance(storage, dict)
    assert storage == {
        "kind": "local_supabase_postgres",
        "enabled": True,
        "dsn_env_var": APPROVED_LOCAL_DSN_ENV_VAR,
        "example_dsn": APPROVED_LOCAL_DSN_PLACEHOLDER,
        "tables": EXPECTED_STORAGE_TABLES,
    }


def test_phase1_strategy_screening_example_dsn_is_local_and_placeholder_only() -> None:
    storage = _strategy_config()["storage"]
    assert isinstance(storage, dict)
    dsn = storage["example_dsn"]
    assert isinstance(dsn, str)

    parsed = urlparse(dsn)
    assert parsed.scheme == "postgresql"
    assert parsed.hostname in LOCAL_DSN_HOSTS
    assert parsed.port == 54322
    assert parsed.path == "/postgres"
    assert parsed.username == "postgres"
    assert parsed.password == "<password>"
    assert parse_qs(parsed.query) == {}

    assert dsn == APPROVED_LOCAL_DSN_PLACEHOLDER
    assert "supabase.co" not in dsn
    assert "pooler.supabase.com" not in dsn
    assert "localhost,example.invalid" not in dsn


def test_phase1_strategy_screening_config_contains_no_real_secret_or_live_fields() -> None:
    config = _strategy_config()
    rendered = json.dumps(config, sort_keys=True)
    lowered_rendered = rendered.lower()

    assert "<password>" in rendered
    assert "super-secret" not in lowered_rendered
    assert "password123" not in lowered_rendered
    assert "access_token" not in lowered_rendered
    assert "private_key" not in lowered_rendered
    for pattern in SECRET_LIKE_PATTERNS:
        assert pattern.search(rendered) is None

    forbidden_keys = []
    for key in _walk_keys(config):
        if key in FORBIDDEN_CONFIG_FIELD_NAMES:
            forbidden_keys.append(key)
        if key.startswith(FORBIDDEN_CONFIG_FIELD_FAMILIES):
            forbidden_keys.append(key)

    assert forbidden_keys == []


def test_phase1_strategy_screening_config_does_not_define_durable_fallback_store() -> None:
    config = _strategy_config()
    storage = config["storage"]
    assert isinstance(storage, dict)

    string_values = tuple(value.lower() for value in _walk_strings(storage))
    blocked_values = [
        value
        for value in string_values
        if any(token in value for token in FORBIDDEN_DURABLE_FALLBACK_TOKENS)
    ]

    assert blocked_values == []
    assert "fallback" not in storage
    assert "fallbacks" not in storage
    assert "legacy_store" not in storage
    assert "durable_store" not in storage
    assert "store_kind" not in storage


def test_phase1_strategy_config_matches_forecast_context_row_minimums() -> None:
    config = _strategy_config()
    thresholds = config["screening_thresholds"]
    manual_review = config["manual_review_gates"]

    assert isinstance(thresholds, dict)
    assert isinstance(manual_review, dict)
    assert "min_source_quorum_count" not in thresholds
    assert {
        key: thresholds[key] for key in EXPECTED_FORECAST_CONTEXT_MINIMUMS
    } == EXPECTED_FORECAST_CONTEXT_MINIMUMS
    assert EXPECTED_FORECAST_CONTEXT_BLOCK_REASONS.issubset(
        manual_review["block_reason_codes"],
    )
    assert "source_quorum_insufficient" not in manual_review["block_reason_codes"]

    schema_text = _doc_text(SCREENING_SCHEMA_DOC)
    for reason_code in EXPECTED_FORECAST_CONTEXT_BLOCK_REASONS:
        assert reason_code in schema_text
    assert "`source_quorum_insufficient` is not part" in schema_text


def test_phase1_strategy_config_matches_category_manual_review_reasons() -> None:
    manual_review = _strategy_config()["manual_review_gates"]

    assert isinstance(manual_review, dict)
    assert manual_review["review_reason_codes"] == EXPECTED_MANUAL_REVIEW_REASON_CODES
    assert "operator_review_missing" not in manual_review["block_reason_codes"]


def test_phase1_strategy_config_freezes_local_dsn_reason_and_count_invariants() -> None:
    config = _strategy_config()
    manual_review = config["manual_review_gates"]

    assert config["dsn_readiness_contract"] == EXPECTED_DSN_READINESS_CONTRACT
    assert isinstance(manual_review, dict)
    assert "local_supabase_dsn_missing" not in manual_review["block_reason_codes"]
    assert {
        "hosted_database_dsn_rejected_blocker",
        "jsonl_file_dsn_rejected_blocker",
        "local_supabase_postgres_dsn_invalid_blocker",
        "sqlite_dsn_rejected_blocker",
    }.issubset(manual_review["block_reason_codes"])


def test_phase1_local_supabase_docs_freeze_durable_only_contract() -> None:
    docs = {
        "screening_schema": _doc_text(SCREENING_SCHEMA_DOC),
        "local_supabase_ops": _doc_text(LOCAL_SUPABASE_DOC),
        "phase1_supabase_principles": _doc_text(PHASE1_SUPABASE_DOC),
        "strategy_pipeline": _doc_text(STRATEGY_PIPELINE_DOC),
    }

    for name, text in docs.items():
        assert "local supabase/postgres" in text, name
        assert (
            "validate_local_postgres_dsn" in text
            or "local postgres dsn validator" in text
            or "validated as local postgres dsn" in text
            or "validated as a local postgres dsn" in text
            or "validated as local postgres dsns" in text
        ), name
        assert "durable" in text, name

    assert "storage.kind` must be `local_supabase_postgres`" in docs["screening_schema"]
    assert APPROVED_LOCAL_DSN_PLACEHOLDER.lower() in docs["screening_schema"]
    assert "real password, token, hosted dsn, or production database url" in docs[
        "screening_schema"
    ]
    assert "must not contain a" in docs["screening_schema"]

    assert "must use local supabase/postgres only" in docs["local_supabase_ops"]
    assert "hosted supabase, hosted postgres, or any hosted database target" in docs[
        "local_supabase_ops"
    ]
    assert "sqlite or sqlite fallback files" in docs["local_supabase_ops"]
    assert "jsonl, csv, parquet, or filesystem ledgers as durable substitutes" in docs[
        "local_supabase_ops"
    ]
    assert "environment-specific fallback behavior that silently switches away" in docs[
        "local_supabase_ops"
    ]
    assert "must fail closed" in docs["local_supabase_ops"]

    assert "must use local supabase/postgres only" in docs[
        "phase1_supabase_principles"
    ]
    assert "forbidden durable substitutes" in docs["phase1_supabase_principles"]
    assert "hosted database assumptions" in docs["phase1_supabase_principles"]
    assert "sqlite or sqlite fallback files" in docs["phase1_supabase_principles"]
    assert "jsonl durable journals" in docs["phase1_supabase_principles"]

    assert "all durable project data for this strategy pipeline must use local" in docs[
        "strategy_pipeline"
    ]
    assert "hosted database assumptions" in docs["strategy_pipeline"]
    assert "sqlite" in docs["strategy_pipeline"]
    assert "jsonl" in docs["strategy_pipeline"]
    assert "must not become phase 1 durable memory" in docs["strategy_pipeline"]
