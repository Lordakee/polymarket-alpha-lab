"""Print retained resolution-review metadata; no confirmation, source fetch or model call."""
from pathlib import Path

from polymarket_alpha_lab.research_resolution_inspection_cli import main


if __name__ == "__main__":
    raise SystemExit(main(default_root=Path(__file__).resolve().parents[1]))
