"""Native CI inventory/aggregation contracts; no new test runner or database.

The original 51-file selection is pinned to PR48 e1e1df52. Partitioning must
retain every original file exactly once. JSON is valid YAML and lets this test
read the deliberately closed matrix without adding a YAML dependency.

Section 61 (2026-09-27) makes Linux the sole V1 platform: the real Linux
matrix job repeats the identical closed inventory under the pinned PG18 tuple
while the Windows matrix job stays byte-identical as frozen history until the
coordinator's controlled required-context replacement removes it. Both
matrices are pinned here so neither can silently drift.
"""
from collections import Counter
import json
import os
from pathlib import Path
import re
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/native-postgres.yml'
ORIGINAL_FILES = """tests/test_project_postgres.py
tests/test_project_postgres_platform.py
tests/test_project_postgres_publication.py
tests/test_project_postgres_publication_native.py
tests/test_project_postgres_migration_compat.py
tests/test_project_postgres_native.py
tests/test_project_postgres_backup.py
tests/test_project_postgres_backup_zip.py
tests/test_project_postgres_backup_native.py
tests/test_project_postgres_resolution_native.py
tests/test_research_resolution.py
tests/test_research_resolution_store.py
tests/test_research_resolution_cli.py
tests/test_research_resolution_inspection_cli.py
tests/test_research_resolution_queue.py
tests/test_research_resolution_poll.py
tests/test_project_postgres_resolution_queue_native.py
tests/test_research_crypto_launch.py
tests/test_crypto_contract_scope.py
tests/test_crypto_observation_time.py
tests/test_research_evidence_timezones.py
tests/test_research_scope_instants.py
tests/test_research_record_timezone_codec.py
tests/test_project_postgres_crypto_launch_native.py
tests/test_public_http.py
tests/test_research_crypto_discovery.py
tests/test_crypto_supported_selection.py
tests/test_handoff_download.py
tests/test_research_evaluation_cli.py
tests/test_research_execution_cli.py
tests/test_research_execution_inventory.py
tests/test_research_inventory_cli.py
tests/test_project_postgres_inventory_native.py
tests/test_research_dispatch.py
tests/test_project_postgres_dispatch_native.py
tests/test_research_dispatch_rotation.py
tests/test_project_postgres_rotation_native.py
tests/test_research_model_budget.py
tests/test_project_postgres_budget_native.py
tests/test_research_dispatch_cli.py
tests/test_research_dispatch_cli_review.py
tests/test_project_postgres_dispatch_cli_native.py
tests/test_research_resolution_confirmation.py
tests/test_research_resolution_confirmation_review.py
tests/test_project_postgres_confirmation_native.py
tests/test_ci_thread_dump.py
tests/test_ci_thread_dump_review.py
tests/test_research_resolution_output.py
tests/test_research_resolution_output_review.py
tests/test_project_postgres_backup_catalog.py
tests/test_project_postgres_backup_catalog_review.py""".splitlines()
SELF = 'tests/test_native_postgres_workflow.py'
# PR47 adds two explicit modules; preserve ORIGINAL_FILES as the pinned baseline.
ADMISSION_FILES = (
    'tests/test_research_dispatch_cli_admission.py',
    'tests/test_research_dispatch_cli_admission_review.py',
)


# Explicit WP02 additions; every original selector remains unchanged.
UNCAPPED_FILES = ('tests/test_research_uncapped.py', 'tests/test_research_codex_exec.py', 'tests/test_research_codex_uncapped_review.py', 'tests/test_project_postgres_uncapped_native.py')
AUDIT_FILES = ('tests/test_research_uncapped_audit.py',
               'tests/test_research_uncapped_audit_review.py',
               'tests/test_project_postgres_uncapped_audit_native.py')

PROCESS_FILES = ('tests/test_research_process.py', 'tests/test_research_process_review.py',
                 'tests/test_research_codex_process.py')

PROFILE_FILES = ('tests/test_research_codex_profile.py',
                 'tests/test_research_codex_profile_review.py')

