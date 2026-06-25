from __future__ import annotations

from pathlib import Path


def test_history_psycopg_and_config_modules_stay_report_only_boundaries() -> None:
    sources = "\n".join(
        Path(path).read_text(encoding="utf-8")
        for path in (
            "src/polymarket_alpha_lab/"
            "paper_probability_selection_summary_history_psycopg.py",
            "src/polymarket_alpha_lab/"
            "supabase_paper_probability_selection_summary_history_config.py",
        )
    ).lower()

    for banned in (
        "live_trading",
        "wallet",
        "private_key",
        "api_key",
        "secret_key",
        "order_placement",
        "order_cancel",
        "order_sign",
        "signing",
        "clob",
        "exchange",
    ):
        assert banned not in sources
