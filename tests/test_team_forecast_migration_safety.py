from __future__ import annotations

from pathlib import Path
import re


SAFETY_DOC_PATH = Path("docs/team-forecast-migration-safety.md")
RUNBOOK_PATH = Path("docs/team-forecast-supabase-runbook.md")
MIGRATION_PATH = Path("supabase/migrations/20260701000000_team_forecast_tables.sql")
PROBABILITY_YES_CONTRACT_MIGRATION_PATH = Path(
    "supabase/migrations/20260713000000_team_forecast_probability_yes_contract.sql"
)

EXPECTED_TABLES = (
    "team_profiles",
    "team_market_routes",
    "team_forecasts",
    "team_forecast_evidence",
    "team_forecast_outcomes",
)


def _safety_text() -> str:
    assert SAFETY_DOC_PATH.exists(), f"{SAFETY_DOC_PATH} must exist"
    return SAFETY_DOC_PATH.read_text(encoding="utf-8")


def test_migration_safety_documents_append_only_local_phase_1_policy() -> None:
    text = _safety_text()
    lower_text = text.lower()

    required_fragments = (
        str(MIGRATION_PATH),
        "applied migrations are append-only",
        "local supabase/postgres only",
        "no hosted db assumptions",
        "no raw dsn examples",
        "no auth/rls/role policy work in phase 1",
        "corrective changes must ship through new migrations",
        "paper-only/report-only/readonly",
    )
    for fragment in required_fragments:
        assert fragment.lower() in lower_text

    for table_name in EXPECTED_TABLES:
        assert table_name in text

    assert "do not edit an applied migration" in lower_text


def test_migration_safety_doc_omits_connection_secrets_and_hosted_examples() -> None:
    lower_text = _safety_text().lower()

    forbidden_patterns = (
        r"postgres(?:ql)?://",
        r"\bdb\.[a-z0-9-]+\.supabase\.co\b",
        r"\b[a-z0-9-]+\.pooler\.supabase\.com\b",
        r"supabase_(?:anon|service)_key",
        r"service_role",
        r"\bsbp_[a-z0-9_=-]{8,}",
        r"\beyj[a-z0-9_-]{20,}",
        r"\bsk-[a-z0-9_-]{20,}",
    )
    for pattern in forbidden_patterns:
        assert re.search(pattern, lower_text) is None


def test_migration_safety_doc_points_operators_to_runbook_without_replacing_it() -> None:
    text = _safety_text()

    assert str(RUNBOOK_PATH) in text
    assert "sudo -n docker exec supabase-db psql" not in text
    assert "psql -v ON_ERROR_STOP=1" not in text


def test_migration_safety_inventories_probability_yes_comment_contract() -> None:
    text = _safety_text()
    lower_text = text.lower()

    baseline_index = text.index(str(MIGRATION_PATH))
    contract_index = text.index(str(PROBABILITY_YES_CONTRACT_MIGRATION_PATH))
    assert baseline_index < contract_index
    assert "column comments only" in lower_text
    assert "no table rewrite, dml, or row rewrite" in lower_text
    assert (
        "Canonical Decimal P(YES) for the event; never P(selected_side)."
        in text
    )
    assert (
        "Paper-review side being evaluated; does not reorient "
        "forecast_probability."
        in text
    )