CLAUDE_FILES = ('tests/test_research_claude_exec.py', 'tests/test_research_claude_profile.py', 'tests/test_research_claude_review.py')

CLAUDE_PROBE_FILES = ('tests/test_claude_cli_probe.py', 'tests/test_claude_cli_probe_review.py')

EXPECTED_INVENTORY = Counter([*ORIGINAL_FILES, SELF, *ADMISSION_FILES, *UNCAPPED_FILES,
                              *AUDIT_FILES, *PROCESS_FILES, *PROFILE_FILES, *CLAUDE_FILES,
                              *CLAUDE_PROBE_FILES])


def matrices(source):
    """Every closed matrix include block, each immediately followed by runs-on."""
    blocks, rest = [], source
    while True:
        _, separator, rest = rest.partition('        include: ')
        if not separator:
            return blocks
        value, end = json.JSONDecoder().raw_decode(rest)
        assert rest[end:].lstrip().startswith('runs-on:')
        blocks.append(value)


def validated(value):
    assert type(value) is list and len(value) == 3
    assert [p['partition'] for p in value] == ['storage', 'research', 'dispatch']
    for partition in value:
        assert set(partition) == {'partition', 'files'}
        assert type(partition['files']) is list and partition['files']
        assert all(type(f) is str and re.fullmatch(r'tests/test_[a-z0-9_]+[.]py', f)
                   for f in partition['files'])
    assert Counter(f for p in value for f in p['files']) == EXPECTED_INVENTORY
    return value


def jobs(text):
    """Split the workflow's jobs section into per-job chunks keyed by job id.

    Two-space comment lines belong to the section or the following job, never
    to the tail of the previous job; deeper-indented comments stay inside
    their job. Keys outside `jobs:` (for example `on.pull_request`) are
    ignored.
    """
    chunks: dict[str, list[str]] = {}
    current: list[str] | None = None
    in_jobs = False
    for line in text.splitlines(keepends=True):
        if re.match(r'^jobs:\s*$', line):
            in_jobs, current = True, None
            continue
        if not in_jobs:
            continue
        matched = re.match(r'^  ([A-Za-z0-9_-]+):\s*$', line)
        if matched:
            current = chunks.setdefault(matched.group(1), [])
        elif re.match(r'^  #', line):
            current = None
        elif current is not None:
            current.append(line)
    return {key: ''.join(value) for key, value in chunks.items()}


def test_native_partitions_preserve_exact_original_inventory():
    text = WORKFLOW.read_text()
    blocks = matrices(text)
    # The frozen Windows matrix and the new Linux matrix must each be complete,
    # closed and identical: no platform may drop or duplicate scenario coverage.
    assert len(blocks) == 2
    for block in blocks:
        parts = validated(block)
        assert len(ORIGINAL_FILES) == len(set(ORIGINAL_FILES)) == 51
        assert set(ADMISSION_FILES) <= set(parts[2]['files'])
        assert set(UNCAPPED_FILES) <= set(parts[2]['files'])
        assert set(AUDIT_FILES) <= set(parts[2]['files'])
        assert set(PROCESS_FILES) <= set(parts[2]['files'])
        assert set(PROFILE_FILES) <= set(parts[2]['files'])
        assert set(CLAUDE_FILES) <= set(parts[2]['files'])
        assert set(CLAUDE_PROBE_FILES) <= set(parts[2]['files'])
        for part in parts:
            assert all((ROOT / path).is_file() for path in part['files'])
        # Both new unit modules and the REAL backup proof stay together on the
        # storage partition of every platform matrix.
        assert {'tests/test_project_postgres_backup_native.py',
                'tests/test_project_postgres_backup_catalog.py',
                'tests/test_project_postgres_backup_catalog_review.py'} <= set(parts[0]['files'])
    assert validated(blocks[0]) == validated(blocks[1])


