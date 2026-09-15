"""Real negative observation after the first-invocation trial, not its rerun."""
import json
import os
import shutil
import subprocess

import pytest

from tests.handoff_process_probe import POWERSHELL_PROBE, run_fixture


@pytest.mark.skipif(os.name != 'nt', reason='real PS5 timeout evidence requires Windows')
def test_real_timeout_preserves_entered_stage(tmp_path, record_property):
    program = shutil.which('powershell.exe')
    if not program:
        pytest.fail('required PS5 shell is missing for timeout proof')
    fixture = tmp_path / 'controlled-wait.ps1'
    fixture.write_text(POWERSHELL_PROBE + "\n[Threading.Thread]::Sleep(60000)\n", encoding='ascii')
    properties = []
    def record(name, value):
        properties.append((name, value))
        record_property(name, value)
    with pytest.raises(subprocess.TimeoutExpired) as caught:
        run_fixture(program, fixture, record_property=record)
    assert caught.value.timeout == 30
    assert len(properties) == 1
    evidence = json.loads(properties[0][1])
    assert evidence['outcome'] == 'timeout'
    assert evidence['last_observed_stage'] == 'script_entered'
    assert evidence['stages'] == [dict(stage='script_entered', elapsed_ms=evidence['stages'][0]['elapsed_ms'])]
    assert not evidence['malformed_marker_seen'] and not evidence['trace_truncated']
    assert evidence['retry_count'] == 0 and evidence['root_cause_established'] is False
