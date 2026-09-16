"""Own-source entrypoints with an unrelated editable import path, no native DB."""
from pathlib import Path
import json
import subprocess
import sys

import pytest

from tests.project_entry_root_probe import ENTRYPOINTS, probe_entry

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('script', ENTRYPOINTS)
def test_operator_help_uses_selected_source_not_unrelated_editable(tmp_path, script):
    result = probe_entry(ROOT, sys.executable, tmp_path / 'Other Working Directory', script=script)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'PROJECT_ENTRY_SOURCE_OK' in result.stderr
    assert '--root' in result.stdout
    assert 'FOREIGN_EDITABLE_SELECTED' not in result.stderr
    assert not (tmp_path / '.local').exists()


def test_database_explicit_root_is_data_target_not_import_target(tmp_path):
    target = tmp_path / 'Selected Data Root'; target.mkdir()
    (target / 'pyproject.toml').write_text('[project]\nname="polymarket-alpha-lab"\n')
    (target / 'database').mkdir()
    (target / 'database/migrations.lock.json').write_text('{}')
    before = sorted(str(p.relative_to(target)) for p in target.rglob('*'))
    result = probe_entry(ROOT, sys.executable, tmp_path / 'Other Cwd', script='project_database.py',
                         arguments=('--root', str(target), 'status'))
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == {'status': 'not_initialized'}
    assert result.stderr == 'PROJECT_ENTRY_SOURCE_OK\n'
    assert sorted(str(p.relative_to(target)) for p in target.rglob('*')) == before


def test_confirmation_missing_permission_rejects_before_database(tmp_path):
    target = tmp_path / 'Must Not Initialize'
    result = probe_entry(ROOT, sys.executable, tmp_path / 'Other Cwd', script='review_resolution_queue.py',
                         arguments=('--root', str(target), '--confirm'))
    assert result.returncode == 2, result.stdout + result.stderr
    assert 'PROJECT_ENTRY_SOURCE_OK' in result.stderr
    assert '--confirm requires --allow-resolution-write' in result.stderr
    assert not target.exists()
