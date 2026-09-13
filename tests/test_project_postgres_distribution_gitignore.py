"""Keep the runtime seed out of a later Git-initialized project extraction."""
from pathlib import Path
import subprocess

from polymarket_alpha_lab.project_postgres.distribution import ENGINE


def test_project_gitignore_excludes_bundled_engine_seed(tmp_path):
    root = tmp_path / 'Extracted Kit'
    (root / 'database').mkdir(parents=True)
    rules = Path(__file__).resolve().parents[1] / '.gitignore'
    (root / '.gitignore').write_bytes(rules.read_bytes())
    (root / ENGINE).write_bytes(b'Synthetic engine archive')
    subprocess.run(['git', '-C', str(root), 'init', '-q'],
                   capture_output=True, check=True)
    result = subprocess.run(['git', '-C', str(root), 'check-ignore', '--quiet', ENGINE],
                            capture_output=True, check=False)
    assert result.returncode == 0, 'bundled PostgreSQL binaries must be ignored'
