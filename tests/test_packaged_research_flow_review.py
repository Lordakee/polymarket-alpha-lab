"""Separate same-assistant adversarial checks of test-evidence boundaries."""
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from tests import packaged_research_flow as flow


@pytest.mark.parametrize('origin', ['other/src/mod.py', 'kit-sibling/src/mod.py'])
def test_foreign_or_similarly_named_root_cannot_count_as_kit_source(monkeypatch, tmp_path, origin):
    module = SimpleNamespace(__file__=str(tmp_path/origin))
    monkeypatch.setattr(flow, 'sys', SimpleNamespace(modules={'polymarket_alpha_lab.fake': module}))
    with pytest.raises(AssertionError, match='checkout code used'):
        flow.assert_origins(tmp_path/'kit')


def test_no_project_modules_is_not_a_successful_origin_check(monkeypatch, tmp_path):
    monkeypatch.setattr(flow, 'sys', SimpleNamespace(modules={}))
    with pytest.raises(AssertionError, match='no project modules'):
        flow.assert_origins(tmp_path)


def test_recipe_timeout_is_preserved_without_retry(monkeypatch, tmp_path):
    original = subprocess.TimeoutExpired('synthetic', 300)
    calls = []
    def fail(*args, **kwargs):
        calls.append(1); raise original
    monkeypatch.setattr(flow.subprocess, 'run', fail)
    with pytest.raises(subprocess.TimeoutExpired) as caught:
        flow.run_packaged_recipe(tmp_path, sys.executable, tmp_path)
    assert caught.value is original and calls == [1]


def test_missing_kit_cannot_use_installed_checkout_or_start_database(tmp_path):
    root = tmp_path/'missing-kit'; root.mkdir()
    before = list(root.iterdir())
    result = flow.run_packaged_recipe(root, sys.executable, tmp_path)
    assert result.returncode != 0 and 'kit source missing' in result.stderr
    assert 'packaged_flow_verified' not in result.stdout
    assert list(root.iterdir()) == before


def test_read_failure_does_not_launch_an_empty_recipe(monkeypatch, tmp_path):
    def fail(*args, **kwargs): raise OSError('synthetic fixture unavailable')
    monkeypatch.setattr(Path, 'read_text', fail)
    monkeypatch.setattr(flow.subprocess, 'run', lambda *a, **k: pytest.fail('empty recipe launched'))
    with pytest.raises(OSError, match='synthetic fixture unavailable'):
        flow.run_packaged_recipe(tmp_path, sys.executable, tmp_path)


def test_short_confirmation_sink_is_byte_exact_under_windows_text_translation(monkeypatch, tmp_path):
    """Model Windows text newlines without pretending to run Windows here."""
    import io
    import json
    import runpy

    root = tmp_path / 'kit'
    package = root / 'src/polymarket_alpha_lab'
    package.mkdir(parents=True)
    (package / '__init__.py').write_bytes(b'')
    class WindowsOutput:
        def __init__(self): self.buffer = io.BytesIO()
        def write(self, text):
            self.buffer.write(text.replace('\n', '\r\n').encode('utf-8'))
            return len(text)
        def flush(self): self.buffer.flush()
    output = WindowsOutput()
    body = json.dumps(dict(operation='confirm_crypto_resolution',
                           status='recorded_operator_confirmation'), indent=2) + '\n'
    def execute(script, *, run_name):
        assert Path(script) == root / 'scripts/review_resolution_queue.py'
        assert run_name == '__main__'
        assert sys.stdout.write(body) == 10
        raise SystemExit(1)
    with monkeypatch.context() as patch:
        patch.setattr(sys, 'stdout', output)
        patch.setattr(sys, 'argv', ['fixture', str(root)])
        patch.setattr(sys, 'path', list(sys.path))
        patch.setattr(runpy, 'run_path', execute)
        with pytest.raises(SystemExit) as exit:
            exec(flow._CONFIRM_SHORT_OUTPUT, {})
        assert exit.value.code == 1
    assert output.buffer.getvalue() == b'{\n  "opera'


