from __future__ import annotations

import importlib
from pathlib import Path


ENV_EXAMPLE_PATH = Path(".env.example")
CONFIG_MODULE_NAMES = (
    "polymarket_alpha_lab.supabase_paper_autonomous_screening_decision_support_gate_config",
    "polymarket_alpha_lab.supabase_paper_autonomous_allocation_proposal_config",
    "polymarket_alpha_lab.supabase_paper_project_screening_rank_stability_config",
)


def test_env_example_contains_new_autonomous_db_env_vars_without_sample_values() -> None:
    text = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
    lines = set(text.splitlines())

    for module_name in CONFIG_MODULE_NAMES:
        module = importlib.import_module(module_name)
        for name in dir(module):
            if not name.endswith("_ENV_VAR"):
                continue
            value = getattr(module, name)
            if isinstance(value, str) and value.startswith("POLYMARKET_ALPHA_LAB_"):
                assert f"{value}=" in lines

    assert "postgresql://" not in text
