from __future__ import annotations

import re
from pathlib import Path


DOC_PATHS = (
    Path("README.md"),
    Path("docs/strategy-recommendation-layer.md"),
    Path("docs/paper-recommendation-reducers.md"),
)

AVAILABLE_CLI_COMMANDS = (
    "paper-recommendation-reason-trend",
    "paper-probability-side-edge-report",
    "paper-recommendation-queue-report",
    "paper-recommendation-risk-budget-report",
)

PLANNED_ONLY_REDUCER_FAMILIES = (
    "paper_recommendation_queue",
)

AVAILABLE_MODULE_ONLY_REDUCER_FAMILIES = (
    "paper_capital_cost",
    "paper_capital_cost_side_edge_adapter",
)


def _read(path: Path) -> str:
    assert path.exists(), f"{path} must exist"
    return path.read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def test_recommendation_reducer_cli_docs_mark_available_commands() -> None:
    for path in DOC_PATHS:
        text = _read(path)
        normalized = _normalized(text).lower()

        assert "available cli" in normalized, path
        for command in AVAILABLE_CLI_COMMANDS:
            assert command in text, (path, command)


def test_recommendation_reducer_docs_mark_planned_only_families() -> None:
    for path in DOC_PATHS:
        normalized = _normalized(_read(path))

        for family in PLANNED_ONLY_REDUCER_FAMILIES:
            pattern = (
                rf"`{re.escape(family)}`[^.]*planned-only|"
                rf"planned-only[^.]*`{re.escape(family)}`"
            )
            assert re.search(pattern, normalized, flags=re.IGNORECASE), (path, family)


def test_recommendation_reducer_docs_mark_module_only_reducers() -> None:
    for path in DOC_PATHS:
        text = _read(path)
        normalized = _normalized(text)

        for family in AVAILABLE_MODULE_ONLY_REDUCER_FAMILIES:
            assert "module-local" in normalized or "module only" in normalized, path
            pattern = (
                rf"`{re.escape(family)}`[^.]*available[^.]*module|"
                rf"available[^.]*module[^.]*`{re.escape(family)}`|"
                rf"`{re.escape(family)}`[^.]*module-local|"
                rf"module-local[^.]*`{re.escape(family)}`"
            )
            assert re.search(pattern, normalized, flags=re.IGNORECASE), (path, family)
            offending_lines = [
                line
                for line in text.splitlines()
                if family in line and "planned-only" in line.lower()
            ]
            assert offending_lines == [], (path, family, offending_lines)


def test_recommendation_reducer_persist_docs_are_report_only() -> None:
    required_phrases = (
        "--persist",
        "default-off",
        "env-driven",
        "local Supabase/Postgres report-only DB persistence",
        "not live trading",
    )

    for path in DOC_PATHS:
        text = _read(path)
        normalized_text = _normalized(text)
        for phrase in required_phrases:
            assert phrase in normalized_text, (path, phrase)

        normalized = normalized_text.lower()
        assert "local" in normalized and "report-only" in normalized, path
        assert "live trading" in normalized and "not live trading" in normalized, path
