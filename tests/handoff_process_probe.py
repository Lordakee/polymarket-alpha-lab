"""Test-only fixed-stage evidence for the unchanged 30s PowerShell process limit.

Never reads process environments, loads modules, prewarms a shell or retries.
Only fixed marker names and durations reach JUnit; raw output stays with pytest.
"""
from __future__ import annotations

import json
import re
import subprocess
from time import monotonic

TIMEOUT_SECONDS = 30
MAX_TRACE_CHARS = 65536
STAGES = frozenset((
    'script_entered', 'encoding_ready', 'helper_loaded', 'invoke_entered',
    'manifest_entered', 'manifest_returned', 'payload_entered', 'payload_returned',
    'partial_expected', 'invoke_returned', 'hash_entered', 'hash_returned',
    'serialization_entered', 'serialization_returned',
))

# This runs inside a synthetic test child, NOT the downloaded production helper.
# Use .NET only so the first marker does not depend on cmdlet/module autoloading.
POWERSHELL_PROBE = """
$ProbeClock = [Diagnostics.Stopwatch]::StartNew()
function Write-HandoffProbe([string]$Stage) {
    [Console]::Error.WriteLine(('PAL_HANDOFF_STAGE|' + $Stage + '|' + $ProbeClock.ElapsedMilliseconds))
    [Console]::Error.Flush()
}
Write-HandoffProbe 'script_entered'
"""


def summarize(stderr, *, outcome: str, elapsed_seconds: float) -> dict:
    """Do not infer a root cause from the last observed marker or its absence."""
    if outcome not in ('returned', 'timeout', 'launch_failed', 'interrupted'):
        raise ValueError('handoff_probe_outcome_invalid')
    if stderr is None:
        text = ''
    elif type(stderr) is bytes:
        text = stderr[:MAX_TRACE_CHARS].decode('utf-8', errors='replace')
    elif type(stderr) is str:
        text = stderr[:MAX_TRACE_CHARS]
    else:
        raise ValueError('handoff_probe_stderr_invalid')
    stages = []
    malformed = False
    for line in text.splitlines():
        if not line.startswith('PAL_HANDOFF_STAGE|'):
            continue
        match = re.fullmatch(r'PAL_HANDOFF_STAGE\|([a-z_]+)\|([0-9]{1,9})', line)
        if (match is None or match[1] not in STAGES or len(stages) >= 32
                or (stages and int(match[2]) < stages[-1]['elapsed_ms'])):
            malformed = True
            continue
        stages.append(dict(stage=match[1], elapsed_ms=int(match[2])))
    return dict(outcome=outcome, process_limit_seconds=TIMEOUT_SECONDS,
        elapsed_seconds=round(elapsed_seconds, 3), stages=stages,
        last_observed_stage=stages[-1]['stage'] if stages else None,
        trace_truncated=stderr is not None and len(stderr) > MAX_TRACE_CHARS,
        malformed_marker_seen=malformed, retry_count=0, root_cause_established=False)


def run_fixture(program, script, *, record_property):
    """Same subprocess contract as the original test; timeout remains a failure.

    TimeoutExpired can carry bytes even with text=True. Preserve the exception,
    and publish only fixed-stage evidence before re-raising. Never extend the
    deadline, repeat the process, alter module paths or turn missing output green.
    """
    started = monotonic()
    try:
        result = subprocess.run([program, '-NoProfile', '-NonInteractive', '-File', str(script)],
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=TIMEOUT_SECONDS)
    except (subprocess.TimeoutExpired, OSError, KeyboardInterrupt) as error:
        kind = ('timeout' if isinstance(error, subprocess.TimeoutExpired) else
                'interrupted' if isinstance(error, KeyboardInterrupt) else 'launch_failed')
        evidence = summarize(getattr(error, 'stderr', None), outcome=kind,
                             elapsed_seconds=monotonic()-started)
        # Secondary diagnostic failures must not replace the original failure.
        try:
            record_property('handoff_process', json.dumps(evidence, sort_keys=True))
        except Exception:
            error.add_note('handoff_probe_junit_unavailable')
        try:
            print('HANDOFF_PROCESS ' + json.dumps(evidence, sort_keys=True), flush=True)
        except Exception:
            error.add_note('handoff_probe_stdout_unavailable')
        raise
    evidence = summarize(result.stderr, outcome='returned', elapsed_seconds=monotonic()-started)
    record_property('handoff_process', json.dumps(evidence, sort_keys=True))
    print('HANDOFF_PROCESS ' + json.dumps(evidence, sort_keys=True), flush=True)
    return result, evidence
