"""Manage the project's native PostgreSQL, without Docker or Supabase services."""
from pathlib import Path
import sys

from polymarket_alpha_lab.project_postgres.cli import main


if __name__ == '__main__':
    raise SystemExit(main(['--root', str(Path(__file__).resolve().parents[1]), *sys.argv[1:]]))
