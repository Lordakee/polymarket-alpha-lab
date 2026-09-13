"""One-shot collection tests with scripted Gamma replies, not live services."""
from dataclasses import replace
from datetime import timedelta
import json
import importlib.util
from pathlib import Path
from contextlib import contextmanager

import pytest

from polymarket_alpha_lab import research_resolution_poll as poll
from polymarket_alpha_lab.research_resolution_queue import ResolutionWorkItem, ResolutionWorklist
from polymarket_alpha_lab.research_resolution_store import StoredResolutionReview
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot
from tests.test_research_resolution_queue import market, review, worklist
from tests.test_research_resolution import CID, SLUG, NOW, submission


@pytest.fixture
def environment(monkeypatch):
    events=[];queued=worklist();saved=[]
    monkeypatch.setattr(poll,'load_resolution_worklist_with_psycopg',lambda *a,**k:events.append('read-complete') or queued)
    monkeypatch.setattr(poll,'_now',lambda:NOW)
    class Reader:
        def __init__(self,*,allow_public_fetch):assert allow_public_fetch is True
        def fetch(self,*,market_slug):
            events.append('fetch')
            assert events[0]=='read-complete'
            return submission(confirmation=False).snapshot
    def save(dsn,*,submission):
        events.append('capture');saved.append(submission)
        assert submission.confirmation is None
        return StoredResolutionReview(submission,NOW)
    monkeypatch.setattr(poll,'GammaResearchReader',Reader)
    monkeypatch.setattr(poll,'record_resolution_review_with_psycopg',save)
    return events,saved


def run(**kwargs):
    return poll.collect_resolution_candidates_with_psycopg('opaque',allow_public_fetch=True,**kwargs)


def test_closed_binary_candidate_stored_unconfirmed_not_scored(environment):
    events,saved=environment;report=run();out=report.to_dict()
    assert events==['read-complete','fetch','capture']
    assert len(saved)==1 and report.attempts[0].receipt.outcome is None
    assert out['recorded_count']==1 and out['failed_count']==0
    assert out['confirmed_outcomes_created']==0 and out['live_model_called'] is False
    assert out['results'][0]['assessment']['status']=='needs_confirmation'
    assert out['results'][0]['assessment']['candidate_yes'] is True
    assert 'raw_json' not in json.dumps(out) and 'raw_json' not in repr(report)
    assert 'Synthetic' not in repr(report.attempts[0])


@pytest.mark.parametrize('value',[False,None,1,'true'])
def test_fetch_opt_in_before_any_connection(monkeypatch,value):
    monkeypatch.setattr(poll,'load_resolution_worklist_with_psycopg',lambda *a,**k:pytest.fail('DB reached'))
    with pytest.raises(ValueError):poll.collect_resolution_candidates_with_psycopg('x',allow_public_fetch=value)


@pytest.mark.parametrize('value',[0,-1,21,True,'2'])
def test_request_bound_precedes_connection(monkeypatch,value):
    monkeypatch.setattr(poll,'load_resolution_worklist_with_psycopg',lambda *a,**k:pytest.fail('DB reached'))
    with pytest.raises(ValueError):run(max_requests=value)


def test_fetch_failure_is_redacted_and_has_no_fabricated_evidence(environment,monkeypatch):
    class Reader:
        def __init__(self,**kwargs):pass
        def fetch(self,**kwargs):raise RuntimeError('private-token-fixture')
    monkeypatch.setattr(poll,'GammaResearchReader',Reader)
    result=run()
    assert result.attempts[0].status=='fetch_failed' and result.attempts[0].submission is None
    assert result.to_dict()['fetch_attempts']==1 and environment[1]==[]
    assert 'private-token-fixture' not in json.dumps(result.to_dict())


def test_capture_failure_retains_same_submission_for_explicit_retry_only(environment,monkeypatch):
    calls=[]
    def save(*a,**k):calls.append(k['submission']);raise RuntimeError('private-db-detail')
    monkeypatch.setattr(poll,'record_resolution_review_with_psycopg',save)
    result=run();attempt=result.attempts[0]
    assert attempt.status=='capture_failed' and attempt.submission==calls[0]
    assert attempt.receipt is None and len(calls)==1 and environment[0].count('fetch')==1
    assert 'private-db-detail' not in str(result.to_dict())


def test_bad_raw_payload_is_retained_as_blocked_not_silently_dropped(environment,monkeypatch):
    class Reader:
        def __init__(self,**kwargs):pass
        def fetch(self,*,market_slug):return GammaMarketSnapshot(market_slug,NOW,b'bad-json')
    monkeypatch.setattr(poll,'GammaResearchReader',Reader)
    report=run()
    assert report.attempts[0].submission.snapshot.raw_json==b'bad-json'
    assert report.to_dict()['results'][0]['assessment']['status']=='blocked'
    assert report.to_dict()['recorded_count']==1


@pytest.mark.parametrize('reply',[None,object(),replace(submission().snapshot,market_slug='foreign')])
def test_invalid_reader_reply_never_reaches_storage(environment,monkeypatch,reply):
    class Reader:
        def __init__(self,**kw):pass
        def fetch(self,**kw):return reply
    monkeypatch.setattr(poll,'GammaResearchReader',Reader)
    assert run().attempts[0].status=='fetch_failed' and environment[1]==[]


