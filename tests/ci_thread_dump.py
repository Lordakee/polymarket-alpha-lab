"""Opt-in CI traceback diagnostics without CPython's C timeout watchdog.

Use -p no:faulthandler -p tests.ci_thread_dump and the SAME positive
faulthandler_timeout. Fatal-exception handlers stay enabled. This is a diagnostic
trigger, not a test deadline or a retry. Outer CI job limits are unchanged.
A Python watchdog needs the GIL: it cannot diagnose a native GIL-holding hang.
"""
from __future__ import annotations

import faulthandler
import math
import os
import sys
from threading import Event, Thread

import pytest

_STATE = pytest.StashKey()


class Watchdog:
    """Own the duplicated descriptor until the diagnostic worker has finished."""
    def __init__(self, seconds: float, descriptor: int):
        self.cancelled = Event()
        self.failed = False
        self.fd = os.dup(descriptor)
        self.seconds = seconds
        try:
            self.thread = Thread(target=self._run, name='ci-traceback-diagnostic', daemon=True)
            self.thread.start()
        except BaseException:
            os.close(self.fd)
            raise

    def _run(self):
        try:
            if not self.cancelled.wait(self.seconds):
                os.write(self.fd, (f'\nCI diagnostic after {self.seconds:g}s (Python watchdog):\n').encode('ascii'))
                faulthandler.dump_traceback(file=self.fd, all_threads=True)
        except BaseException:
            # Main test protocol turns diagnostic failure into a nonzero run.
            # Do not dump arbitrary exception text from a background callback.
            self.failed = True
        finally:
            try:
                os.close(self.fd)
            except BaseException:
                self.failed = True

    def stop(self):
        self.cancelled.set()
        self.thread.join(5)
        if self.thread.is_alive() or self.failed:
            raise RuntimeError('ci_traceback_diagnostic_failed')


def pytest_addoption(parser):
    parser.addini('faulthandler_timeout', 'Seconds until one diagnostic per test protocol', default='0')
    parser.addini('faulthandler_exit_on_timeout', 'Unsupported by Python diagnostic watchdog',
                  type='bool', default=False)


def pytest_configure(config):
    if config.pluginmanager.hasplugin('faulthandler'):
        raise pytest.UsageError('Use -p no:faulthandler with tests.ci_thread_dump')
    try:
        seconds = float(config.getini('faulthandler_timeout'))
        if not math.isfinite(seconds) or seconds <= 0:
            raise ValueError
    except (TypeError, ValueError, OverflowError):
        raise pytest.UsageError('A positive finite faulthandler_timeout is required') from None
    if config.getini('faulthandler_exit_on_timeout'):
        # Never silently replace an explicitly requested hard exit with a dump.
        raise pytest.UsageError('Python watchdog cannot implement a hard timeout; use the CI job deadline')
    try:
        descriptor = sys.stderr.fileno()
        if descriptor < 0:
            raise ValueError
    except (AttributeError, ValueError):
        descriptor = sys.__stderr__.fileno()
    fd = os.dup(descriptor)
    enabled = faulthandler.is_enabled()
    try:
        faulthandler.enable(file=fd)
    except BaseException:
        os.close(fd)
        raise
    config.stash[_STATE] = dict(fd=fd, original_fd=descriptor, enabled=enabled,
                                seconds=seconds, active=None)


def _stop(config):
    state = config.stash.get(_STATE, None)
    if state is not None and state['active'] is not None:
        watcher = state['active']
        state['active'] = None
        watcher.stop()


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_protocol(item):
    state = item.config.stash[_STATE]
    if state['active'] is not None:
        raise RuntimeError('ci_traceback_protocol_overlap')
    state['active'] = Watchdog(state['seconds'], state['fd'])
    try:
        return (yield)
    finally:
        _stop(item.config)


@pytest.hookimpl(tryfirst=True)
def pytest_enter_pdb(config):
    _stop(config)


@pytest.hookimpl(tryfirst=True)
def pytest_exception_interact(node):
    _stop(node.config)


def pytest_unconfigure(config):
    state = config.stash.get(_STATE, None)
    if state is None:
        return
    try:
        _stop(config)
    finally:
        try:
            faulthandler.disable()
            if state['enabled']:
                faulthandler.enable(file=state['original_fd'])
        finally:
            os.close(state['fd'])
            del config.stash[_STATE]


def pytest_report_header(config):
    seconds = config.stash[_STATE]['seconds']
    return f'CI Python-thread traceback after {seconds:g}s; fatal handler enabled; outer deadline unchanged'
