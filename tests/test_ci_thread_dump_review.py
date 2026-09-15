"""Separate failure-path review of the explicit CI-only diagnostic replacement."""
import os
from pathlib import Path
import tempfile
from threading import Event
from types import SimpleNamespace

import pytest

from tests import ci_thread_dump as diagnostic
from tests.test_ci_thread_dump import run_child


def test_constructor_failure_must_not_leak_a_duplicated_descriptor(monkeypatch):
    duplicated = []; original_dup = os.dup
    def dup(fd):
        value = original_dup(fd); duplicated.append(value); return value
    def broken_thread(**kw): raise RuntimeError('thread constructor failed')
    monkeypatch.setattr(diagnostic.os, 'dup', dup)
    monkeypatch.setattr(diagnostic, 'Thread', broken_thread)
    with tempfile.TemporaryFile() as output:
        with pytest.raises(RuntimeError): diagnostic.Watchdog(120, output.fileno())
        fd = duplicated[0]
        try:
            with pytest.raises(OSError): os.fstat(fd)
        finally:
            try: os.close(fd)
            except OSError: pass


def test_worker_close_failure_cannot_be_only_an_unhandled_warning(monkeypatch):
    closed = Event(); original_close = os.close
    def close_then_fail(fd):
        original_close(fd); closed.set(); raise OSError('private close error')
    with tempfile.TemporaryFile() as output:
        # Only the explicit diagnostic module uses the fake OS object.
        monkeypatch.setattr(diagnostic, 'os', SimpleNamespace(dup=os.dup, write=os.write, close=close_then_fail))
        watcher = diagnostic.Watchdog(120, output.fileno())
        try:
            with pytest.raises(RuntimeError, match='^ci_traceback_diagnostic_failed$'): watcher.stop()
        finally:
            assert closed.wait(5)


@pytest.mark.parametrize('originally_enabled', [False, True])
def test_explicit_fatal_handler_configuration_is_restored(monkeypatch, originally_enabled):
    events = []
    handler = SimpleNamespace(is_enabled=lambda: originally_enabled,
        enable=lambda **kw: events.append(('enable', kw)), disable=lambda: events.append(('disable',)))
    monkeypatch.setattr(diagnostic, 'faulthandler', handler)
    config = SimpleNamespace(stash=pytest.Stash(),
        pluginmanager=SimpleNamespace(hasplugin=lambda _: False),
        getini=lambda key: '120' if key == 'faulthandler_timeout' else False)
    diagnostic.pytest_configure(config)
    state = config.stash[diagnostic._STATE]; fd = state['fd']
    assert events == [('enable', {'file': fd})]
    diagnostic.pytest_unconfigure(config)
    assert events[1] == ('disable',)
    assert events[2:] == ([('enable', {'file': state['original_fd']})] if originally_enabled else [])
    with pytest.raises(OSError): os.fstat(fd)
    assert diagnostic._STATE not in config.stash
    diagnostic.pytest_unconfigure(config)  # idempotent after successful cleanup


def test_worker_failure_makes_actual_pytest_nonzero_without_disclosing_exception(tmp_path):
    result = run_child(tmp_path, '''
import time
from tests import ci_thread_dump

def broken(**kw): raise ValueError('PRIVATE-DIAGNOSTIC-TEXT')
ci_thread_dump.faulthandler.dump_traceback = broken

def test_not_false_green(): time.sleep(.15)
''')
    assert result.returncode != 0
    assert 'ci_traceback_diagnostic_failed' in result.stdout + result.stderr
    assert 'PRIVATE-DIAGNOSTIC-TEXT' not in result.stdout + result.stderr


def test_real_python_churn_uses_synchronous_diagnostic_not_c_watchdog(tmp_path):
    result = run_child(tmp_path, '''
import faulthandler, time
from pathlib import PureWindowsPath

def forbidden(*a, **kw): raise AssertionError('C timeout watchdog used')
faulthandler.dump_traceback_later = forbidden

def churn(depth, number):
    if depth: return churn(depth-1, number+1)
    path = PureWindowsPath('C:/ordinary/synthetic/' + str(number))
    return path.root, path.parent, path.name

def test_churn():
    end = time.monotonic()+.3
    while time.monotonic() < end: churn(30,1)
    assert faulthandler.is_enabled()
''')
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert 'CI diagnostic after 0.05s' in result.stderr
    assert 'test_owned_probe.py' in result.stderr