@pytest.mark.parametrize('result', [
    subprocess.CompletedProcess([], 0, b'{\n  "opera', b''),
    subprocess.CompletedProcess([], 1, b'', b''),
    subprocess.CompletedProcess([], 1, b'{\n  "opera', b'error'),
    subprocess.CompletedProcess([], 1, b'{\n  "statu', b''),
], ids=['zero-exit', 'no-success-witness', 'stderr', 'wrong-prefix'])
def test_short_confirmation_refuses_false_process_witness(monkeypatch, tmp_path, result):
    calls = []
    def run(*args, **kwargs): calls.append(1); return result
    monkeypatch.setattr(flow.subprocess, 'run', run)
    with pytest.raises(AssertionError):
        flow.run_confirmation_output_failure(tmp_path, b'synthetic')
    assert calls == [1]


def test_confirmation_failure_probe_uses_one_kit_process_and_original_bytes(monkeypatch, tmp_path):
    calls = []
    result = subprocess.CompletedProcess([], 1, b'{\n  "opera', b'')
    payload = b'{"synthetic":"unchanged"}'
    def run(*args, **kwargs): calls.append((args, kwargs)); return result
    monkeypatch.setattr(flow.subprocess, 'run', run)
    assert flow.run_confirmation_output_failure(tmp_path, payload) is result
    args, kwargs = calls[0]
    assert args[0] == [sys.executable, '-I', '-c', flow._CONFIRM_SHORT_OUTPUT, str(tmp_path)]
    assert kwargs['input'] is payload and kwargs['timeout'] == 60
    assert kwargs['cwd'] == tmp_path.parent and kwargs['shell'] is False
    assert kwargs['check'] is False and kwargs['capture_output'] is True
    assert len(calls) == 1


def test_confirmation_failure_probe_does_not_retry_timeout(monkeypatch, tmp_path):
    original = subprocess.TimeoutExpired('synthetic', 60)
    calls = []
    def run(*args, **kwargs): calls.append(1); raise original
    monkeypatch.setattr(flow.subprocess, 'run', run)
    with pytest.raises(subprocess.TimeoutExpired) as caught:
        flow.run_confirmation_output_failure(tmp_path, b'synthetic')
    assert caught.value is original and calls == [1]


def test_injected_recipe_fits_windows_process_command_line(monkeypatch, tmp_path):
    commands = []
    monkeypatch.setattr(flow.subprocess, 'run', lambda args, **kw: commands.append(args))
    root = tmp_path / ('k'*160)
    flow.run_packaged_recipe(root, root / '.venv/Scripts/python.exe', tmp_path)
    # CreateProcessW includes the terminating NUL in its 32767-character limit.
    # This is a bounded representative path probe, not an arbitrary-path guarantee.
    units = len(subprocess.list2cmdline(commands[0]).encode('utf-16-le')) // 2 + 1
    assert units < 32767


class _FirstApprovedAdmission(Exception):
    """Stop the offline ordering probe before any positive storage/model work."""