def test_batch_is_bounded_stable_and_one_failure_does_not_hide_other_tasks(environment,monkeypatch):
    items=tuple(ResolutionWorkItem(market(condition_id='0x'+str(i)*64,market_slug='market-'+str(i))) for i in range(4))
    monkeypatch.setattr(poll,'load_resolution_worklist_with_psycopg',lambda *a,**kw:ResolutionWorklist(NOW,items,4))
    calls=[]
    class Reader:
        def __init__(self,**kw):pass
        def fetch(self,*,market_slug):
            calls.append(market_slug)
            if len(calls)==1:raise RuntimeError('private-error')
            return GammaMarketSnapshot(market_slug,NOW,b'{}')
    monkeypatch.setattr(poll,'GammaResearchReader',Reader)
    report=run(max_requests=2)
    assert calls==['market-0','market-1']
    result=report.to_dict()
    assert result['fetch_attempts']==2 and result['unprocessed_due_count']==2
    assert result['failed_count']==1 and result['recorded_count']==1
    assert [item.status for item in report.attempts]==['fetch_failed','recorded']


@pytest.mark.parametrize('latest',[review(),review(data={'closed':False}),review(data={'closed':None})])
def test_not_due_never_fetches(environment,monkeypatch,latest):
    monkeypatch.setattr(poll,'load_resolution_worklist_with_psycopg',lambda *a,**kw:worklist(latest=latest))
    assert run().attempts==() and environment[0]==[]


def test_result_does_not_allow_confirmation_or_missing_attempt(environment):
    report=run()
    with pytest.raises(ValueError):replace(report,attempts=())
    with pytest.raises(ValueError):replace(report.attempts[0],submission=submission())
    with pytest.raises(ValueError):replace(report.attempts[0],receipt=None)


def test_session_uses_bound_context_and_blocks_after_close(monkeypatch):
    from polymarket_alpha_lab.project_postgres.research import ProjectResearchSession
    from polymarket_alpha_lab.project_postgres.files import ProjectDatabaseError
    from polymarket_alpha_lab import research_resolution_queue_store as q
    class DB:
        def _dsn(self,_):return 'managed-private-dsn'
    session=ProjectResearchSession(DB(),dict(instance_id='a'*32,root_sha256='b'*64,system_identifier='123'))
    calls=[]
    monkeypatch.setattr(q,'load_resolution_worklist_with_psycopg',lambda dsn,**kw:calls.append(('list',dsn,kw)))
    monkeypatch.setattr(poll,'collect_resolution_candidates_with_psycopg',lambda dsn,**kw:calls.append(('poll',dsn,kw)))
    session.resolution_worklist(max_markets=2)
    session.collect_resolution_candidates(allow_public_fetch=True,max_requests=1)
    assert [c[0] for c in calls]==['list','poll']
    assert all(c[1]=='managed-private-dsn' for c in calls)
    session.close()
    with pytest.raises(ProjectDatabaseError):session.resolution_worklist()


@pytest.fixture
def cli():
    path=Path(__file__).resolve().parents[1]/'scripts/review_resolution_queue.py'
    spec=importlib.util.spec_from_file_location('queue_cli_test',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('args',[['--collect'],['--allow-public-fetch'],['--max-requests','21'],
    ['--max-markets','0'],['--recheck-after-seconds','59']])
def test_cli_invalid_input_before_database(cli,monkeypatch,args):
    monkeypatch.setattr(cli,'ProjectPostgres',lambda *a:pytest.fail('invalid input reached DB'))
    with pytest.raises(SystemExit) as e:cli.main(args)
    assert e.value.code==2


def test_default_cli_only_lists_and_never_collects(cli,monkeypatch,capsys):
    class Session:
        def resolution_worklist(self,**kw):return worklist()
        def collect_resolution_candidates(self,**kw):pytest.fail('default should not fetch')
    class DB:
        def __init__(self,*a):pass
        @contextmanager
        def session(self):yield Session()
    monkeypatch.setattr(cli,'ProjectPostgres',DB)
    assert cli.main([])==0
    assert json.loads(capsys.readouterr().out)['state_counts']['fetch_due']==1


def test_cli_failure_never_prints_database_paths(cli,monkeypatch,capsys):
    def denied(*a):raise RuntimeError('private-DSN-fixture')
    monkeypatch.setattr(cli,'ProjectPostgres',denied)
    assert cli.main([])==1
    out=capsys.readouterr().out
    assert 'private-DSN-fixture' not in out and json.loads(out)['reason_code']=='resolution_queue_operation_failed'


def test_interrupt_during_fetch_is_not_swallowed(environment,monkeypatch):
    class Reader:
        def __init__(self,**kw):pass
        def fetch(self,**kw):raise KeyboardInterrupt()
    monkeypatch.setattr(poll,'GammaResearchReader',Reader)
    with pytest.raises(KeyboardInterrupt):run()
    assert environment[1]==[]
