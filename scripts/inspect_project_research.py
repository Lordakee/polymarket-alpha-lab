"""Inspect one native-project research claim; no model, public network or business write."""
from pathlib import Path

from polymarket_alpha_lab.research_execution_cli import main


if __name__ == "__main__":
    raise SystemExit(main(default_root=Path(__file__).resolve().parents[1]))
