"""Inspect/manage durable research tasks using this source or extracted kit."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from polymarket_alpha_lab.research_dispatch_cli import main


if __name__ == '__main__':
    raise SystemExit(main(default_root=ROOT))
