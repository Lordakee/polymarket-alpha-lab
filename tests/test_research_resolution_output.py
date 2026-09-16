"""Resolution console failures are not success; fixtures never perform I/O."""
from contextlib import contextmanager
from types import SimpleNamespace
import io
import json

import pytest

from polymarket_alpha_lab import research_resolution_confirmation_cli as confirmation
from tests.test_research_resolution_poll import cli
from tests.test_research_resolution_queue import worklist

PRIVATE = 'synthetic-private-resolution-detail'
COLLECT = ['--collect', '--allow-public-fetch', '--max-requests', '1']


@pytest.fixture
def operation(cli, monkeypatch):
    state = dict(events=[], failure=None, phase=None, collecting=False, failed_count=0)

    def hit(phase):
        state['events'].append(phase)
        if state['phase'] == phase:
            raise state['failure']

    class Result:
        def to_dict(self):
            hit('to_dict')
            return (dict(failed_count=state['failed_count'], confirmed_outcomes_created=0,
                         live_model_called=False, results=[]) if state['collecting'] else worklist().to_dict())

    class Session:
        def resolution_worklist(self, **kw):
            state['options'] = kw
            hit('operation')
            return Result()

        def collect_resolution_candidates(self, **kw):
            state['options'] = kw
            state['collecting'] = True
            hit('operation')
            return Result()

    class Database:
        def __init__(self, root):
            hit('constructor')

        @contextmanager
        def session(self):
            hit('enter')
            try:
                yield Session()
            finally:
                hit('close')

    monkeypatch.setattr(cli, 'ProjectPostgres', Database)
    state['cli'] = cli
    return state


@pytest.mark.parametrize('collecting', [False, True])
@pytest.mark.parametrize('phase', ['constructor', 'enter', 'operation', 'to_dict', 'close'])
@pytest.mark.parametrize('kind', ['exit-zero', 'interrupt'])
def test_operation_and_cleanup_failures_never_escape_as_success(operation, capsys, collecting, phase, kind):
    operation.update(phase=phase, failure=SystemExit(0) if kind == 'exit-zero' else KeyboardInterrupt(PRIVATE))
    try:
        code = operation['cli'].main(COLLECT if collecting else [])
    except (SystemExit, KeyboardInterrupt) as error:
        code = ('escaped', type(error).__name__)
    output = capsys.readouterr()
    assert code == (130 if kind == 'interrupt' else 1)
    value = json.loads(output.out)
    assert value['status'] == ('interrupted' if kind == 'interrupt' else 'failed')
    assert value['business_writes_possible'] is collecting
    assert value['public_network_calls_possible'] is collecting
    assert value['automatic_retry_permitted'] is False
    assert value['confirmed_outcomes_created'] == 0
    assert value['live_model_called'] is False
    assert PRIVATE not in output.out + output.err
    assert operation['events'].count('operation') <= 1


@pytest.mark.parametrize('collecting,failures', [(False, 0), (True, 0), (True, 1)])
def test_success_body_and_partial_collection_exit_are_preserved(operation, monkeypatch, collecting, failures):
    operation['failed_count'] = failures
    stream = io.StringIO()
    original = stream.write

    class Output:
        def write(self, text):
            assert operation['events'][-1] == 'close'
            return original(text)

        def flush(self):
            assert operation['events'][-1] == 'close'

    with monkeypatch.context() as patch:
        patch.setattr(operation['cli'].sys, 'stdout', Output())
        code = operation['cli'].main(COLLECT if collecting else [])
    assert code == (1 if failures else 0)
    expected = (dict(failed_count=failures, confirmed_outcomes_created=0, live_model_called=False, results=[])
                if collecting else worklist().to_dict())
    assert json.loads(stream.getvalue()) == expected
    assert operation['events'].count('operation') == 1


@pytest.mark.parametrize('mode', ['list', 'collect', 'confirm-blocked'])
@pytest.mark.parametrize('fault', ['short', 'flush', 'write-exit', 'write-error', 'write-interrupt'])
def test_failed_output_is_nonzero_without_second_envelope(operation, monkeypatch, mode, fault):
    events = []

    class Output:
        def write(self, text):
            events.append('write')
            if fault == 'write-exit':
                raise SystemExit(0)
            if fault == 'write-error':
                raise OSError(PRIVATE)
            if fault == 'write-interrupt':
                raise KeyboardInterrupt(PRIVATE)
            return len(text) - 1 if fault == 'short' else len(text)

        def flush(self):
            events.append('flush')
            if fault == 'flush':
                raise OSError(PRIVATE)

    with monkeypatch.context() as patch:
        patch.setattr(operation['cli'].sys, 'stdout', Output())
        try:
            if mode == 'confirm-blocked':
                code = confirmation.confirm_from_stdin(root=None, stream=None)
            else:
                code = operation['cli'].main(COLLECT if mode == 'collect' else [])
        except (Exception, SystemExit, KeyboardInterrupt) as error:
            code = ('escaped', type(error).__name__)
    assert code == (130 if fault == 'write-interrupt' else 1)
    assert events.count('write') == 1
    assert events.count('flush') == (1 if fault == 'flush' else 0)
    assert operation['events'].count('operation') == (0 if mode == 'confirm-blocked' else 1)
