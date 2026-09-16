"""Separate same-assistant adversarial pass over the resolution console boundary."""
from types import SimpleNamespace
import io
import json

import pytest

from polymarket_alpha_lab import research_resolution_confirmation_cli as confirmation
from tests.test_research_resolution_poll import cli
from tests.test_research_resolution_confirmation import ROOT, managed, input_bytes

PRIVATE = 'synthetic-private-resolution-boundary'


@pytest.mark.parametrize('kind', ['exit-zero', 'read-error', 'interrupt'])
def test_default_binary_input_access_cannot_escape_confirmation_guard(cli, managed, monkeypatch, capsys, kind):
    error = {'exit-zero': SystemExit(0), 'read-error': OSError(PRIVATE),
             'interrupt': KeyboardInterrupt(PRIVATE)}[kind]

    class Input:
        @property
        def buffer(self):
            raise error

    with monkeypatch.context() as patch:
        patch.setattr(cli.sys, 'stdin', Input())
        try:
            code = cli.main(['--confirm', '--allow-resolution-write'])
        except (Exception, SystemExit, KeyboardInterrupt) as escaped:
            code = ('escaped', type(escaped).__name__)
    output = capsys.readouterr()
    assert code == (130 if kind == 'interrupt' else 2)
    value = json.loads(output.out)
    assert value['result'] is None and value['business_writes_possible'] is False
    assert PRIVATE not in output.out + output.err
    assert 'root' not in managed and not managed['calls']


@pytest.mark.parametrize('fault', ['short', 'flush', 'exit-zero'])
def test_confirmation_output_failure_preserves_one_completed_operation(managed, monkeypatch, fault):
    counts = dict(write=0, flush=0)

    class Output:
        def write(self, text):
            counts['write'] += 1
            assert managed['closed']
            assert json.loads(text)['status'] == 'recorded_operator_confirmation'
            if fault == 'exit-zero':
                raise SystemExit(0)
            return len(text) - 1 if fault == 'short' else len(text)

        def flush(self):
            counts['flush'] += 1
            if fault == 'flush':
                raise OSError(PRIVATE)

    with monkeypatch.context() as patch:
        patch.setattr(confirmation.sys, 'stdout', Output())
        code = confirmation.confirm_from_stdin(root=ROOT,
            stream=io.BytesIO(input_bytes(managed['instruction'])), allow_resolution_write=True)
    assert code == 1
    assert len(managed['calls']) == 1 and managed['closed']
    assert counts == dict(write=1, flush=1 if fault == 'flush' else 0)


@pytest.mark.parametrize('kind', ['exit-zero', 'value-error', 'interrupt'])
def test_serialization_failure_emits_nothing_and_is_nonzero(monkeypatch, kind):
    error = {'exit-zero': SystemExit(0), 'value-error': ValueError(PRIVATE),
             'interrupt': KeyboardInterrupt(PRIVATE)}[kind]
    writes = []

    def serialize(*args, **kwargs):
        raise error

    with monkeypatch.context() as patch:
        patch.setattr(confirmation.json, 'dumps', serialize)
        patch.setattr(confirmation.sys, 'stdout', SimpleNamespace(write=lambda s: writes.append(s)))
        code = confirmation._emit({'status': 'example'}, 0)
    assert code == (130 if kind == 'interrupt' else 1)
    assert writes == []


@pytest.mark.parametrize('value', [None, True, -1, 100000])
def test_wrong_write_count_never_claims_complete_output(monkeypatch, value):
    writes = []
    flushed = []

    def write(text):
        writes.append(text)
        return value

    with monkeypatch.context() as patch:
        patch.setattr(confirmation.sys, 'stdout', SimpleNamespace(write=write, flush=lambda: flushed.append(1)))
        code = confirmation._emit({}, 0)
    assert code == 1 and len(writes) == 1 and not flushed


def test_success_emitter_preserves_legacy_json_and_nonzero_operation_code(monkeypatch):
    stream = io.StringIO()
    body = dict(status='failed', reason_code='resolution_queue_operation_failed')
    with monkeypatch.context() as patch:
        patch.setattr(confirmation.sys, 'stdout', stream)
        assert confirmation._emit(body, 1) == 1
    assert stream.getvalue() == json.dumps(body, ensure_ascii=True, allow_nan=False, indent=2) + '\n'


def test_default_input_is_not_resolved_without_opt_in(managed, monkeypatch, capsys):
    class Input:
        @property
        def buffer(self):
            pytest.fail('input accessed without authorization')

    with monkeypatch.context() as patch:
        patch.setattr(confirmation.sys, 'stdin', Input())
        code = confirmation.confirm_from_stdin(root=ROOT)
    assert code == 2 and not managed['calls'] and 'root' not in managed
    assert json.loads(capsys.readouterr().out)['business_writes_possible'] is False


def test_script_resolves_default_binary_input_inside_confirmation(cli, managed, monkeypatch, capsys):
    payload = input_bytes(managed['instruction'])
    with monkeypatch.context() as patch:
        patch.setattr(cli.sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(payload)))
        code = cli.main(['--confirm', '--allow-resolution-write'])
    assert code == 0 and managed['closed'] and len(managed['calls']) == 1
    output = json.loads(capsys.readouterr().out)
    assert output['status'] == 'recorded_operator_confirmation'
    assert output['result']['linked_outcome']['actual_yes'] is True


_PROCESS = r'''
from pathlib import Path
from contextlib import contextmanager
from types import SimpleNamespace
import runpy, sys
root, collecting, phase = Path(sys.argv[1]), sys.argv[2] == 'yes', sys.argv[3]
sys.path.insert(0, str(root / 'src'))
from polymarket_alpha_lab.project_postgres import server
class Session:
    def operation(self, **kwargs):
        if phase == 'operation':
            raise SystemExit(0)
        return SimpleNamespace(to_dict=lambda: dict(failed_count=0, results=[]))
    resolution_worklist = collect_resolution_candidates = operation
class Database:
    def __init__(self, root): pass
    @contextmanager
    def session(self):
        yield Session()
        if phase == 'close':
            raise SystemExit(0)
server.ProjectPostgres = Database
if phase == 'short':
    original = sys.stdout
    class ShortOutput:
        def write(self, text):
            original.write(text[:10])
            return 10
        def flush(self): original.flush()
    sys.stdout = ShortOutput()
script = root / 'scripts/review_resolution_queue.py'
sys.argv = [str(script)] + (['--collect', '--allow-public-fetch'] if collecting else [])
runpy.run_path(str(script), run_name='__main__')
'''


@pytest.mark.parametrize('collecting', [False, True])
@pytest.mark.parametrize('phase', ['operation', 'close', 'short'])
def test_real_interpreter_never_reports_zero_for_internal_exit_or_short_write(tmp_path, collecting, phase):
    import subprocess
    import sys
    from polymarket_alpha_lab.project_postgres.files import clean_environment

    child = subprocess.run([sys.executable, '-I', '-c', _PROCESS, str(ROOT),
        'yes' if collecting else 'no', phase], cwd=tmp_path, env=clean_environment(),
        stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding='utf-8', timeout=30)
    assert child.returncode == 1, (child.stdout, child.stderr)
    assert child.stderr == ''
    if phase == 'short':
        assert len(child.stdout) == 10
    else:
        body = json.loads(child.stdout)
        assert body['status'] == 'failed' and body['business_writes_possible'] is collecting
        assert body['public_network_calls_possible'] is collecting
    assert not list(tmp_path.iterdir())
