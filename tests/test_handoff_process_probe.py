"""Offline evidence contracts; no PowerShell, HTTP or local user data."""
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from tests import handoff_process_probe as probe

MARKER = 'PAL_HANDOFF_STAGE|script_entered|0\n'


@pytest.mark.parametrize('value', [None, b'', '', MARKER, MARKER.encode()])
def test_stderr_text_bytes_and_missing_are_supported(value):
    result = probe.summarize(value, outcome='timeout', elapsed_seconds=30.1)
    assert result['last_observed_stage'] == ('script_entered' if value else None)
    assert result['root_cause_established'] is False
    assert result['retry_count'] == 0 and result['process_limit_seconds'] == 30


@pytest.mark.parametrize('line', [
    'PAL_HANDOFF_STAGE|secret-sentinel|1', 'PAL_HANDOFF_STAGE|script_entered|-1',
    'PAL_HANDOFF_STAGE|script_entered|NaN', 'PAL_HANDOFF_STAGE|script_entered|1|secret-sentinel',
    'PAL_HANDOFF_STAGE|script_entered|1000000000',
])
def test_unknown_or_malformed_markers_never_echo_untrusted_strings(line):
    result = probe.summarize(line, outcome='timeout', elapsed_seconds=30)
    assert result['stages'] == [] and result['malformed_marker_seen'] is True
    assert 'secret-sentinel' not in json.dumps(result)


def test_nonmarker_stderr_and_output_limit_are_not_copied():
    value = 'secret-sentinel\n' + MARKER + ('x' * probe.MAX_TRACE_CHARS)
    result = probe.summarize(value, outcome='returned', elapsed_seconds=1)
    assert result['trace_truncated'] is True
    assert 'secret-sentinel' not in json.dumps(result)


def test_nonmonotonic_or_excessive_stages_are_visible_as_invalid():
    value = MARKER + 'PAL_HANDOFF_STAGE|helper_loaded|2\nPAL_HANDOFF_STAGE|invoke_entered|1\n'
    result = probe.summarize(value, outcome='timeout', elapsed_seconds=30)
    assert result['last_observed_stage'] == 'helper_loaded' and result['malformed_marker_seen']
    result = probe.summarize(MARKER*33, outcome='returned', elapsed_seconds=1)
    assert len(result['stages']) == 32 and result['malformed_marker_seen']


def test_returned_process_retains_exact_command_deadline_and_original_output(monkeypatch):
    calls = []
    finished = subprocess.CompletedProcess([], 7, 'original-json', MARKER)
    def launch(args, **kwargs):
        calls.append((args, kwargs)); return finished
    monkeypatch.setattr(probe.subprocess, 'run', launch)
    properties = []
    got, result = probe.run_fixture('powershell.exe', Path('fixture.ps1'),
                                   record_property=lambda *args: properties.append(args))
    assert got is finished and result['outcome'] == 'returned'
    assert calls == [(['powershell.exe', '-NoProfile', '-NonInteractive', '-File', 'fixture.ps1'],
                     dict(capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30))]
    assert len(properties) == 1 and properties[0][0] == 'handoff_process'


@pytest.mark.parametrize('error,kind', [
    (subprocess.TimeoutExpired('fixture', 30, output=b'private-stdout', stderr=MARKER.encode()), 'timeout'),
    (OSError('private-launch-error'), 'launch_failed'),
    (KeyboardInterrupt('private-interrupt'), 'interrupted'),
], ids=['timeout-bytes', 'launch-error', 'interrupted'])
def test_original_failure_propagates_once_with_fixed_evidence(monkeypatch, capsys, error, kind):
    calls = []
    def launch(*args, **kwargs): calls.append(1); raise error
    monkeypatch.setattr(probe.subprocess, 'run', launch)
    properties = []
    with pytest.raises(type(error)) as caught:
        probe.run_fixture('powershell.exe', 'fixture.ps1', record_property=lambda *x: properties.append(x))
    assert caught.value is error and calls == [1]
    result = json.loads(properties[0][1])
    assert result['outcome'] == kind and result['root_cause_established'] is False
    output = capsys.readouterr().out
    assert 'private-' not in output


def test_complete_serialization_marker_does_not_make_timeout_a_pass(monkeypatch):
    error = subprocess.TimeoutExpired('fixture', 30, stderr=MARKER +
                                     'PAL_HANDOFF_STAGE|serialization_returned|10\n')
    def launch(*args, **kwargs): raise error
    monkeypatch.setattr(probe.subprocess, 'run', launch)
    properties = []
    with pytest.raises(subprocess.TimeoutExpired):
        probe.run_fixture('powershell.exe', 'fixture.ps1', record_property=lambda *x: properties.append(x))
    result = json.loads(properties[0][1])
    assert result['outcome'] == 'timeout'
    assert result['last_observed_stage'] == 'serialization_returned'


def test_required_missing_shell_fails_instead_of_becoming_ci_skip(monkeypatch, tmp_path):
    from tests import test_handoff_download as target
    monkeypatch.setattr(target, 'os', SimpleNamespace(name='nt', environ={'PAL_REQUIRE_HANDOFF_SHELLS': '1'}))
    monkeypatch.setattr(target.shutil, 'which', lambda _: None)
    with pytest.raises(pytest.fail.Exception, match='required Windows handoff shell'):
        target.test_real_powershell_download_publication(tmp_path, 'powershell.exe', 'success', lambda *a: None)
    with pytest.raises(pytest.fail.Exception, match='required Windows handoff shell'):
        target.test_dotnet_hash_is_exact_unicode_safe_and_releases_file(tmp_path, 'pwsh', lambda *a: None)


def test_original_script_bytes_and_probe_keep_no_execution_policy_override():
    assert probe.POWERSHELL_PROBE.isascii()
    assert 'ConvertTo-Json' not in probe.POWERSHELL_PROBE
    assert 'Write-Output' not in probe.POWERSHELL_PROBE
    assert 'ExecutionPolicy' not in probe.POWERSHELL_PROBE
