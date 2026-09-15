"""Test-only diagnostics: real pytest children, no project database or network."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
from threading import Event

import pytest

from tests import ci_thread_dump as diagnostic

ROOT = Path(__file__).resolve().parents[1]


def run_child(tmp_path, body, *, options=(), disable_builtin=True, seconds='0.05'):
    test = tmp_path / 'test_owned_probe.py'
    test.write_text(body, encoding='utf-8')
    # Keep this child away from the project's default testpaths and user plugins.
    config = tmp_path / 'pytest.ini'
    config.write_text('[pytest]\n', encoding='utf-8')
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('PYTEST_', 'PYTHONPATH', 'PYTHONHOME'))}
    env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
    args = [sys.executable, '-m', 'pytest', '-q', '-s', '-c', str(config)]
    if disable_builtin:
        args += ['-p', 'no:faulthandler']
    args += ['-p', 'tests.ci_thread_dump', '-o', 'faulthandler_timeout='+seconds, *options, str(test)]
    return subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True,
                          encoding='utf-8', timeout=30, check=False)


@pytest.mark.parametrize('phase', ['setup', 'call', 'teardown'])
def test_actual_stack_dump_covers_protocol_and_keeps_fatal_handler(tmp_path, phase):
    result = run_child(tmp_path, f'''
import faulthandler, time, pytest
from threading import enumerate as threads

def forbidden(*a, **k):
    raise AssertionError('unsafe C watchdog used')
faulthandler.dump_traceback_later = forbidden
@pytest.fixture
def slow():
    if {phase!r} == 'setup': time.sleep(.15)
    yield
    if {phase!r} == 'teardown': time.sleep(.15)
def test_probe(slow):
    assert faulthandler.is_enabled()
    if {phase!r} == 'call': time.sleep(.15)
def test_next():
    assert len([t for t in threads() if t.name == 'ci-traceback-diagnostic']) == 1
''')
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert '2 passed' in result.stdout
    assert result.stderr.count('CI diagnostic after 0.05s') == 1
    assert 'test_owned_probe.py' in result.stderr and 'Thread' in result.stderr


@pytest.mark.parametrize('body,code', [
    ('def test_fast(): pass\n', 0),
    ('def test_failure(): assert False\n', 1),
    ('def test_interrupt(): raise KeyboardInterrupt()\n', 2),
])
def test_exit_status_is_not_swallowed_or_retried(tmp_path, body, code):
    result = run_child(tmp_path, body, seconds='120')
    assert result.returncode == code, (result.stdout, result.stderr)
    assert 'CI diagnostic after' not in result.stderr


@pytest.mark.parametrize('seconds', ['0', '-1', 'nan', 'inf', 'bad'])
def test_disabled_or_nonfinite_diagnostic_refuses_before_tests(tmp_path, seconds):
    result = run_child(tmp_path, "raise AssertionError('body must not be imported')", seconds=seconds)
    assert result.returncode == 4 and 'positive finite' in result.stderr
    assert 'body must not be imported' not in result.stdout


def test_duplicate_builtin_and_requested_hard_exit_cannot_silently_downgrade(tmp_path):
    body = "raise AssertionError('body must not be imported')"
    result = run_child(tmp_path, body, disable_builtin=False)
    assert result.returncode == 4 and 'Use -p no:faulthandler' in result.stderr
    result = run_child(tmp_path, body, options=('-o', 'faulthandler_exit_on_timeout=true'))
    assert result.returncode == 4 and 'cannot implement a hard timeout' in result.stderr


def test_cancel_closes_owned_fd_once_without_late_callback(monkeypatch):
    calls = []
    monkeypatch.setattr(diagnostic.faulthandler, 'dump_traceback', lambda **kw: calls.append(kw))
    with tempfile.TemporaryFile() as output:
        watcher = diagnostic.Watchdog(120, output.fileno())
        watcher.stop(); watcher.stop()
        assert not calls and not watcher.thread.is_alive()
        with pytest.raises(OSError): os.fstat(watcher.fd)
        os.fstat(output.fileno())  # Borrowed output descriptor was not closed.


def test_diagnostic_failure_surfaces_without_private_text(monkeypatch):
    entered = Event()
    def broken(**kw):
        entered.set()
        raise ValueError('private diagnostic error')
    monkeypatch.setattr(diagnostic.faulthandler, 'dump_traceback', broken)
    with tempfile.TemporaryFile() as output:
        watcher = diagnostic.Watchdog(.001, output.fileno())
        assert entered.wait(5)
        with pytest.raises(RuntimeError, match='^ci_traceback_diagnostic_failed$'):
            watcher.stop()
        with pytest.raises(OSError): os.fstat(watcher.fd)


def test_thread_start_failure_closes_the_duplicate(monkeypatch):
    duplicates = []; original = diagnostic.os.dup
    def dup(fd):
        value = original(fd); duplicates.append(value); return value
    def failed_start(self): raise RuntimeError('synthetic start failure')
    monkeypatch.setattr(diagnostic.os, 'dup', dup)
    monkeypatch.setattr(diagnostic.Thread, 'start', failed_start)
    with tempfile.TemporaryFile() as output:
        with pytest.raises(RuntimeError): diagnostic.Watchdog(120, output.fileno())
        assert len(duplicates) == 1
        with pytest.raises(OSError): os.fstat(duplicates[0])
        os.fstat(output.fileno())
