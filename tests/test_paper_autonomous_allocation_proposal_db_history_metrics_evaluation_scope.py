from pathlib import Path

MODULE_PATH = Path('src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_metrics_evaluation.py')

def test_evaluation_module_has_no_io_or_env_leaks() -> None:
    text = MODULE_PATH.read_text()
    forbidden = (
        'psycopg',
        'supabase',
        'os.environ',
        'requests',
        'httpx',
        'urllib',
        'subprocess',
        'socket',
        'asyncio',
        'import io',
        'import sys',
        'import logging',
        'import pathlib',
        'private_key',
        'wallet',
        'account',
        'submit_order',
        'cancel_order',
        'replace_order',
        'execute(',
        'approve(',
        'trade(',
        'open(',
        'print(',
    )
    for fragment in forbidden:
        assert fragment not in text, fragment
