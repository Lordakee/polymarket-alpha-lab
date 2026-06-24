from __future__ import annotations

import ast
from pathlib import Path

CLI_PATH = Path('src/polymarket_alpha_lab/cli.py')
COMMAND = 'paper-autonomous-allocation-proposal-db-history-metrics-evaluation'


def test_command_branch_has_no_raw_network_trade_or_secret_dependencies() -> None:
    text = CLI_PATH.read_text(encoding='utf-8')
    tree = ast.parse(text, filename=str(CLI_PATH))
    forbidden = {
        'account',
        'approve',
        'cancel_order',
        'httpx',
        'private_key',
        'replace_order',
        'requests',
        'socket',
        'submit_order',
        'subprocess',
        'supabase',
        'trade',
        'urllib',
        'wallet',
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        if COMMAND not in {
            child.value
            for child in ast.walk(node)
            if isinstance(child, ast.Constant) and isinstance(child.value, str)
        }:
            continue
        source = ast.unparse(node).replace('-', '_').lower()
        for fragment in forbidden:
            assert fragment not in source
        return
    raise AssertionError('command branch not found')
