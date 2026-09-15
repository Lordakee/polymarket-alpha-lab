"""Separate same-assistant adversarial review of first-failure preservation."""
import json
import subprocess

import pytest

from tests import handoff_process_probe as probe


@pytest.mark.parametrize('sink', ['junit', 'stdout'])
def test_diagnostic_failure_must_not_replace_original_timeout(monkeypatch, sink):
    original = subprocess.TimeoutExpired('fixture', 30, stderr=b'PAL_HANDOFF_STAGE|script_entered|0\n')
    calls = []
    def launch(*args, **kwargs): calls.append(1); raise original
    def broken(*args, **kwargs): raise OSError('private diagnostic failure')
    monkeypatch.setattr(probe.subprocess, 'run', launch)
    record = broken if sink == 'junit' else lambda *args: None
    if sink == 'stdout': monkeypatch.setattr(probe, 'print', broken, raising=False)
    with pytest.raises(subprocess.TimeoutExpired) as caught:
        probe.run_fixture('powershell.exe', 'fixture.ps1', record_property=record)
    assert caught.value is original and calls == [1]
    assert 'private' not in repr(getattr(original, '__notes__', []))


def test_missing_markers_cannot_be_labeled_a_proven_startup_failure():
    report = probe.summarize(b'unrelated private stderr', outcome='timeout', elapsed_seconds=30)
    assert report['last_observed_stage'] is None and report['root_cause_established'] is False
    assert 'private' not in json.dumps(report)


def test_terminal_marker_does_not_overrule_return_code(monkeypatch):
    finished = subprocess.CompletedProcess([], 1, '', 'PAL_HANDOFF_STAGE|serialization_returned|9\n')
    monkeypatch.setattr(probe.subprocess, 'run', lambda *a, **k: finished)
    result, report = probe.run_fixture('powershell.exe', 'fixture.ps1', record_property=lambda *a: None)
    assert result.returncode == 1 and report['root_cause_established'] is False


def test_invalid_marker_does_not_select_secret_as_last_stage():
    report = probe.summarize('PAL_HANDOFF_STAGE|script_entered|0\nPAL_HANDOFF_STAGE|private_secret|1',
                            outcome='timeout', elapsed_seconds=30)
    assert report['last_observed_stage'] == 'script_entered'
    assert report['malformed_marker_seen'] is True and 'private_secret' not in json.dumps(report)
