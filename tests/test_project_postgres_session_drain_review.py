"""Separate self-review of drain, exception precedence and unchanged admission.

No OS signal is sent and no service/provider is called. The controlled interrupt
is raised at close while real admitted threads are held by test-owned Events.
"""
import pytest

from polymarket_alpha_lab.project_postgres import files, research
from tests.test_project_postgres_session_drain import exercise, managed


@pytest.mark.parametrize('started', [False, True])
def test_repeated_close_interrupts_preserve_first_without_restarting_work(managed, started):
    first = KeyboardInterrupt('first test-owned interruption')
    managed.update(started=started, close_errors=[first, SystemExit(4), KeyboardInterrupt('later')])
    exercise(managed)
    assert managed['checkpoint_lease'] is True and managed['in_flight_at_unlock'] == [0]
    assert managed['error'] is first
    assert managed['events'].count('wait') >= 4
    assert managed['events'].count('stop') == int(started)
    assert managed['operation_calls'] == 1


@pytest.mark.parametrize('kind', ['regular', 'interrupt', 'exit'])
def test_stop_error_stays_primary_with_delayed_interrupt_as_cause(managed, kind):
    interruption = KeyboardInterrupt('close test')
    failure = {'regular': files.ProjectDatabaseError('project_postgres_stop_failed'),
               'interrupt': KeyboardInterrupt('stop test'), 'exit': SystemExit(9)}[kind]
    managed.update(close_errors=[interruption], stop_error=failure)
    exercise(managed)
    assert managed['in_flight_at_unlock'] == [0]
    assert managed['error'] is failure and failure.__cause__ is interruption
    assert managed['events'].count('stop') == 1


def test_borrowed_engine_never_stopped_even_with_deferred_interrupt(managed):
    first = SystemExit(0)
    managed.update(started=False, close_errors=[first], stop_error=AssertionError('must not stop'))
    exercise(managed)
    assert managed['error'] is first and 'stop' not in managed['events']
    assert managed['in_flight_at_unlock'] == [0]


def test_body_failure_remains_in_exception_chain_after_close_interrupt(managed):
    body = ValueError('original body failed')
    interruption = KeyboardInterrupt('during drain')
    managed.update(body_error=body, close_errors=[interruption])
    exercise(managed)
    assert managed['error'] is interruption and interruption.__context__ is body
    assert managed['in_flight_at_unlock'] == [0]


def test_interruption_before_close_enters_is_still_deferred(managed, monkeypatch):
    original = research.ProjectResearchSession.close
    first = KeyboardInterrupt('before condition acquisition')
    calls = []
    def close(session):
        calls.append(session)
        if len(calls) == 1:
            raise first
        return original(session)
    monkeypatch.setattr(research.ProjectResearchSession, 'close', close)
    exercise(managed)
    assert managed['error'] is first and len(calls) == 2 and calls[0] is calls[1]
    assert managed['checkpoint_lease'] is True and managed['in_flight_at_unlock'] == [0]


def test_non_interrupt_close_failure_is_not_retried_or_mislabeled_drained(managed, monkeypatch):
    failure = RuntimeError('synthetic unexpected close failure')
    calls = []
    def close(session):
        calls.append(session)
        # This scenario has no admitted operations. General close faults are
        # outside the controlled-interruption retry, and must not spin forever.
        raise failure
    monkeypatch.setattr(research.ProjectResearchSession, 'close', close)
    with pytest.raises(RuntimeError) as caught:
        with managed['db'].session() as session:
            managed['session'] = session
    assert caught.value is failure and calls == [session]
    assert 'stop' not in managed['events']


@pytest.mark.parametrize('started', [False, True])
def test_no_inflight_work_and_normal_close_retains_original_return(managed, started):
    managed['started'] = started
    with managed['db'].session() as session:
        managed['session'] = session
        assert session._call(lambda _: 42) == 42
    assert managed['in_flight_at_unlock'] == [0]
    assert managed['events'].count('stop') == int(started)
    with pytest.raises(files.ProjectDatabaseError, match='session_closed'):
        session._call(lambda _: pytest.fail('closed session readmitted work'))


def test_packaged_probe_uses_exact_kit_interpreter_once(monkeypatch, tmp_path):
    import subprocess
    from tests import packaged_session_drain as probe
    calls = []
    result = subprocess.CompletedProcess([], 1, 'synthetic', '')
    def run(args, **kwargs):
        calls.append((args, kwargs))
        return result
    monkeypatch.setattr(probe.subprocess, 'run', run)
    python = tmp_path / '.venv/Scripts/python.exe'
    assert probe.run_packaged_session_drain(tmp_path, python, tmp_path.parent) is result
    assert len(calls) == 1
    args, options = calls[0]
    assert args == [str(python), '-I', '-c', probe.RECIPE, str(tmp_path)]
    assert options['timeout'] == 180 and options['check'] is options['shell'] is False
    assert options['stdin'] is subprocess.DEVNULL and options['cwd'] == tmp_path.parent


def test_packaged_probe_preserves_timeout_without_retry(monkeypatch, tmp_path):
    import subprocess
    from tests import packaged_session_drain as probe
    original = subprocess.TimeoutExpired('synthetic', 180)
    calls = []
    def run(*args, **kwargs):
        calls.append(1)
        raise original
    monkeypatch.setattr(probe.subprocess, 'run', run)
    with pytest.raises(subprocess.TimeoutExpired) as caught:
        probe.run_packaged_session_drain(tmp_path, 'synthetic-python', tmp_path)
    assert caught.value is original and calls == [1]


def test_packaged_probe_command_line_and_syntax_are_bounded():
    import subprocess
    from tests.packaged_session_drain import RECIPE
    compile(RECIPE, '<packaged session drain>', 'exec')
    command = ['C:/'+('p'*180)+'/python.exe', '-I', '-c', RECIPE, 'C:/'+('k'*180)]
    assert len(subprocess.list2cmdline(command).encode('utf-16-le')) // 2 + 1 < 32767