def _admission_order_probe(monkeypatch, tmp_path, second, *, fail_call=None):
    from contextlib import contextmanager
    from datetime import UTC, datetime, timedelta
    import json

    start = datetime(2026, 9, 19, 10, 0, second, tzinfo=UTC)
    state = dict(now=start, running=False, prepared=[], commands=[])
    class Clock(datetime):
        @classmethod
        def now(cls, zone=None):
            assert zone is UTC
            return state['now']
    original = flow.prepared
    def prepare(at, opening, **kwargs):
        rows = original(at, opening, **kwargs)
        state['prepared'].append((kwargs.get('namespace', 'packaged'), at, opening, rows))
        return rows
    class Database:
        def status(self): return {'status': 'running' if state['running'] else 'stopped'}
        def _state(self): return {'instance_id': 'synthetic'}
        def up(self): state['running'] = True; return self.status()
        def down(self): state['running'] = False
        @contextmanager
        def session(self):
            yield SimpleNamespace(execution_inventory=lambda: SimpleNamespace(
                to_dict=lambda: {'claim_count': 0}))
    def command(args, **kwargs):
        assert Path(args[2]).name == 'manage_research_tasks.py'
        operation = args[5]
        assert kwargs['timeout'] == 60 and kwargs['check'] is False
        assert kwargs['capture_output'] is True
        if '--allow-queue-write' in args or '--allow-budget-write' in args:
            state['positive_payload'] = kwargs['input']
            raise _FirstApprovedAdmission
        index = len(state['commands'])
        state['commands'].append((operation, kwargs['input']))
        # Only the offline probe advances time. Native recipe uses real UTC.
        state['now'] += timedelta(seconds=8)
        if index == fail_call:
            return subprocess.CompletedProcess(args, 99, b'{}', b'')
        denied = operation in ('enqueue-batch', 'create-budget')
        data = {'operation_entered': False, 'business_writes_possible': False} if denied else {'result': None}
        return subprocess.CompletedProcess(args, 2 if denied else 3, json.dumps(data).encode(), b'')
    monkeypatch.setattr(flow, 'datetime', Clock)
    monkeypatch.setattr(flow, 'prepared', prepare)
    monkeypatch.setattr(flow, 'ProjectPostgres', lambda _: Database())
    monkeypatch.setattr(flow.distribution, 'verify_distribution', lambda _: {})
    monkeypatch.setattr(flow, 'assert_origins', lambda _: None)
    monkeypatch.setattr(flow.subprocess, 'run', command)
    return state, lambda: flow.run_packaged_flow(tmp_path)


@pytest.mark.parametrize('second', [0, 30, 59])
def test_negative_admission_checks_precede_original_prospective_inputs(monkeypatch, tmp_path, second):
    from datetime import timedelta
    state, run = _admission_order_probe(monkeypatch, tmp_path, second)
    with pytest.raises(_FirstApprovedAdmission):
        run()
    assert [op for op, _ in state['commands']] == [
        'enqueue-batch', 'inspect-batch', 'enqueue-batch', 'inspect-batch',
        'create-budget', 'inspect-budget']
    control, active = state['prepared']
    assert control[0] == 'admission-check' and active[0] == 'packaged'
    assert active[1] == state['now'] == control[1] + timedelta(seconds=48)
    assert active[2] == active[1].replace(second=0, microsecond=0) + timedelta(minutes=2)
    control_requests = tuple(row[0] for row in control[3])
    requests = tuple(row[0] for row in active[3])
    assert set(r.record_id for r in requests).isdisjoint(r.record_id for r in control_requests)
    assert all(r.forecast_cutoff_at == active[2]-timedelta(seconds=1) for r in requests)
    assert [r.record_id for r in requests] == ['packaged-0', 'packaged-1', 'packaged-2', 'packaged-3']
    assert state['commands'][0][1] == flow.ResearchBatch(flow.BATCHES[0], control_requests[::2]).payload.encode()
    assert state['positive_payload'] == flow.ResearchBatch(flow.BATCHES[0], requests[::2]).payload.encode()
    assert state['running'] is False


@pytest.mark.parametrize('fail_call', range(6))
def test_failed_negative_admission_check_never_creates_original_inputs(monkeypatch, tmp_path, fail_call):
    state, run = _admission_order_probe(monkeypatch, tmp_path, 59, fail_call=fail_call)
    with pytest.raises(AssertionError):
        run()
    assert [entry[0] for entry in state['prepared']] == ['admission-check']
    assert 'positive_payload' not in state and len(state['commands']) == fail_call+1
    assert state['running'] is False
