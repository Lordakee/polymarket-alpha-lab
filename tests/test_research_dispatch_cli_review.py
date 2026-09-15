"""Separate adversarial self-review of the operator boundary, not external audit."""
from dataclasses import replace
import json

import pytest

from polymarket_alpha_lab import research_dispatch_cli as cli
from polymarket_alpha_lab import research_dispatch_rotation_runner as rotation
from polymarket_alpha_lab import research_model_budget_runner as budgeted
from polymarket_alpha_lab.research_dispatch_rotation import ResearchRotationTurn, StoredResearchRotationTurn
from polymarket_alpha_lab.research_dispatch_rotation_runner import ResearchRotationReport
from polymarket_alpha_lab.research_dispatch_runner import ResearchDispatchStop
from tests.test_research_dispatch_cli import (
    ROOT, NOW, PRIVATE, RUN, READS, managed, invoke, read_value, stored_turn,
)


@pytest.mark.parametrize('value', [0, PRIVATE])
@pytest.mark.parametrize('where', ['error', 'cleanup_error'])
def test_system_exit_is_not_success_or_an_unsanitized_terminal_exit(managed, capsys, value, where):
    managed['value'] = ResearchRotationReport('turn_already_reserved', stored_turn())
    managed[where] = SystemExit(value)
    code, out = invoke(capsys, RUN, model_factory=lambda _: None)
    assert code == 1 and out['status'] == 'failed' and out['result'] is None
    assert out['business_writes_possible'] is True and managed['closed']


@pytest.mark.parametrize('operation,arguments', READS)
def test_output_is_not_emitted_while_session_is_open(managed, capsys, monkeypatch, operation, arguments):
    managed['value'] = read_value(operation)
    original = cli.json.dumps
    def serialize(*a, **kw):
        if type(a[0]) is dict and 'operation' in a[0]: assert managed['closed']
        return original(*a, **kw)
    monkeypatch.setattr(cli.json, 'dumps', serialize)
    code, _ = invoke(capsys, [operation, *arguments])
    assert code == 0


@pytest.mark.parametrize('error', [KeyboardInterrupt(PRIVATE), SystemExit(0), SystemExit(PRIVATE)])
def test_real_executor_drains_and_stops_on_worker_base_exception(managed, capsys, monkeypatch, error):
    batch = read_value('inspect-batch')
    control = ResearchDispatchStop()
    calls = []
    monkeypatch.setattr(rotation, 'inspect_research_turn_with_psycopg', lambda *a, **k: None)
    monkeypatch.setattr(rotation, 'load_research_batch_with_psycopg', lambda *a, **k: batch)
    def reserve(dsn, **kw):
        turn = ResearchRotationTurn(turn_number=1, start_slot=0, **kw)
        return True, StoredResearchRotationTurn(turn, NOW)
    monkeypatch.setattr(rotation, '_reserve', reserve)
    def execute(*a, **kw):
        calls.append(kw)
        raise error
    monkeypatch.setattr(budgeted, 'run_budgeted_research_with_psycopg', execute)
    original = cli._run
    class RealSession:
        def run_research_rotation(self, **kw):
            return rotation.run_research_rotation_with_psycopg('unused-test-seam', **kw)
    def run(session, args, model_factory, stop):
        return original(RealSession(), args, model_factory, stop)
    monkeypatch.setattr(cli, '_run', run)
    code, out = invoke(capsys, RUN, model_factory=lambda _: None, stop=control)
    assert code == (130 if isinstance(error, KeyboardInterrupt) else 1)
    assert control.is_stopped() and managed['closed']
    assert len(calls) == 1 and calls[0]['budget_id'] == 'budget'
    assert out['result'] is None


def test_mutated_run_and_non_receipt_rejected(managed, capsys):
    for value in (object(), {'status': 'success'}, ResearchRotationReport('turn_already_reserved', stored_turn())):
        if type(value) is ResearchRotationReport: object.__setattr__(value, 'status', 'success')
        managed['value'] = value
        code, out = invoke(capsys, RUN, model_factory=lambda _: None)
        assert code == 1 and out['result'] is None


def test_stopped_before_reservation_never_reaches_store_or_client(managed, capsys, monkeypatch):
    control = ResearchDispatchStop(); control.request_stop()
    def forbidden(*a, **kw): pytest.fail('pre-stopped run reached the store')
    monkeypatch.setattr(rotation, 'inspect_research_turn_with_psycopg', forbidden)
    original = cli._run
    class RealSession:
        def run_research_rotation(self, **kw):
            return rotation.run_research_rotation_with_psycopg('unused-test-seam', **kw)
    monkeypatch.setattr(cli, '_run', lambda session, args, factory, stop: original(RealSession(), args, factory, stop))
    code, out = invoke(capsys, RUN, model_factory=forbidden, stop=control)
    assert code == 130 and out['result']['status'] == 'stopped_before_reservation'
    assert out['result']['cursor_written_here'] is False
