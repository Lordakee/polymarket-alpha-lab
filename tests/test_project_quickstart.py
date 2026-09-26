"""Keep the existing quickstart's literal commands tied to real argument parsers.

Parsing exits before the command's operation; no guide write/fetch is executed.
This is a documentation test, not an application command interpreter or loader.
"""
import json
from pathlib import Path
import re
import shlex
import shutil
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

# Version-switch examples pin one unchanged original root and two distinct kits:
# the reviewed candidate ($CandidateSource/$CandidatePython) and the retained
# old kit ($OldSource/$OldPython). Every switch invocation names the kit's own
# absolute entrypoint and keeps --root on $OriginalRoot.
SWITCH_COMMANDS = re.findall(
    r'^& \$(?P<python>CandidatePython|OldPython) -I '
    r'"\$(?P<source>CandidateSource|OldSource)/scripts/(?P<script>[^"\r\n]+)"'
    r'(?P<args>[^\r\n]*)$', TEXT, re.M)
SWITCH_ASSIGNMENTS = dict(re.findall(
    r'^\$(OriginalRoot|CandidateSource|CandidatePython|OldSource|OldPython) = ([^\r\n]+)$',
    TEXT, re.M))
SWITCH_INVOCATIONS = re.findall(r'^& \$(?:CandidatePython|OldPython)[^\r\n]*$', TEXT, re.M)
SWITCH_PARSE_ONLY = r'''
import argparse, json, pathlib, runpy, sys
kit = pathlib.Path(sys.argv[1])
original_root = sys.argv[2]
script = sys.argv[3]
arguments = [original_root if value == '$OriginalRoot' else value for value in sys.argv[4:]]
original = argparse.ArgumentParser.parse_args
def parse_only(self, args=None, namespace=None):
    parsed = original(self, args, namespace)
    print(json.dumps({
        'marker': 'QUICKSTART_SWITCH_ARGUMENTS_ACCEPTED',
        'script': sys.argv[0],
        'root': str(getattr(parsed, 'root', None)),
        'action': getattr(parsed, 'action', None),
    }, sort_keys=True))
    raise SystemExit(0)
argparse.ArgumentParser.parse_args = parse_only
sys.argv = [str(kit / 'scripts' / script), *arguments]
try:
    runpy.run_path(sys.argv[0], run_name='__main__')
except SystemExit as error:
    code = error.code
else:
    code = 0
cli = sys.modules['polymarket_alpha_lab.project_postgres.cli']
assert pathlib.Path(cli.__file__).resolve().is_relative_to((kit / 'src').resolve()), 'kit source not selected'
raise SystemExit(code)
'''


@pytest.fixture(scope='module')
def switch_kits(tmp_path_factory):
    """Two synthetic side-by-side kits carrying real entrypoint/source bytes."""
    base = tmp_path_factory.mktemp('quickstart_version_switch_kits')
    kits = {}
    for name in ('CandidateSource', 'OldSource'):
        kit = base / name
        (kit / 'scripts').mkdir(parents=True)
        shutil.copy2(ROOT / 'scripts/project_database.py', kit / 'scripts/project_database.py')
        shutil.copytree(ROOT / 'src/polymarket_alpha_lab', kit / 'src/polymarket_alpha_lab',
                        ignore=shutil.ignore_patterns('__pycache__'))
        kits[name] = kit
    return kits


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


def test_version_switch_variables_pin_two_kits_and_one_original_root():
    assert set(SWITCH_ASSIGNMENTS) == {'OriginalRoot', 'CandidateSource',
                                       'CandidatePython', 'OldSource', 'OldPython'}
    for name in ('OriginalRoot', 'CandidateSource', 'OldSource'):
        assert re.fullmatch(r"'[^']+'", SWITCH_ASSIGNMENTS[name]), name
    assert re.fullmatch(r"Join-Path \$CandidateSource '[^']*'",
                        SWITCH_ASSIGNMENTS['CandidatePython'])
    assert re.fullmatch(r"Join-Path \$OldSource '[^']*'", SWITCH_ASSIGNMENTS['OldPython'])
    # The candidate is a separate reviewed kit; the original root stays unchanged.
    assert SWITCH_ASSIGNMENTS['CandidateSource'] != SWITCH_ASSIGNMENTS['OldSource']
    assert SWITCH_ASSIGNMENTS['CandidateSource'] != SWITCH_ASSIGNMENTS['OriginalRoot']


def test_version_switch_commands_are_exactly_the_documented_set():
    # Every candidate/old invocation line must match the accepted grammar, and
    # the captured set must be exactly the documented commands: an extraction
    # that misses forms or passes with zero commands must not succeed.
    assert len(SWITCH_COMMANDS) == len(SWITCH_INVOCATIONS) == 6
    assert sorted((python_var, shlex.split(argument_text)[2])
                  for python_var, _, _, argument_text in SWITCH_COMMANDS) == sorted([
        ('CandidatePython', 'status'),
        ('OldPython', 'down'),
        ('OldPython', 'status'),
        ('OldPython', 'status'),
        ('OldPython', 'backup'),
        ('OldPython', 'verify-backup'),
    ])
    for python_var, source_var, script, argument_text in SWITCH_COMMANDS:
        assert python_var == ('CandidatePython' if source_var == 'CandidateSource'
                              else 'OldPython'), (python_var, source_var)
        assert script == 'project_database.py'
        assert (ROOT / 'scripts' / script).is_file()
        assert selected_source('scripts/' + script)
        assert shlex.split(argument_text)[:2] == ['--root', '$OriginalRoot'], argument_text


@pytest.mark.parametrize('python_var,source_var,script,argument_text', SWITCH_COMMANDS)
def test_version_switch_command_selects_kit_source_and_original_root_before_any_operation(
        tmp_path, switch_kits, python_var, source_var, script, argument_text):
    kit = switch_kits[source_var]
    other_kit = switch_kits['OldSource' if source_var == 'CandidateSource' else 'CandidateSource']
    original_root = tmp_path / 'Original Project'
    original_root.mkdir()
    working = tmp_path / 'Working Directory'
    working.mkdir()
    tokens = shlex.split(argument_text)
    assert tokens[:2] == ['--root', '$OriginalRoot']
    result = subprocess.run([sys.executable, '-I', '-c', SWITCH_PARSE_ONLY, str(kit),
        str(original_root), script, *tokens], cwd=working, env=clean_environment(),
        stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding='utf-8',
        timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ''
    payload = json.loads(result.stdout)
    assert payload['marker'] == 'QUICKSTART_SWITCH_ARGUMENTS_ACCEPTED'
    # The effective parsed data target is the unchanged original root, not the
    # adjacent kit root the entrypoint would otherwise select for itself.
    assert payload['root'] == str(original_root)
    assert payload['action'] == tokens[2]
    executed = Path(payload['script']).resolve()
    assert executed.is_relative_to(kit.resolve())
    assert not executed.is_relative_to(ROOT.resolve())
    assert not executed.is_relative_to(other_kit.resolve())
    assert not list(working.iterdir())
    assert not list(original_root.iterdir())
