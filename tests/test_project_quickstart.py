"""Keep the existing quickstart's literal commands tied to real argument parsers.

Parsing exits before the command's operation; no guide write/fetch is executed.
This is a documentation test, not an application command interpreter or loader.
"""
from pathlib import Path
import re
import shlex
import subprocess
import sys

import pytest

from polymarket_alpha_lab.project_postgres.distribution import selected_source
from polymarket_alpha_lab.project_postgres.files import clean_environment

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / 'database/quickstart.md'
TEXT = GUIDE.read_text(encoding='utf-8')
COMMANDS = re.findall(r'^& \$Python -I "\$Project/scripts/([^"\r\n]+)"([^\r\n]*)$', TEXT, re.M)
_PARSE_ONLY = r'''
import argparse, pathlib, runpy, sys
root = pathlib.Path(sys.argv[1])
script = sys.argv[2]
arguments = [str(root) if value == '$Project' else value for value in sys.argv[3:]]
original = argparse.ArgumentParser.parse_args
def parse_only(self, args=None, namespace=None):
    original(self, args, namespace)
    print('QUICKSTART_ARGUMENTS_ACCEPTED')
    raise SystemExit(0)
argparse.ArgumentParser.parse_args = parse_only
sys.argv = [str(root / 'scripts' / script), *arguments]
runpy.run_path(sys.argv[0], run_name='__main__')
'''


@pytest.mark.parametrize('script,argument_text', COMMANDS)
def test_literal_operator_command_is_valid_before_any_operation(tmp_path, script, argument_text):
    result = subprocess.run([sys.executable, '-I', '-c', _PARSE_ONLY, str(ROOT), script,
        *shlex.split(argument_text)], cwd=tmp_path, env=clean_environment(), stdin=subprocess.DEVNULL,
        capture_output=True, text=True, encoding='utf-8', timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == 'QUICKSTART_ARGUMENTS_ACCEPTED'
    assert result.stderr == ''
    assert not list(tmp_path.iterdir())


def test_guide_contains_commands_and_they_never_enable_live_trading():
    assert len(COMMANDS) >= 12  # An empty regex extraction must not pass vacuously.
    for script, args in COMMANDS:
        assert selected_source('scripts/' + script)
        assert (ROOT / 'scripts' / script).is_file()
        assert '--root $Project' in args or script == 'discover_crypto_research.py'
    assert 'no `--root` option' in TEXT
    assert '**no model factory**' in TEXT and 'D1' in TEXT and 'D3' in TEXT


def test_all_immediate_runbook_links_are_in_new_kits():
    for href in re.findall(r'\]\(([^)]+)\)', TEXT):
        if href.startswith(('#', 'https://')):
            continue
        path = (GUIDE.parent / href.split('#')[0]).resolve()
        relative = path.relative_to(ROOT).as_posix()
        assert path.is_file(), href
        assert selected_source(relative), f'runbook omitted from kit: {relative}'
