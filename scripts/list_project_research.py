"""List the initialized project's research claims without running or retrying them."""
from pathlib import Path

from polymarket_alpha_lab.research_inventory_cli import main


if __name__ == "__main__":
    raise SystemExit(main(default_root=Path(__file__).resolve().parents[1]))