def test_native_partition_limits_and_failure_policy_are_explicit():
    text = WORKFLOW.read_text()
    worker, gate = jobs(text)['windows-native-part'], jobs(text)['windows-native']
    assert '      fail-fast: false\n' in worker
    assert '    timeout-minutes: 20\n' in worker
    assert '    runs-on: windows-2025\n' in worker
    assert 'continue-on-error' not in text
    # Section 61 controlled CI transition (2026-09-28): the Windows matrix and
    # its summary gate are retired as visible frozen history; a skipped input
    # would fail an always() gate, so both carry if: false.
    assert "if: false  # retired 2026-09-28 per DELIVERY_PLAN.md section 61" in worker
    assert gate.startswith(
        '    if: false  # retired 2026-09-28 with windows-native-part')
    assert '    needs: [windows-native-part]\n' in gate
    assert 'NATIVE_RESULT: ${{ needs.windows-native-part.result }}' in gate
    assert '    timeout-minutes: 2\n' in gate
    assert gate.count('run: |') == 1
    assert 'test "$NATIVE_RESULT" = success' in gate


def test_linux_partitions_and_pg18_prefix_are_explicit():
    text = WORKFLOW.read_text()
    worker, gate = jobs(text)['linux-native-part'], jobs(text)['linux-native']
    assert '      fail-fast: false\n' in worker
    assert '    timeout-minutes: 40\n' in worker
    assert '    runs-on: ubuntu-24.04\n' in worker
    assert 'continue-on-error' not in text
    # The qualified package-to-prefix assembly: pinned apt PostgreSQL 18 only,
    # binaries-only, no symlinks, notices preserved, no installed data used.
    assert 'noble-pgdg main' in worker and 'postgresql-18' in worker
    assert '/usr/lib/postgresql/18/bin "$PREFIX/bin"' in worker
    assert '/usr/share/postgresql/18 "$PREFIX/share"' in worker
    assert 'copyright "$PREFIX/COPYRIGHT"' in worker
    assert 'find "$PREFIX" -type l | wc -l' in worker and '-eq 0' in worker
    assert 'POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX="$RUNNER_TEMP/pg18-portable-prefix"' in worker
    assert '    if: ${{ always() }}\n' in gate
    assert '    needs: [linux-native-part]\n' in gate
    assert 'NATIVE_RESULT: ${{ needs.linux-native-part.result }}' in gate
    assert '    timeout-minutes: 2\n' in gate
    assert gate.count('run: |') == 1
    assert 'test "$NATIVE_RESULT" = success' in gate


def test_original_native_options_and_cleanliness_remain_required():
    text = WORKFLOW.read_text()
    assert 'uv sync --locked --extra dev --extra postgres --python 3.12' in text
    assert '-p no:faulthandler -p tests.ci_thread_dump -q -s -o junit_family=legacy -o faulthandler_timeout=120 @testFiles --durations=20' in text
    assert "NATIVE_TEST_FILES: ${{ join(matrix.files, ' ') }}" in text
    assert "$testFiles = $env:NATIVE_TEST_FILES -split ' '" in text
    for name in ('POLYMARKET_ALPHA_LAB_RUN_NATIVE_PROJECT_POSTGRES',
                 'POLYMARKET_ALPHA_LAB_RUN_NATIVE_BACKUP', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD',
                 'PYTHONUTF8', 'PAL_REQUIRE_HANDOFF_SHELLS'):
        assert f"$env:{name} = '1'" in text
    assert "Remove-Item ('Env:' + $_.Name)" in text
    assert 'git diff --check\n          git diff --exit-code' in text
    assert '$code = $LASTEXITCODE\n          exit $code' in text
    assert 'permissions:\n  contents: read\n' in text
    assert 'persist-credentials: false' in text
    assert 'enable-cache: false' in text


