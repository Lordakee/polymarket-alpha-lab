# WP-06: evidence for the first test-controlled PowerShell invocation

## The defect is still open

PR #30's initial native job 104082175714 (run 34875688580) failed the
unchanged `success-powershell.exe` handoff test at its 30-second deadline.
A later same-head pass did not establish a root cause. This change adds
focused test evidence for that specific release limitation. It does not claim
to repair Windows startup or to complete WP-06/G6 or V1.

The production `scripts/download_handoff.ps1` is byte-identical. No module path,
profile, execution policy, antivirus, ACL, cache, network configuration or timeout
is changed. There is no prewarming or retry. No user-machine command is required.

## What the test records

The existing synthetic PowerShell harness emits fixed stage names and elapsed
milliseconds to stderr using .NET, beginning before its first cmdlet. Stages cover
script entry, encoding setup, helper import, mock manifest/payload reads, helper
return and JSON serialization. The production helper remains uninstrumented and
HTTP remains replaced by the existing fixture bytes; no actual download occurs.
All prior success, hash, path, partial-transfer and preservation assertions remain.
Complete expected stage sequences are now required in addition to those assertions.
The hash test also records its entry/return and checks the released file handle.

The Python test helper publishes a bounded, fixed-vocabulary summary to the test
log and JUnit property `handoff_process`. It accepts both bytes and text from
TimeoutExpired, and never copies unknown stage names, other stderr text, stdout,
command arguments, environment values or raw fixture bodies into that summary.
Original pytest failure objects are retained; this is not a promise that arbitrary
raw pytest output is private-data-safe. Only synthetic tests use this helper.
Both native and first-invocation CI explicitly use pytest
`junit_family=legacy`, whose per-case properties support this evidence. The
initial candidate kept the native default xunit2 and emitted compatibility
warnings; its XML was readable, but no strict-xunit2 schema conformity was
claimed. The explicit format fixes that newly introduced warning without
changing test selection, assertions, process limits or production code.

TimeoutExpired, launch failure and interruption remain failures. Even a final
serialization marker does not override a nonzero exit code or process timeout.
A failure of the diagnostic sink must not replace the primary process exception;
only a fixed diagnostic-unavailable note is added. On an otherwise completed
process, a diagnostic sink error still fails the test rather than claiming complete
evidence. The original 30-second subprocess contract and invocation arguments
remain unchanged. Python notes that process creation itself may not be interruptible
on some platforms; this is not a newly promised universal wall-clock deadline.

## Reading incomplete evidence

| Last observed stage | What is known, not a root-cause finding |
| --- | --- |
| None | No fixture marker was observed. This alone does not prove a Windows startup fault. |
| `script_entered` or `encoding_ready` | The child entered the script; setup/import has not yet been observed complete. |
| `helper_loaded` or `invoke_entered` | The source helper loaded; the reported later operation has not completed. |
| `manifest_returned` | Mock manifest bytes were written; validation/next-stage completion remains unknown. |
| `payload_returned` | Mock payload bytes were written; hash/publication/return may still be outstanding. |
| `invoke_returned` | The helper returned; JSON serialization and process exit are separately observed. |
| `serialization_returned` | Serialization finished in the child; a later timeout still fails and can involve exit/pipe draining. |

Markers are observations, not authenticated tracing or proof of causality.
`root_cause_established=false` is retained on all summaries. Instrumentation can
itself perturb timing. Neither a fast observed run nor three passes closes the
original intermittent defect. Source-faithful failing evidence is required before
choosing a runtime/environment repair; do not guess at certificate checks or
module caches and disable them to obtain green.

## Fixed CI experiment

`handoff-first-run.yml` declares three independent Windows runner jobs BEFORE
execution, with fail-fast disabled so one failed trial does not erase the others.
Each runs the original PS5.1 success test as its FIRST test-controlled PS5.1
invocation, then the offline probe contracts and a deliberate negative timeout
fixture. The latter enters its script and sleeps beyond the unchanged 30-second
limit: the real TimeoutExpired must retain that first marker. This is an injected
wait AFTER the first trial, not a reproduction or retry of the intermittent defect. They are not retries of a failure.
No other test-controlled PS5.1 process is launched first. Runner provisioning and
GitHub action internals are outside this assertion; this is not proof that the
entire VM has never run PowerShell. Setup uses the same pinned actions and locked
Python environment as the original native workflow, not a tweaked module path.

Missing Windows test shells are errors when `PAL_REQUIRE_HANDOFF_SHELLS=1`;
optional local shell testing otherwise retains its old skip behavior. The normal
native workflow keeps all existing cases and its original timeout, and also
requires shells. All original 18 PS5.1/PS7 cases still run there. Helper-only
changes trigger that workflow as well as the three-trial experiment.

Artifacts contain the synthetic log and JUnit, uploaded even on failure. Record
all three trial outcomes, their run attempts, the exact head/tree and original
native regression separately; never select only a successful trial or sum
repeated test counts. Actions artifacts expire after seven days. Relevant fixed
review summaries must be retained in GitHub, not described as a permanent Release.

Local offline commands (not Windows execution evidence):

```bash
python -m pytest -q tests/test_handoff_process_probe.py tests/test_handoff_process_probe_review.py tests/test_handoff_download.py
```

The real shell tests skip on non-Windows. This is test infrastructure, not a new
application report, business persistence layer, user diagnostic script or service.
No provider, database, credentials, real market call or installed kit is touched.

Primary reference: https://docs.python.org/3/library/subprocess.html
(`run`, `TimeoutExpired`, process-creation timeout caveat; checked 2026-09-16).

JUnit property/family reference (checked 2026-09-16):
https://docs.pytest.org/en/stable/_modules/_pytest/junitxml.html
