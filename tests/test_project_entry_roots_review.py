"""Separate same-assistant source-root boundary review, not a third-party audit."""
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from polymarket_alpha_lab.project_postgres.files import clean_environment
from tests.project_entry_root_probe import ENTRYPOINTS, probe_entry

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('script', ENTRYPOINTS)
@pytest.mark.parametrize('namespace_only', (False, True))
def test_missing_selected_package_never_falls_back_to_other_install(tmp_path, script, namespace_only):
    selected = tmp_path / 'Damaged Source'; (selected / 'scripts').mkdir(parents=True)
    shutil.copyfile(ROOT / 'scripts' / script, selected / 'scripts' / script)
    if namespace_only:
        (selected / 'src/polymarket_alpha_lab').mkdir(parents=True)
    foreign = tmp_path / 'Other Install'; (foreign / 'polymarket_alpha_lab').mkdir(parents=True)
    (foreign / 'polymarket_alpha_lab/__init__.py').write_text(
        "raise RuntimeError('UNWANTED_FALLBACK_EXECUTED')\n", encoding='ascii')
    code = 'import sys, runpy; sys.path.insert(0,sys.argv[1]); sys.argv=sys.argv[2:]; runpy.run_path(sys.argv[0],run_name="__main__")'
    result = subprocess.run([sys.executable, '-I', '-c', code, str(foreign),
        str(selected / 'scripts' / script), '--help'], cwd=tmp_path, env=clean_environment(),
        stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding='utf-8', timeout=30)
    assert result.returncode == 1
    assert result.stdout == ''
    assert result.stderr.strip() == 'project_entry_source_missing'
    assert not (selected / '.local').exists()


@pytest.mark.parametrize('script,arguments', (
    ('project_database.py', ('unexpected-action',)),
    ('review_resolution_queue.py', ('--collect',)),
))
def test_argument_failures_remain_nonzero_under_foreign_editable(tmp_path, script, arguments):
    result = probe_entry(ROOT, sys.executable, tmp_path / 'Elsewhere', script=script, arguments=arguments)
    assert result.returncode == 2
    assert 'PROJECT_ENTRY_SOURCE_OK' in result.stderr
    assert 'FOREIGN_EDITABLE_SELECTED' not in result.stderr
    assert result.stdout == ''