def test_linux_native_options_and_cleanliness_remain_required():
    worker = jobs(WORKFLOW.read_text())['linux-native-part']
    assert 'uv sync --locked --extra dev --extra postgres --python 3.12' in worker
    assert '-p no:faulthandler -p tests.ci_thread_dump -q -s -o junit_family=legacy -o faulthandler_timeout=120 $NATIVE_TEST_FILES --durations=20' in worker
    assert "NATIVE_TEST_FILES: ${{ join(matrix.files, ' ') }}" in worker
    for name in ('POLYMARKET_ALPHA_LAB_RUN_NATIVE_PROJECT_POSTGRES',
                 'POLYMARKET_ALPHA_LAB_RUN_NATIVE_BACKUP', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD',
                 'PYTHONUTF8', 'PAL_REQUIRE_HANDOFF_SHELLS'):
        assert f'export {name}=1' in worker
    assert 'for variable in $(compgen -e PG); do unset "$variable"; done' in worker
    assert '.venv/bin/python -u -m pytest' in worker
    assert 'test ${PIPESTATUS[0]} -eq 0' in worker
    assert 'git diff --check\n          git diff --exit-code' in worker
    assert 'persist-credentials: false' in worker
    assert 'enable-cache: false' in worker
    assert 'fetch-depth: 0\n' in worker


def test_each_partition_retains_distinct_failure_artifacts():
    text = WORKFLOW.read_text()
    assert 'if: always()' in text
    assert 'name: native-postgres-proof-${{ matrix.partition }}-${{ github.sha }}' in text
    assert 'name: native-postgres-linux-proof-${{ matrix.partition }}-${{ github.sha }}' in text
    assert '${{ runner.temp }}/native-proof.log' in text
    assert '${{ runner.temp }}/native-proof.xml' in text
    assert 'if-no-files-found: error' in text
    assert "      - 'tests/test_native_postgres_workflow*.py'" in text


@pytest.mark.parametrize('gate_job', ['windows-native', 'linux-native'])
@pytest.mark.parametrize('result', ['success', 'failure', 'cancelled', 'skipped', ''])
def test_aggregate_shell_only_accepts_complete_success(gate_job, result):
    # On POSIX execute the actual aggregate body. Both hosted aggregates are
    # Ubuntu; Windows validates its exact body instead of invoking Git
    # Bash/MSYS implicitly.
    gate = jobs(WORKFLOW.read_text())[gate_job]
    script = '\n'.join(line[10:] for line in gate.split('        run: |\n', 1)[1].splitlines())
    assert script == 'set -euo pipefail\ntest "$NATIVE_RESULT" = success'
    if os.name != 'nt':
        done = subprocess.run(['/bin/bash', '-c', script], env={'NATIVE_RESULT': result},
                              stdin=subprocess.DEVNULL, capture_output=True, timeout=5)
        assert done.returncode == (0 if result == 'success' else 1)
        assert done.stdout == done.stderr == b''


@pytest.mark.parametrize('change', ['missing', 'duplicate', 'selector', 'unknown-partition',
                                    'linux-missing', 'linux-unknown-partition'])
def test_partition_inventory_rejects_silent_coverage_changes(change):
    text = WORKFLOW.read_text()
    if change == 'missing':
        text = text.replace('            "tests/test_project_postgres_backup_native.py",\n', '', 1)
    elif change == 'duplicate':
        text = text.replace('"tests/test_project_postgres_backup.py"', '"tests/test_project_postgres_backup_native.py"', 1)
    elif change == 'selector':
        text = text.replace('"tests/test_project_postgres_backup_native.py"', '"tests/test_project_postgres_backup_native.py::test_selected"', 1)
    elif change == 'unknown-partition':
        text = text.replace('"partition": "storage"', '"partition": "unknown"', 1)
    elif change == 'linux-missing':
        head, separator, tail = text.partition('  linux-native-part:')
        assert separator
        text = head + separator + tail.replace(
            '            "tests/test_project_postgres_backup_native.py",\n', '', 1)
    else:
        head, separator, tail = text.partition('  linux-native-part:')
        assert separator
        text = head + separator + tail.replace('"partition": "storage"', '"partition": "unknown"', 1)
    with pytest.raises((AssertionError, ValueError)):
        for block in matrices(text):
            validated(block)
