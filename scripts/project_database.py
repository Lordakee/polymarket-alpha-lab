"""Manage the project's native PostgreSQL, without Docker or Supabase services."""
from pathlib import Path
import sys

# Always use this source/kit, not an unrelated editable installation.
ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / 'src/polymarket_alpha_lab/__init__.py').is_file():
    raise SystemExit('project_entry_source_missing')
sys.path.insert(0, str(ROOT / 'src'))

from polymarket_alpha_lab.project_postgres.cli import main


if __name__ == '__main__':
    raise SystemExit(main(['--root', str(ROOT), *sys.argv[1:]]))
