from __future__ import annotations

import ast
from pathlib import Path


CLI_PATH = Path("src/polymarket_alpha_lab/cli.py")

FORBIDDEN_TOKENS = frozenset(
    (
        "wallet",
        "private_key",
        "allowance",
        "balance",
        "account",
        "sign",
        "signed",
        "submit_order",
        "cancel_order",
        "replace_order",
        "live_trade",
        "execute_trade",
    ),
)


class _ForbiddenTokenCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.tokens: set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:
        self.tokens.add(node.id.lower())

    def visit_Attribute(self, node: ast.Attribute) -> None:
        self.tokens.add(node.attr.lower())
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str):
            self.tokens.add(node.value.lower())


def _trend_command_source() -> str:
    source = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    chunks: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and (
            node.name in (
                "_run_action_gated_queue_decision_support_trend",
                "_print_action_gated_queue_decision_support_trend_summary",
            )
        ):
            chunks.append(ast.get_source_segment(source, node) or "")
    assert chunks, "trend CLI functions must exist"
    return "\n".join(chunks)


def test_action_gated_queue_decision_support_trend_cli_scope_stays_phase_one() -> None:
    source = _trend_command_source()
    collector = _ForbiddenTokenCollector()
    collector.visit(ast.parse(source))

    for token in FORBIDDEN_TOKENS:
        assert token not in collector.tokens
    assert "load_paper_action_gated_strategy_recommendation_queue_decision_support_reports_with_psycopg" in source
    assert "insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg" in source
    assert "build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report" in source


def test_action_gated_queue_decision_support_trend_cli_exposes_no_dsn_flags() -> None:
    source = CLI_PATH.read_text(encoding="utf-8")

    command_index = source.index('"action-gated-queue-decision-support-trend"')
    next_command_index = source.index('"action-gated-queue-history"', command_index)
    command_block = source[command_index:next_command_index]

    assert "--source-limit" in command_block
    assert "--source-risk-status" in command_block
    assert "--persist" in command_block
    assert "--dsn" not in command_block
    assert "--decision-support-db-dsn" not in command_block
