"""Print diagnostics from the initialized project-private database; no public network or model call."""
from pathlib import Path

from polymarket_alpha_lab.research_evaluation_cli import main


if __name__ == "__main__":
    raise SystemExit(main(default_root=Path(__file__).resolve().parents[1]))
