"""Existing console routes to the original settlement service; synthetic only."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import timedelta
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys

import pytest

from polymarket_alpha_lab import research_evaluation_cli as cli
from polymarket_alpha_lab.team_research_evaluation import ResearchEvaluationReport
from tests.test_research_paper_settlement import case, assemble, PRIVATE


def exported(p='.7', actual=True):
    h, receipt, review, _, _ = case(p=p, actual=actual)
    return assemble(h, {receipt.scenario.record_id: receipt}, {review.outcome.condition_id: review})


@pytest.fixture
def managed(monkeypatch):
    state = dict(report=exported(), events=[], error=None, cleanup_error=None)
    class Session:
        def evaluate_settled_paper_research(self, **kw):
            state['events'].append(('settled', kw))
            if state['error'] is not None: raise state['error']
            return state['report']
        def evaluate(self, **kw):
            state['events'].append(('legacy', kw))
            return ResearchEvaluationReport((), (), case()[0].generated_at)
    class DB:
        def __init__(self, root): state['events'].append(('root', root))
        @contextmanager
        def session(self):
            state['events'].append(('enter',))
            try: yield Session()
            finally:
                state['events'].append(('exit',))
                if state['cleanup_error'] is not None: raise state['cleanup_error']
    monkeypatch.setattr(cli, 'ProjectPostgres', DB)
    return state


def invoke(capsys, *args):
    code = cli.main(['--settled-paper', *args], default_root=Path('/unused/project'))
    captured = capsys.readouterr()
    assert captured.err == ''
    assert PRIVATE not in captured.out
    return code, json.loads(captured.out)


@pytest.mark.parametrize('details', [False, True])
@pytest.mark.parametrize('p,actual', [('.7', True), ('.7', False), ('.1', True), ('.1', False)])
def test_existing_amounts_groups_flags_and_nulls_are_preserved(managed, capsys, details, p, actual):
    managed['report'] = exported(p, actual)
    original = deepcopy(managed['report'])
    code, out = invoke(capsys, *(['--include-decisions'] if details else []))
    assert code == 0 and out['status'] == 'evaluated'
    assert out['evaluation_kind'] == 'settled_paper'
    expected = deepcopy(original)
    if not details:
        expected.pop('attempts'); expected['history'].pop('decisions')
    expected['decisions_included'] = details
    assert out['evaluation'] == expected
    assert managed['report'] == original
    assert out['evaluation']['actual_account_pnl'] is None
    assert out['evaluation']['tariff_verified'] is False
    assert [event[0] for event in managed['events']] == ['root', 'enter', 'settled', 'exit']
    assert managed['events'][2][1] == dict(generated_at=None, max_records=10000,
        bucket_count=10, min_sample_count=30, min_bin_count=5)


def test_historical_options_reach_the_same_service_without_fallback(managed, capsys):
    h, receipt, review, _, _ = case()
    h = replace(h, bucket_count=5, min_sample_count=50, min_bin_count=8)
    managed['report'] = assemble(h, {receipt.scenario.record_id: receipt}, {review.outcome.condition_id: review})
    at = h.generated_at
    code, out = invoke(capsys, '--root', '/unused/other', '--as-of', at.isoformat(),
        '--max-records', '12', '--buckets', '5', '--min-sample-count', '50', '--min-bin-count', '8')
    assert code == 0
    assert managed['events'][0] == ('root', Path('/unused/other'))
    assert managed['events'][2][1] == dict(generated_at=at, max_records=12,
        bucket_count=5, min_sample_count=50, min_bin_count=8)


def test_no_flag_uses_unchanged_probability_path(managed, capsys):
    assert cli.main([], default_root=Path('/unused/project')) == 0
    out = json.loads(capsys.readouterr().out)
    assert 'evaluation_kind' not in out
    assert out['evaluation']['evaluation_status'] == 'no_visible_attempts'
    assert [e[0] for e in managed['events']] == ['root', 'enter', 'legacy', 'exit']


@pytest.mark.parametrize('empty', [False, True])
def test_missing_simulations_are_not_empty_history_or_zero_pnl(managed, capsys, empty):
    history = case()[0]
    if empty: history = ResearchEvaluationReport((), (), history.generated_at)
    managed['report'] = assemble(history, {}, {})
    code, out = invoke(capsys)
    assert code == 0
    assert out['evaluation']['attempt_count'] == (0 if empty else 1)
    assert out['evaluation']['status_counts']['paper_evidence_missing'] == (0 if empty else 1)
    assert out['evaluation']['groups'] == []
    assert out['evaluation']['actual_account_pnl'] is None


def test_pending_group_null_amounts_remain_null(managed, capsys):
    h, receipt, _, _, _ = case()
    history = ResearchEvaluationReport(h.records, (), h.generated_at)
    managed['report'] = assemble(history, {receipt.scenario.record_id: receipt}, {})
    code, out = invoke(capsys)
    assert code == 0 and out['evaluation']['status_counts']['outcome_pending'] == 1
    assert out['evaluation']['groups'][0]['settled_pnl_lower_bound_sum'] is None


@pytest.mark.parametrize('reason', sorted(cli._BLOCKS | {'research_paper_settlement_read_limit'}))
def test_known_blocks_return_no_partial_result_or_retry(managed, capsys, reason):
    managed['error'] = cli.ResearchCaptureConflict(reason)
    code, out = invoke(capsys)
    assert code == 1 and out['status'] == 'blocked' and out['reason_code'] == reason
    assert out['evaluation'] is None and out['history_gate'] == 'not_established'
    assert [e[0] for e in managed['events']] == ['root', 'enter', 'settled', 'exit']


@pytest.mark.parametrize('field', ['error', 'cleanup_error'])
def test_runtime_and_cleanup_errors_suppress_success(managed, capsys, field):
    managed[field] = RuntimeError(PRIVATE)
    code, out = invoke(capsys)
    assert code == 1 and out['status'] == 'failed' and out['evaluation'] is None
    assert out['reason_code'] == 'research_paper_evaluation_operation_failed'


@pytest.mark.parametrize('bad', [None, [], {}, {'private': PRIVATE}])
def test_invalid_service_export_does_not_get_a_success_envelope(managed, capsys, bad):
    managed['report'] = bad
    code, out = invoke(capsys)
    assert code == 1 and out['evaluation'] is None


@pytest.mark.parametrize('args', [
    ['--as-of', '2026-09-15'], ['--max-records', '0'], ['--max-records', '10001'],
    ['--buckets', '3'], ['--min-bin-count', '0'], ['--min-sample-count', '10001'],
    ['--dsn', 'unsupported'], ['--allow-paper-write'], ['--skip-incomplete'], ['--record-id', 'pick-a-winner'],
])
def test_configuration_error_precedes_database_access(managed, args):
    with pytest.raises(SystemExit) as error:
        cli.main(['--settled-paper', *args], default_root=Path('/unused'))
    assert error.value.code == 2 and managed['events'] == []


def test_actual_help_has_new_option_without_initialization(tmp_path):
    path = Path(__file__).resolve().parents[1] / 'scripts/evaluate_project_research.py'
    result = subprocess.run([sys.executable, '-I', str(path), '--help'], cwd=tmp_path,
        capture_output=True, text=True, timeout=30)
    assert result.returncode == 0 and '--settled-paper' in result.stdout
    assert not (tmp_path / '.local').exists()
